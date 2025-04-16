import os
import shutil
import chess
import chess.engine
import chess.pgn
import time
from collections import defaultdict, namedtuple
from rich.text import Text
from src import utils
from src import analysis  # Substitui o antigo ambiguity
from src import exporter
from src import config
from src import visual
from src import resume as resume_module
from src import candidates
from src.statistics import PuzzleStatistics, AnalysisResult

# Estrutura para armazenar informações sobre um candidato a puzzle
PuzzleCandidate = namedtuple('PuzzleCandidate', [
    'board_pre_blunder',      # Posição antes do blunder
    'board_post_blunder',     # Posição após o blunder
    'adjusted_board',         # Posição após pular lances forçados
    'blunder_move',           # O lance que causou o blunder
    'forced_sequence',        # Sequência de lances forçados a pular
    'solver_color',           # Cor que deve resolver o puzzle
    'post_cp',                # Avaliação após o blunder
    'original_headers',       # Headers do jogo original
    'move_number'             # Número do lance na partida
])

def extend_puzzle_sequence(engine, puzzle_node, board, solver_color, max_variants, depth, min_moves=2):
    solver_moves = 0
    current_board = board.copy()
    move_sequence = []  # Lista temporária de movimentos (move, is_solver_move)

    while True:
        # Turno do Solver
        alt_info = analysis.analyze_solutions(
            engine, current_board, solver_color, max_variants, depth=depth
        )

        if alt_info is None:
            # Ambiguidade detectada, encerramos imediatamente
            break

        solver_move = alt_info["best"]
        move_sequence.append((solver_move, True))
        current_board.push(solver_move)
        solver_moves += 1

        # Turno do Oponente
        opp_move = analysis.opponent_response(engine, current_board, depth)

        if opp_move is None:
            # Não há mais movimentos possíveis, terminamos aqui
            break

        move_sequence.append((opp_move, False))
        current_board.push(opp_move)

    # Garantir que o puzzle termine no solver:
    # Se a última jogada foi do oponente, removemos para encerrar no solver
    if move_sequence and not move_sequence[-1][1]:
        last_opp_move, _ = move_sequence.pop()
        current_board.pop()

    # Validar quantidade mínima de lances do solver
    if solver_moves < min_moves:
        return {
            "success": False,
            "reason": "sequência muito curta",
            "final_board": current_board
        }

    # Finalmente, aplicar os movimentos guardados ao puzzle_node original
    current_node = puzzle_node
    for move, _ in move_sequence:
        current_node = current_node.add_main_variation(move)

    return {
        "success": True,
        "reason": "puzzle válido",
        "final_board": current_board
    }

def configure_headers(puzzle_game, candidate):
    """
    Configura os cabeçalhos (headers) do puzzle_game com base nos headers originais do jogo.
    """
    for tag, value in candidate.original_headers.items():
        puzzle_game.headers[tag] = value

    puzzle_game.headers["SetUp"] = "1"
    puzzle_game.headers["FEN"] = candidate.board_pre_blunder.fen()
    if "Result" in candidate.original_headers:
        puzzle_game.headers["Result"] = candidate.original_headers["Result"]


def determine_puzzle_objective(engine, final_board, candidate, depths):
    """
    Determina o objetivo do puzzle (Mate, Reversão, Equalização, Defesa, Blunder, etc.)
    de acordo com a posição final e a avaliação do engine.
    """
    if final_board.is_checkmate():
        return "Mate"

    # Analisar posição final para determinar vantagem
    final_info = engine.analyse(final_board, limit=chess.engine.Limit(depth=depths['quick']))
    final_score = final_info.get("score")
    final_cp = final_score.pov(candidate.solver_color).score() if final_score else None

    final_win = (final_cp is not None and final_cp >= config.WINNING_ADVANTAGE)
    final_draw = (final_cp is not None and -config.DRAWING_RANGE < final_cp < config.DRAWING_RANGE)

    if final_win:
        return "Reversão" if (candidate.post_cp < 0) else "Blunder"
    elif final_draw:
        return "Equalização" if (candidate.post_cp < 0) else "Defesa"
    else:
        return "Defesa"

def determine_puzzle_phase(candidate):
    """
    Determina a fase da partida (Abertura, Meio-jogo ou Final) baseado no número de
    lances (fullmove_number) e quantidade de peças restantes (desconsiderando reis).
    """
    fullmove_num = candidate.board_pre_blunder.fullmove_number
    piece_count = sum(
        1 for sq in chess.SQUARES
        if candidate.board_pre_blunder.piece_at(sq)
        and candidate.board_pre_blunder.piece_at(sq).piece_type != chess.KING
    )

    if fullmove_num <= 10:
        return "Abertura"
    elif fullmove_num >= 30 or piece_count <= 10:
        return "Final"
    else:
        return "Meio-jogo"

