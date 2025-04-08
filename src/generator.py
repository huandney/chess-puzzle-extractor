import os
import shutil
import chess
import chess.engine
import chess.pgn
import time
from collections import defaultdict
from rich.text import Text
from src import ambiguity
from src import exporter
from src import config
from src import visual

def format_eval(score):
    """
    Formata a pontuação do motor de xadrez para um formato legível.

    Args:
        score: Objeto Score do python-chess, contendo a avaliação

    Returns:
        str: String formatada representando a avaliação (ex: "1.45" ou "M5")
    """
    if score is None:
        return "?"
    try:
        if score.is_mate():
            mate = score.white().mate()
            return f"M{abs(mate)}" if mate else "0"
        cp = score.white().score()
        return f"{cp / 100:.2f}"
    except:
        return "?"


def generate_puzzles(input_path, output_path=None, depth=config.DEFAULT_DEPTH, max_variants=config.DEFAULT_MAX_VARIANTS, verbose=False, resume=False):
    """
    Analisa jogos do arquivo PGN input_path e gera puzzles táticos conforme critérios.

    Args:
        input_path (str): Caminho para o arquivo PGN contendo as partidas.
        output_path (str, optional): Caminho para o arquivo de saída dos puzzles (padrão: config.DEFAULT_OUTPUT).
        depth (int): Profundidade máxima de análise do motor (padrão: config.DEFAULT_DEPTH).
        max_variants (int): Número máximo de variantes alternativas permitidas (padrão: config.DEFAULT_MAX_VARIANTS).
        verbose (bool): Se True, exibe informações detalhadas durante análise.
        resume (bool): Se True, retoma a análise a partir do último jogo processado.

    Returns:
        tuple: (total_games, puzzles_found, puzzles_rejected, reason_stats)
    """
    # Inicializa contadores
    total_games = 0
    puzzles_found = 0
    puzzles_rejected = 0
    reason_stats = {
        "peça solta": 0,
        "apenas capturas": 0,
        "ganho não instrutivo": 0,
        "múltiplas soluções": 0,
        "sequência muito curta": 0
    }

    # Estatísticas adicionais, para os paineis
    objetivo_stats = defaultdict(int)  # Contagem por tipo de objetivo
    fase_stats = defaultdict(int)      # Contagem por fase de jogo
    tempo_inicio = time.time()         # Marca o início da análise

    # Abrir arquivo PGN de entrada
    try:
        pgn_file = open(input_path, "r", encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        raise

    # Contar número de jogos para barra de progresso
    total_games = 0
    try:
        # Contagem mais precisa usando o parser PGN
        pgn_copy = open(input_path, "r", encoding="utf-8", errors="ignore")
        while chess.pgn.read_game(pgn_copy) is not None:
            total_games += 1
        pgn_copy.close()
    except Exception:
        # Fallback para o método anterior se ocorrer erro
        total_games = 0
        for line in pgn_file:
            if line.strip().startswith("[Event"):
                total_games += 1
        pgn_file.seek(0)

    # Se nenhum jogo for encontrado, definir como pelo menos 1
    total_games = max(1, total_games)

    # Preparar saída (arquivo ou console)
    output_handle = None
    if output_path:
        output_handle = open(output_path, "w", encoding="utf-8")

    # Calcular profundidades de análise utilizando o config
    depths = config.calculate_depths(depth)

    # Detecta o caminho do Stockfish
    local_stockfish = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stockfish"))
    if os.path.isfile(local_stockfish):
        engine_path = local_stockfish  # usa o binário compilado local
    elif shutil.which("stockfish"):
        engine_path = "stockfish"      # usa o Stockfish instalado no sistema
    else:
        raise Exception("Nenhum executável do Stockfish foi encontrado. Compile ou instale o Stockfish.")

    # Exibe o caminho do Stockfish utilizando o módulo visual
    visual.print_stockfish_info(engine_path)

    # Tenta iniciar o engine
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as e:
        raise Exception(f"Não foi possível iniciar o Stockfish em '{engine_path}'. Erro: {e}")

    # Configurar retomada de progresso
    progress_file = None
    skip_games = 0
    progress_path = input_path + ".resume"
    if resume:
        try:
            # Verificar último jogo processado no arquivo de progresso
            with open(progress_path, "r") as pf:
                lines = pf.read().strip().split()
                if lines:
                    skip_games = int(lines[-1])
            visual.print_resume_info(skip_games)
        except FileNotFoundError:
            skip_games = 0
        # Pular jogos já processados em execução anterior
        for _ in range(skip_games):
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break
    else:
        # Reiniciar arquivo de progresso se existir
        open(progress_path, "w").close()
    # Abrir arquivo de progresso para registrar andamento
    try:
        progress_file = open(progress_path, "a")
    except Exception:
        progress_file = None

    # Cabeçalho inicial
    try:
        # Mostrar informações sobre o arquivo de entrada e definir tamanho em B, KB ou MB
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
    visual.print_initial_analysis_info(input_path, file_size, total_games, resume, skip_games, depth, depths, max_variants)

    # Usamos Progress com transient=False para manter a barra fixa e progress.log para as mensagens
    with visual.create_progress() as progress:
        # Adicionar tarefa principal
        task_id = progress.add_task("[yellow]Analisando partidas...", total=total_games, completed=skip_games)

        # Iterar por cada jogo no PGN
        game_count = skip_games
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break  # Fim do arquivo PGN
            game_count += 1

            # Obter headers originais do jogo
            original_headers = game.headers.copy()
            board = game.board()

            # Avaliação inicial da posição
            try:
                info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['scan']))
            except Exception as e:
                progress.log(f"[red]Erro ao analisar posição inicial do jogo {game_count}: {e}[/red]")
                continue
            prev_score = info.get("score")
            prev_cp = prev_score.pov(chess.WHITE).score() if prev_score else None

            # Iterar movimentos do jogo
            move_number = 0
            for move in game.mainline_moves():
                move_number += 1
                side_to_move = "White" if board.turn == chess.WHITE else "Black"
                move_san = board.san(move)
                board.push(move)

                # Nova análise após o lance
                try:
                    # Tentativa com profundidade normal
                    info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['scan']))
                except Exception:
                    # Fallback com profundidade reduzida em caso de erro
                    info = engine.analyse(board, limit=chess.engine.Limit(depth=depths['quick']))
                score = info.get("score")
                post_cp = score.pov(chess.WHITE).score() if score else None

                # Modo verbose: mostrar lance e avaliações antes/depois
                if verbose:
                    prev_str = format_eval(prev_score)
                    post_str = format_eval(score)
                    move_index = board.fullmove_number  # número do lance completo atual
                    log_prefix = f"{move_index}." if side_to_move == "White" else f"{move_index}..."

                    # Estilizar avaliação (vermelho/verde para variações significativas)
                    eval_text = Text()
                    eval_text.append(f"{log_prefix} {move_san}: eval ")
                    eval_text.append(prev_str, style="blue")
                    eval_text.append(" → ")

                    if prev_cp is not None and post_cp is not None:
                        diff = post_cp - prev_cp
                        if abs(diff) > 50:  # 0.5 peão de diferença
                            style = "red" if diff < 0 else "green"
                            eval_text.append(post_str, style=style)
                        else:
                            eval_text.append(post_str, style="blue")
                    else:
                        eval_text.append(post_str, style="blue")

                    progress.log(eval_text)

                # Verifica queda de avaliação (possível blunder)
                if prev_cp is not None and post_cp is not None:
                    eval_diff = prev_cp - post_cp
                    blunder = False
                    solver_color = None

                    if board.turn == chess.BLACK:  # Brancas acabaram de jogar e causou queda na avaliação
                        if eval_diff >= config.BLUNDER_THRESHOLD:
                            blunder = True
                            solver_color = chess.BLACK  # Pretas devem resolver
                    else:  # Pretas acabaram de jogar e causou queda na avaliação
                        if eval_diff <= -config.BLUNDER_THRESHOLD:
                            blunder = True
                            solver_color = chess.WHITE  # Brancas devem resolver

                    if blunder:
                        # Candidato a puzzle detectado
                        if verbose:
                            diff = abs(post_cp - prev_cp)
                            diff_pawn = diff / 100.0
                            side = "Brancas" if solver_color == chess.WHITE else "Pretas"
                            prev_str = format_eval(prev_score)
                            post_str = format_eval(score)
                            progress.log(f"[bold yellow]Candidato a puzzle detectado no lance {move_number}[/bold yellow]\n"
                                         f"{side_to_move} cometeu erro: avaliação {prev_str} → {post_str}\n"
                                         f"Diferença: {diff_pawn:.2f} peões")
                        puzzle_ok = True
                        reason = None

                        # 1. Filtro de vantagem prévia: solver_color já tinha grande vantagem?
                        solver_prev_adv = prev_cp if solver_color == chess.WHITE else (-prev_cp if prev_cp else None)
                        if solver_prev_adv and solver_prev_adv > config.WINNING_ADVANTAGE:
                            puzzle_ok = False
                            reason = "ganho não instrutivo"
                            reason_stats["ganho não instrutivo"] += 1

                        # 2. Gerar sequência de solução (caso passe filtros anteriores)
                        if puzzle_ok:
                            # Preparar posições de partida para o puzzle
                            board_post_blunder = board.copy()    # posição após o lance errado
                            board_pre_blunder = board.copy()
                            board_pre_blunder.pop()             # voltar ao lance pré-blunder

                            # Montar objeto Game do puzzle
                            puzzle_game = chess.pgn.Game()
                            # Copiar headers originais
                            for tag, value in original_headers.items():
                                puzzle_game.headers[tag] = value
                            # Adicionar FEN da posição inicial do puzzle
                            puzzle_game.headers["SetUp"] = "1"
                            puzzle_game.headers["FEN"] = board_pre_blunder.fen()
                            # Manter resultado original
                            if "Result" in original_headers:
                                puzzle_game.headers["Result"] = original_headers["Result"]

                            # Montar linha principal e variações do puzzle
                            node = puzzle_game
                            # Adicionar lance de blunder do adversário como primeiro lance do puzzle
                            blunder_move = move
                            node = node.add_main_variation(blunder_move)
                            # (Agora node representa a posição após o blunder, vez do solver jogar)

                            # a) Primeiro lance do solucionador (S1)
                            solver_board = board_post_blunder.copy()
                            # Análise de ambiguidade (melhor lance e alternativas viáveis)
                            candidates = ambiguity.find_alternatives(engine, solver_board, solver_color, max_variants, depth=depths['solve'])
                            if candidates is None:
                                # Se muitas alternativas equivalentes, puzzle rejeitado
                                puzzle_ok = False
                                reason = "múltiplas soluções"
                                reason_stats["múltiplas soluções"] += 1
                            else:
                                # Adicionar melhor lance e alternativas à árvore de variações
                                best_move = candidates["best"]
                                alt_moves = candidates["alternatives"]
                                node_s1 = node.add_main_variation(best_move)
                                for alt in alt_moves:
                                    node.add_variation(alt)

                                # b) Resposta do oponente (O1)
                                opponent_board = solver_board.copy()
                                opponent_board.push(best_move)
                                try:
                                    # Análise profunda para resposta do oponente
                                    info_opp = engine.analyse(opponent_board, limit=chess.engine.Limit(depth=depths['solve']))
                                except Exception:
                                    # Fallback com profundidade menor
                                    info_opp = engine.analyse(opponent_board, limit=chess.engine.Limit(depth=depths['scan']))
                                # Extrair melhor resposta do oponente
                                opp_move = None
                                if "pv" in info_opp:
                                    pv_line = info_opp["pv"]
                                    if pv_line:
                                        opp_move = pv_line[0]
                                # Fallback: qualquer lance legal se não houver sugestão
                                if opp_move is None:
                                    opp_move = list(opponent_board.legal_moves)[0]
                                node_o1 = node_s1.add_main_variation(opp_move)

                                # c) Segundo lance do solucionador (S2)
                                solver_board2 = opponent_board.copy()
                                solver_board2.push(opp_move)
                                # Nova análise de ambiguidade para S2
                                candidates2 = ambiguity.find_alternatives(engine, solver_board2, solver_color, max_variants, depth=depths['solve'])
                                if candidates2 is None:
                                    puzzle_ok = False
                                    reason = "múltiplas soluções"
                                    reason_stats["múltiplas soluções"] += 1
                                else:
                                    # Adicionar segundo lance e alternativas
                                    best_move2 = candidates2["best"]
                                    alt_moves2 = candidates2["alternatives"]
                                    node_s2 = node_o1.add_main_variation(best_move2)
                                    for alt2 in alt_moves2:
                                        node_o1.add_variation(alt2)
                                    # Aqui poderia ser adicionada extensão para S3, S4, etc.

                        # 3. Filtro de comprimento mínimo da sequência
                        if puzzle_ok:
                            # Contar total de half-moves na linha principal do puzzle
                            half_moves = 0
                            node_iter = puzzle_game
                            while node_iter.variations:
                                node_iter = node_iter.variations[0]
                                half_moves += 1
                            # Rejeitar puzzles muito curtos (< 4 meios-lances)
                            if half_moves < 4:
                                puzzle_ok = False
                                reason = "sequência muito curta"
                                reason_stats["sequência muito curta"] += 1

                        # Decisão final sobre o puzzle
                        if puzzle_ok:
                            # Categorizar objetivo e fase do jogo nos headers PGN
                            node_iter = puzzle_game
                            while node_iter.variations:
                                node_iter = node_iter.variations[0]
                            final_board = node_iter.board()

                            # Determinar objetivo (mate, reversão, equalização, defesa ou blunder)
                            if final_board.is_checkmate():
                                objective = "Mate"
                            else:
                                # Avaliar posição final com menos profundidade (quick)
                                final_info = engine.analyse(final_board, limit=chess.engine.Limit(depth=depths['quick']))
                                final_score = final_info.get("score")
                                final_cp = final_score.pov(solver_color).score() if final_score else None

                                # Definir tipo de puzzle com base na avaliação final
                                final_win = (final_cp is not None and final_cp >= config.WINNING_ADVANTAGE)
                                final_draw = (final_cp is not None and -config.DRAWING_RANGE < final_cp < config.DRAWING_RANGE)

                                if final_win:
                                    # Vitória: distinguir entre reversão (estava perdendo) e blunder normal
                                    objective = "Reversão" if solver_prev_adv is not None and solver_prev_adv < 0 else "Blunder"
                                elif final_draw:
                                    # Empate: distinguir entre equalização (estava perdendo) e defesa normal
                                    objective = "Equalização" if solver_prev_adv is not None and solver_prev_adv < 0 else "Defesa"
                                else:
                                    objective = "Defesa"

                            # Determinar fase (abertura, meio-jogo ou final)
                            fullmove_num = board_pre_blunder.fullmove_number
                            # Contar peças não-rei no tabuleiro
                            piece_count = sum(
                                1
                                for sq in chess.SQUARES
                                if board_pre_blunder.piece_at(sq)
                                and board_pre_blunder.piece_at(sq).piece_type != chess.KING
                            )

                            # Aplicar critérios de fase baseados em lance e peças
                            if fullmove_num <= 10:
                                phase = "Abertura"
                            elif fullmove_num >= 30 or piece_count <= 10:
                                phase = "Final"
                            else:
                                phase = "Meio-jogo"

                            # Adicionar metadados ao puzzle
                            puzzle_game.headers["Objetivo"] = objective
                            puzzle_game.headers["Fase"] = phase

                            # Atualizar estatísticas por categoria
                            objetivo_stats[objective] += 1
                            fase_stats[phase] += 1

                            puzzles_found += 1
                            if output_handle:
                                exporter.export_puzzle(puzzle_game, output_handle)

                            # Exibir puzzle gerado
                            if not verbose:
                                visual.print_puzzle_found(progress, puzzles_found, puzzle_game)
                            else:
                                visual.print_verbose_puzzle_generated(progress, "[bold green]Puzzle gerado com sucesso.[/bold green]\n", puzzle_game)
                        else:
                            puzzles_rejected += 1
                            if verbose and reason:
                                progress.log(f"[bold red]Descartado:[/] [bold]{reason}.[/]\n")
                prev_score = score
                prev_cp = post_cp

            progress.update(
                task_id,
                advance=1,
                description=f"[yellow]Analisando partidas... [green]Encontrados: {puzzles_found} [red]Rejeitados: {puzzles_rejected}",
                refresh=True  # Força atualização da barra
            )
            if progress_file:
                progress_file.write(f"{game_count}\n")
                progress_file.flush()

    engine.quit()
    if progress_file:
        progress_file.close()

    # Cálculo do tempo ao final da função
    total_time = time.time() - start_time
    average_time_per_game = total_time / max(1, game_count)

    # Apresentação final das estatísticas utilizando o módulo visual através da função render_final_statistics
    if verbose:
        print()  # Adiciona uma linha em branco apenas no modo verbose
    visual.render_final_statistics(game_count, puzzles_found, puzzles_rejected, tempo_total, tempo_medio_por_jogo, reason_stats, objetivo_stats, fase_stats, output_path)

    return game_count, puzzles_found, puzzles_rejected, reason_stats
