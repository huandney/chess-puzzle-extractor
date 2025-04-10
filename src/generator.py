import os
import shutil
import chess
import chess.engine
import chess.pgn
import time
from collections import defaultdict
from rich.text import Text
from src import utils         # Contém iterate_games(), count_games() e format_eval()
from src import ambiguity     # Lógica que futuramente migrará para o módulo analyzer
from src import exporter
from src import config
from src import visual
from src import resume as resume_module
from src.statistics import PuzzleStatistics  # Módulo de estatísticas

def generate_puzzles(input_path, output_path=None, depth=config.DEFAULT_DEPTH, max_variants=config.DEFAULT_MAX_VARIANTS, verbose=False, resume=False):
    """
    Analisa os jogos do arquivo PGN input_path e gera puzzles táticos conforme os critérios.

    Args:
        input_path (str): Caminho para o arquivo PGN contendo as partidas.
        output_path (str, optional): Caminho para o arquivo de saída dos puzzles (padrão: config.DEFAULT_OUTPUT).
        depth (int): Profundidade máxima de análise do motor (padrão: config.DEFAULT_DEPTH).
        max_variants (int): Número máximo de variantes alternativas permitidas (padrão: config.DEFAULT_MAX_VARIANTS).
        verbose (bool): Se True, exibe informações detalhadas durante análise.
        resume (bool): Se True, retoma a análise a partir do último progresso salvo.

    Returns:
        tuple: (total_games, puzzles_found, puzzles_rejected, rejection_reasons)
    """

    # Preparar saída (arquivo ou console) - Modo append se resume=True
    output_handle = open(output_path, "a" if resume else "w", encoding="utf-8") if output_path else None

    # Calcular profundidades de análise utilizando o config
    depths = config.calculate_depths(depth)

    # Detecta o caminho do Stockfish
    local_stockfish = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stockfish"))
    if os.path.isfile(local_stockfish):
        engine_path = local_stockfish  # Usa o binário compilado local
    elif shutil.which("stockfish"):
        engine_path = "stockfish"      # Usa o Stockfish instalado no sistema
    else:
        raise Exception("Nenhum executável do Stockfish foi encontrado. Compile ou instale o Stockfish.")

    # Exibe o caminho do Stockfish utilizando o módulo visual
    visual.print_stockfish_info(engine_path)

    # Tenta iniciar o engine
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as e:
        raise Exception(f"Não foi possível iniciar o Stockfish em '{engine_path}'. Erro: {e}")

    # Inicializa os dados de resume (ou reseta caso não esteja usando resume)
    resume_data, games_analyzed, stats = resume_module.initialize_resume(input_path, puzzles_dir="puzzles", resume_flag=resume)
    if resume:
        visual.print_resume_info(games_analyzed)

    # Contar o número total de jogos para a barra de progresso
    total_game_count = utils.count_games(input_path)

    # Exibir cabeçalho inicial
    try:
        size_bytes = os.path.getsize(input_path)
        if size_bytes < 1024:
            file_size = f"{size_bytes:.2f} B"
        elif size_bytes < 1024 * 1024:
            file_size = f"{size_bytes / 1024:.2f} KB"
        else:
            file_size = f"{size_bytes / (1024 * 1024):.2f} MB"
    except OSError:
        print("Falha ao obter o tamanho do arquivo")
        file_size = "0.00 MB"
    visual.print_initial_analysis_info(input_path, file_size, total_game_count, resume, games_analyzed, depth, depths, max_variants)

    # Obter o offset de tempo salvo (se houver) para a barra de progresso
    elapsed_offset = resume_data.get("elapsed_time", 0) if resume else 0

    # Criar iterador para os jogos via utils e pular os já processados
    games_iterator = utils.iterate_games(input_path)
    if resume:
        for _ in range(games_analyzed):
            next(games_iterator, None)

    # Cria a barra de progresso com o tempo acumulado
    try:
        with visual.create_progress(elapsed_offset=elapsed_offset) as progress:
            task_id = progress.add_task("[yellow]Analisando partidas...", total=total_game_count, completed=games_analyzed)
            # Para cada partida, processa os movimentos e gera puzzles se necessário.
            for game in games_iterator:

                # Obter headers originais do jogo e criar a posição inicial
                original_headers = game.headers.copy()
                board = game.board()

                # Avaliação inicial da posição com profundidade 'scan'
                try:
                    info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['scan']))
                except Exception as e:
                    progress.log(f"[red]Erro ao analisar posição inicial do jogo {stats.total_games}: {e}[/red]")
                    continue
                prev_score = info.get("score")
                prev_cp = prev_score.pov(chess.WHITE).score() if prev_score else None

                # Iterar pelos movimentos da linha principal do jogo
                move_number = 0
                for move in game.mainline_moves():
                    move_number += 1
                    side_to_move = "White" if board.turn == chess.WHITE else "Black"
                    move_san = board.san(move)
                    board.push(move)

                    # Nova análise após o lance
                    try:
                        info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['scan']))
                    except Exception:
                        info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['quick']))
                    score = info.get("score")
                    post_cp = score.pov(chess.WHITE).score() if score else None

                    # Modo verbose: log dos lances e avaliações
                    if verbose:
                        prev_str = utils.format_eval(prev_score)
                        post_str = utils.format_eval(score)
                        move_index = board.fullmove_number
                        log_prefix = f"{move_index}." if side_to_move == "White" else f"{move_index}..."
                        eval_text = Text()
                        eval_text.append(f"{log_prefix} {move_san}: eval ")
                        eval_text.append(prev_str, style="blue")
                        eval_text.append(" → ")
                        if prev_cp is not None and post_cp is not None:
                            diff = post_cp - prev_cp
                            style = "red" if diff < 0 and abs(diff) > 50 else ("green" if diff > 0 and abs(diff) > 50 else "blue")
                            eval_text.append(post_str, style=style)
                        else:
                            eval_text.append(post_str, style="blue")
                        progress.log(eval_text)

                    # Verificar se há queda de avaliação (possível blunder)
                    if prev_cp is not None and post_cp is not None:
                        eval_diff = prev_cp - post_cp
                        blunder = False
                        solver_color = None
                        if board.turn == chess.BLACK:  # Brancas jogaram e a avaliação caiu
                            if eval_diff >= config.BLUNDER_THRESHOLD:
                                blunder = True
                                solver_color = chess.BLACK  # Pretas devem resolver
                        else:  # Pretas jogaram e a avaliação caiu
                            if eval_diff <= -config.BLUNDER_THRESHOLD:
                                blunder = True
                                solver_color = chess.WHITE  # Brancas devem resolver

                        if blunder:
                            # Candidato a puzzle detectado
                            if verbose:
                                diff = abs(post_cp - prev_cp)
                                diff_pawn = diff / 100.0
                                side = "Brancas" if solver_color == chess.WHITE else "Pretas"
                                prev_str = utils.format_eval(prev_score)
                                post_str = utils.format_eval(score)
                                progress.log(f"[bold yellow]Candidato a puzzle detectado no lance {move_number}[/bold yellow]\n"
                                             f"{side_to_move} cometeu erro: avaliação {prev_str} → {post_str}\n"
                                             f"Diferença: {diff_pawn:.2f} peões")
                            puzzle_ok = True
                            reason = None

                            # Filtro de vantagem prévia removido conforme nova estratégia
                            # Gerar sequência de solução se passar nos filtros iniciais
                            board_post_blunder = board.copy()    # Posição após o lance errado
                            board_pre_blunder = board.copy()
                            board_pre_blunder.pop()              # Volta para a posição pré-blunder

                            # Monta o objeto Game para o puzzle
                            puzzle_game = chess.pgn.Game()
                            # Copiar headers originais
                            for tag, value in original_headers.items():
                                puzzle_game.headers[tag] = value
                                # Adicionar FEN da posição inicial do puzzle
                            puzzle_game.headers["SetUp"] = "1"
                            puzzle_game.headers["FEN"] = board_pre_blunder.fen()
                            if "Result" in original_headers:
                                puzzle_game.headers["Result"] = original_headers["Result"]

                            # Montar linha principal e variações do puzzle
                            node = puzzle_game
                            # Adicionar lance de blunder do adversário como o primeiro lance do puzzle
                            blunder_move = move
                            node = node.add_main_variation(blunder_move)
                            # Agora, node representa a posição após o blunder, e é a vez do solver jogar

                            # a) Primeiro lance do solucionador (S1)
                            solver_board = board_post_blunder.copy()
                            # Análise de ambiguidade (melhor lance e alternativas viáveis)
                            candidates = ambiguity.find_alternatives(engine, solver_board, solver_color, max_variants, depth=depths['solve'])
                            if candidates is None:
                                puzzle_ok = False
                                reason = "múltiplas soluções"
                            else:
                                best_move = candidates["best"]
                                alt_moves = candidates["alternatives"]
                                node_s1 = node.add_main_variation(best_move)
                                for alt in alt_moves:
                                    node.add_variation(alt)

                                # b) Resposta do oponente (O1)
                                opponent_board = solver_board.copy()
                                opponent_board.push(best_move)
                                try:
                                    info_opp = engine.analyse(opponent_board, limit=chess.engine.Limit(depth=depths['solve']))
                                except Exception:
                                    info_opp = engine.analyse(opponent_board, limit=chess.engine.Limit(depth=depths['scan']))
                                opp_move = None
                                if "pv" in info_opp:
                                    pv_line = info_opp["pv"]
                                    if pv_line:
                                        opp_move = pv_line[0]
                                if opp_move is None:
                                    opp_move = list(opponent_board.legal_moves)[0]
                                node_o1 = node_s1.add_main_variation(opp_move)

                                # c) Segundo lance do solucionador (S2)
                                solver_board2 = opponent_board.copy()
                                solver_board2.push(opp_move)
                                candidates2 = ambiguity.find_alternatives(engine, solver_board2, solver_color, max_variants, depth=depths['solve'])
                                if candidates2 is None:
                                    puzzle_ok = False
                                    reason = "múltiplas soluções"
                                else:
                                    best_move2 = candidates2["best"]
                                    alt_moves2 = candidates2["alternatives"]
                                    node_s2 = node_o1.add_main_variation(best_move2)
                                    for alt2 in alt_moves2:
                                        node_o1.add_variation(alt2)
                                        # Possibilidade de extensão para S3, S4, etc.

                            # Filtro de comprimento mínimo da sequência
                            if puzzle_ok:
                                half_moves = 0
                                node_iter = puzzle_game
                                while node_iter.variations:
                                    node_iter = node_iter.variations[0]
                                    half_moves += 1
                                if half_moves < 4:
                                    puzzle_ok = False
                                    reason = "sequência muito curta"

                            # Decisão final sobre o puzzle
                            if puzzle_ok:
                                node_iter = puzzle_game
                                while node_iter.variations:
                                    node_iter = node_iter.variations[0]
                                final_board = node_iter.board()
                                if final_board.is_checkmate():
                                    objective = "Mate"
                                else:
                                    final_info = engine.analyse(final_board, limit=chess.engine.Limit(depth=depths['quick']))
                                    final_score = final_info.get("score")
                                    final_cp = final_score.pov(solver_color).score() if final_score else None
                                    final_win = (final_cp is not None and final_cp >= config.WINNING_ADVANTAGE)
                                    final_draw = (final_cp is not None and -config.DRAWING_RANGE < final_cp < config.DRAWING_RANGE)
                                    if final_win:
                                        objective = "Reversão" if (prev_cp is not None and prev_cp < 0) else "Blunder"
                                    elif final_draw:
                                        objective = "Equalização" if (prev_cp is not None and prev_cp < 0) else "Defesa"
                                    else:
                                        objective = "Defesa"

                                fullmove_num = board_pre_blunder.fullmove_number
                                piece_count = sum(
                                    1 for sq in chess.SQUARES
                                    if board_pre_blunder.piece_at(sq) and board_pre_blunder.piece_at(sq).piece_type != chess.KING
                                )
                                if fullmove_num <= 10:
                                    phase = "Abertura"
                                elif fullmove_num >= 30 or piece_count <= 10:
                                    phase = "Final"
                                else:
                                    phase = "Meio-jogo"

                                puzzle_game.headers["Objetivo"] = objective
                                puzzle_game.headers["Fase"] = phase

                                stats.update_objective(objective)
                                stats.update_phase(phase)
                                stats.add_found()

                                if output_handle:
                                    exporter.export_puzzle(puzzle_game, output_handle)
                                if not verbose:
                                    visual.print_puzzle_found(progress, stats.puzzles_found, puzzle_game)
                                else:
                                    visual.print_verbose_puzzle_generated(progress, "[bold green]Puzzle gerado com sucesso.[/bold green]\n", puzzle_game)
                            else:
                                stats.add_rejected(reason)
                                if verbose and reason:
                                    progress.log(f"[bold red]Descartado:[/] [bold]{reason}.[/]\n")
                    prev_score = score
                    prev_cp = post_cp

                # Atualiza o contador acumulado de jogos processados
                stats.increment_games()
                # Atualiza os dados de resume usando os valores acumulados
                resume_module.update_resume_data(input_path, stats.total_games, stats, puzzles_dir="puzzles")

                progress.update(task_id,
                                advance=1,
                                description=f"[yellow]Analisando partidas... [green]Encontrados: {stats.puzzles_found} [red]Rejeitados: {stats.puzzles_rejected}",
                                refresh=True)
    except KeyboardInterrupt:
        # Em caso de interrupção, exibe as estatísticas acumuladas até o momento
        total_time = time.time() - stats.start_time
        average_time_per_game = total_time / max(1, stats.total_games)
        visual.render_end_statistics(stats.total_games, stats.puzzles_found, stats.puzzles_rejected, total_time,
                                       average_time_per_game, dict(stats.rejection_reasons),
                                       dict(stats.objective_stats), dict(stats.phase_stats))
        visual.print_error("\nInterrompido pelo usuário.")
        engine.quit()
        raise

    engine.quit()

    total_time = time.time() - stats.start_time
    average_time_per_game = total_time / max(1, stats.total_games)

    visual.render_end_statistics(stats.total_games, stats.puzzles_found, stats.puzzles_rejected, total_time,
                                   average_time_per_game, dict(stats.rejection_reasons),
                                   dict(stats.objective_stats), dict(stats.phase_stats), output_path)

    return stats.total_games, stats.puzzles_found, stats.puzzles_rejected, dict(stats.rejection_reasons)