def create_puzzle_tree(candidate, engine, depths, max_variants):
    """
    Cria a árvore completa do puzzle a partir de um candidato, usando as funções
    auxiliares para configurar cabeçalhos, determinar objetivo e fase.
    """
    # Criação do objeto PGN base
    puzzle_game = chess.pgn.Game()

    # Configura os cabeçalhos iniciais
    configure_headers(puzzle_game, candidate)

    # Adiciona o lance de blunder como primeiro movimento
    node = puzzle_game.add_main_variation(candidate.blunder_move)

    current_node = node
    current_board = candidate.board_post_blunder.copy()

    # Se houver sequência forçada, adicionar à linha principal
    for forced_move in candidate.forced_sequence:
        current_node = current_node.add_main_variation(forced_move)
        current_board.push(forced_move)

    # Estender a sequência do puzzle
    result = extend_puzzle_sequence(
        engine=engine,
        puzzle_node=current_node,
        board=current_board,
        solver_color=candidate.solver_color,
        max_variants=max_variants,
        depth=depths['solve'],
        min_moves=2  # Mínimo de 2 lances do solver
    )

    puzzle_ok = result.get("success", False)
    reason = result.get("reason", "desconhecido") if not puzzle_ok else None

    if not puzzle_ok:
        return puzzle_game, "Desconhecido", "Meio-jogo", False, reason

    final_board = result["final_board"]

    # Determinar objetivo
    objective = determine_puzzle_objective(engine, final_board, candidate, depths)

    # Determinar fase do jogo
    phase = determine_puzzle_phase(candidate)

    return puzzle_game, objective, phase, True, None

def collect_candidates(game, engine, depths, verbose=False, progress=None):
    """
    Escaneia uma partida completa e coleta todos os candidatos a puzzle.
    """
    candidates_list = []
    original_headers = game.headers.copy()
    board = game.board()

    # Avaliação inicial da posição
    try:
        info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['scan']))
    except Exception as e:
        if progress:
            progress.log(f"[red]Erro ao analisar posição inicial do jogo: {e}[/red]")
        return []

    prev_score = info.get("score")
    prev_cp = prev_score.pov(chess.WHITE).score() if prev_score else None

    # Itera pelos movimentos da linha principal
    move_number = 0
    for move in game.mainline_moves():
        move_number += 1
        side_to_move = "White" if board.turn == chess.WHITE else "Black"
        move_san = board.san(move)

        # Guarda posição antes do lance
        board_pre_blunder = board.copy()

        # Executa o lance
        board.push(move)

        # Nova análise após o lance
        try:
            info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['scan']))
        except Exception:
            info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['quick']))

        score = info.get("score")
        post_cp = score.pov(chess.WHITE).score() if score else None

        # Log detalhado se verbose estiver ativo
        if verbose and progress:
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

        # Verificar se é um candidato a puzzle
        is_candidate, candidate_data, reason = candidates.find_candidate(
            board, prev_score, prev_cp, score, post_cp, move_number,
            board_pre_blunder, depths, engine, verbose, progress
        )

        if is_candidate:
            # Criar objeto PuzzleCandidate com os dados necessários
            candidate = PuzzleCandidate(
                board_pre_blunder=board_pre_blunder,
                board_post_blunder=candidate_data["board_post"],
                adjusted_board=candidate_data["adjusted_board"],
                blunder_move=candidate_data["blunder_move"],
                forced_sequence=candidate_data["forced_sequence"],
                solver_color=candidate_data["solver_color"],
                post_cp=candidate_data["post_cp"],
                original_headers=original_headers,
                move_number=move_number
            )
            candidates_list.append(candidate)
        elif reason and verbose and progress:
            progress.log(f"[bold red]Descartado no lance {move_number}:[/] [bold]{reason}.[/]\n")

        # Atualiza a avaliação para o próximo lance
        prev_score = score
        prev_cp = post_cp

    return candidates_list

def generate_puzzles(input_path, output_path=None, depth=config.DEFAULT_DEPTH, max_variants=config.DEFAULT_MAX_VARIANTS, verbose=False, resume=False):
    """
    Analisa os jogos do arquivo PGN input_path e gera puzzles táticos conforme os critérios.
    Implementa o padrão "Escanear Tudo Primeiro".
    """
    # Preparar saída (arquivo ou console) - Modo append se resume=True
    output_handle = open(output_path, "a" if resume else "w", encoding="utf-8") if output_path else None
    engine = None
    was_interrupted = False

    # Calcular profundidades de análise utilizando o config
    depths = utils.calculate_depths(depth)

    try:
        # Detecta o caminho do Stockfish (priorizando o binário local)
        engine_path = utils.detect_stockfish_path()
        visual.print_stockfish_info(engine_path)

        # Inicia o Stockfish usando a função do módulo utils
        engine = utils.start_stockfish(engine_path)

        # Inicializa os dados de resume (ou reseta caso não esteja usando --resume)
        resume_data, games_analyzed, stats = resume_module.initialize_resume(input_path, puzzles_dir="puzzles", resume_flag=resume)
        if resume:
            visual.print_resume_info(games_analyzed)

        # Conta o número total de jogos no arquivo
        total_game_count = utils.count_games(input_path)

        # Exibe cabeçalho (informações iniciais tamanho do arquivo, total de jogos, etc.)
        file_size = utils.format_size(input_path)
        visual.print_initial_analysis_info(input_path, file_size, total_game_count, resume, games_analyzed, depth, depths, max_variants)

        # Cria o iterador e avança os jogos já analisados, se --resume
        games_iterator = utils.iterate_games(input_path)
        if resume:
            games_iterator = resume_module.skip_processed_games(games_iterator, games_analyzed)

        # Cria a barra de progresso com o tempo acumulado (caso --resume esteja ativo)
        with visual.create_progress(elapsed_offset=resume_data.get("elapsed_time", 0) if resume else 0) as progress:
            task_id = progress.add_task("[yellow]Analisando partidas...", total=total_game_count, completed=games_analyzed)

            # Processa cada jogo para gerar puzzles
            for game in games_iterator:
                # ETAPA 1: Escanear a partida para coletar todos os candidatos
                if verbose:
                    progress.log("[cyan]Escaneando partida para identificar candidatos...[/cyan]")

                candidates_list = collect_candidates(game, engine, depths, verbose, progress)

                if verbose:
                    progress.log(f"[cyan]Encontrados {len(candidates_list)} candidatos a puzzle[/cyan]")

                # ETAPA 2: Analisar cada candidato com profundidade
                for idx, candidate in enumerate(candidates_list):
                    if verbose:
                        progress.log(f"[yellow]Analisando candidato {idx+1}/{len(candidates_list)}...[/yellow]")

                    # Criar o puzzle a partir do candidato
                    puzzle_game, objective, phase, puzzle_ok, reason = create_puzzle_tree(
                        candidate, engine, depths, max_variants
                    )

                    # Processar o resultado
                    if puzzle_ok:
                        # Adicionar metadados ao puzzle
                        puzzle_game.headers["Objetivo"] = objective
                        puzzle_game.headers["Fase"] = phase

                        # Atualizar estatísticas
                        stats.update_objective(objective)
                        stats.update_phase(phase)
                        stats.add_found()

                        # Exportar o puzzle
                        if output_handle:
                            exporter.export_puzzle(puzzle_game, output_handle)

                        # Exibir informações
                        if not verbose:
                            visual.print_puzzle_found(progress, stats.puzzles_found, puzzle_game)
                        else:
                            visual.print_verbose_puzzle_generated(
                                progress,
                                f"[bold green]Puzzle #{stats.puzzles_found} gerado com sucesso.[/bold green]\n",
                                puzzle_game
                            )
                    else:
                        # Registrar motivo da rejeição
                        stats.add_rejected(reason)
                        if verbose and reason:
                            progress.log(f"[bold red]Candidato descartado:[/] [bold]{reason}.[/]\n")

                # Atualiza o contador acumulado de jogos processados
                stats.increment_games()
                # Atualiza os dados de resume usando os valores acumulados
                resume_module.update_resume_data(input_path, stats.total_games, stats, puzzles_dir="puzzles")

                progress.update(task_id,
                                advance=1,
                                description=f"[yellow]Analisando partidas... [green]Encontrados: {stats.puzzles_found} [red]Rejeitados: {stats.puzzles_rejected}",
                                refresh=True)
    except KeyboardInterrupt:
        was_interrupted = True
    except Exception:
        # Captura outras exceções, mas as propaga após limpeza
        if engine:
            engine.quit()
        if output_handle:
            output_handle.close()
        raise  # Re-lança a exceção original
    finally:
        # Limpeza de recursos
        if engine:
            engine.quit()
        if output_handle:
            output_handle.close()

    # Cria o objeto de resultado
    result = AnalysisResult(stats, was_interrupted)

    # Exibe estatísticas
    result.display_statistics(visual, output_path)

    # Retorna o objeto de resultado
    return result
