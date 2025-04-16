# src/candidates.py
import chess
import chess.engine
from src import config
from src import utils

def detect_eval_drop(board, prev_cp, post_cp):
    """
    Detecta queda de avaliação (blunder) analisando se houve uma queda significativa
    na avaliação da posição após um lance.

    Retorna: (blunder, solver_color) onde blunder é boolean e solver_color é a cor que resolve
    """
    if prev_cp is None or post_cp is None:
        return False, None

    blunder = False
    solver_color = None
    eval_diff = prev_cp - post_cp

    if board.turn == chess.BLACK:  # Brancas jogaram e a avaliação caiu
        if eval_diff >= config.BLUNDER_THRESHOLD:
            blunder = True
            solver_color = chess.BLACK  # Pretas devem resolver
    else:  # Pretas jogaram e a avaliação caiu
        if eval_diff <= -config.BLUNDER_THRESHOLD:
            blunder = True
            solver_color = chess.WHITE  # Brancas devem resolver

    return blunder, solver_color

def is_forced_move(board):
    """
    Verifica se existe apenas um lance legal ou se é uma posição de xeque com único escape.
    Um lance é considerado forçado APENAS se:
    1. Há apenas um lance legal disponível
    2. Há um xeque e apenas uma forma de escapar

    Retorna: True se for um lance forçado
    """
    # Verificar número de lances legais
    legal_moves = list(board.legal_moves)

    # Se houver apenas um lance legal, é forçado
    if len(legal_moves) == 1:
        return True

    # Se estiver em xeque e houver poucas opções, ainda pode ser considerado forçado
    if board.is_check() and len(legal_moves) <= 2:
        return True

    # Em todos os outros casos, não é forçado
    return False

def get_best_move(board, engine, depth):
    """
    Obtém o melhor lance para a posição atual.

    Retorna: O melhor lance ou None se não for possível determinar
    """
    try:
        info = engine.analyse(board, limit=chess.engine.Limit(depth=depth))
        if "pv" in info and info["pv"]:
            return info["pv"][0]
    except Exception:
        pass

    return None

def skip_forced_moves(board, engine, solver_color, depth):
    """
    Avança a posição inicial do puzzle para pular sequências de lances forçados.
    IMPORTANTE: Apenas lances do SOLVER são considerados para pular, não os do oponente.

    Retorna: (adjusted_board, forced_sequence, is_valid)
    - adjusted_board: Posição ajustada após pular lances forçados
    - forced_sequence: Lista de lances que foram executados
    - is_valid: False se toda a sequência inicial for de lances forçados
    """
    current_board = board.copy()
    forced_sequence = []
    found_non_forced = False

    # Máximo de lances para verificar
    max_moves = 5
    moves_checked = 0

    while moves_checked < max_moves:
        # Se não for a vez do solucionador, executar o melhor lance do oponente e continuar
        if current_board.turn != solver_color:
            opponent_move = get_best_move(current_board, engine, depth)
            if opponent_move:
                current_board.push(opponent_move)
                forced_sequence.append(opponent_move)
                moves_checked += 1
                continue
            else:
                break

        # Quando for a vez do solucionador, verificar se o lance é forçado
        if is_forced_move(current_board):
            # É um lance forçado, executar e continuar
            solver_move = get_best_move(current_board, engine, depth)
            if solver_move:
                current_board.push(solver_move)
                forced_sequence.append(solver_move)
                moves_checked += 1
            else:
                break
        else:
            # Encontramos um lance não-forçado para o solucionador
            found_non_forced = True
            break

    # Se não encontramos nenhum lance não-forçado para o solucionador, o puzzle é inválido
    is_valid = found_non_forced

    return current_board, forced_sequence, is_valid

def check_hanging_piece(board, engine, last_move, depth):
    """
    Verifica se o lance foi apenas deixar uma peça desprotegida.

    Retorna: True se for peça solta, False caso contrário
    """
    # Obter o quadrado de destino e a peça
    to_square = last_move.to_square
    piece = board.piece_at(to_square)

    # Se não houver peça no destino, não é hanging piece
    if piece is None:
        return False

    # Lado que jogará a seguir
    side_to_move = board.turn

    # Verificar se a peça está ameaçada
    attackers = list(board.attackers(side_to_move, to_square))
    if not attackers:
        return False  # A peça não está sendo ameaçada

    # Verificar se a peça está defendida
    defenders = list(board.attackers(not side_to_move, to_square))

    # Se estiver bem defendida, não é peça solta
    if len(defenders) >= len(attackers):
        return False

    # Analisar com o engine para ver se capturar a peça é o melhor lance
    try:
        info = engine.analyse(board, limit=chess.engine.Limit(depth=depth), multipv=2)
        if isinstance(info, dict):
            info = [info]

        if not info or len(info) < 1:
            return False

        # Verificar se o melhor lance é capturar a peça
        best_move = None
        if "pv" in info[0] and info[0]["pv"]:
            best_move = info[0]["pv"][0]

        if best_move is None:
            return False

        is_capture_of_hanging = best_move.to_square == to_square

        # Se o melhor lance não é capturar a peça, não é hanging piece
        if not is_capture_of_hanging:
            return False

        # Se houver uma segunda opção boa, não é apenas hanging piece
        if len(info) > 1:
            best_score = info[0].get("score")
            second_score = info[1].get("score")

            if best_score and second_score:
                # Calcular valores relativos para comparação
                if best_score.is_mate():
                    best_cp = 10000 if best_score.relative.mate() > 0 else -10000
                else:
                    best_cp = best_score.relative.score() or 0

                if second_score.is_mate():
                    second_cp = 10000 if second_score.relative.mate() > 0 else -10000
                else:
                    second_cp = second_score.relative.score() or 0

                # Se a diferença for pequena, há outras opções táticas interessantes
                if abs(best_cp - second_cp) < 400:
                    return False

        # É uma peça solta se o melhor lance é capturá-la e a vantagem é clara
        return True

    except Exception:
        return False

def check_captures_sequence(board, engine, depth, max_moves=5):
    """
    Verifica se a sequência é apenas uma série de capturas diretas.

    Retorna: True se for sequência de capturas diretas, False caso contrário
    """
    current_board = board.copy()
    moves_analyzed = 0

    while moves_analyzed < max_moves:
        # Se o jogo acabou, encerra a análise
        if current_board.is_game_over():
            break

        try:
            # Analisar a posição
            info = engine.analyse(current_board, limit=chess.engine.Limit(depth=depth))

            # Obter o melhor lance
            best_move = None
            if "pv" in info and info["pv"]:
                best_move = info["pv"][0]

            if best_move is None:
                break

            # Verificar se é uma captura
            is_capture = current_board.is_capture(best_move)

            # Se não for captura, não é sequência de capturas diretas
            if not is_capture:
                return False

            # Jogar o lance e continuar a análise
            current_board.push(best_move)
            moves_analyzed += 1

        except Exception:
            break

    # É uma sequência de capturas diretas se analisamos pelo menos dois lances
    # e todos eles foram capturas
    return moves_analyzed >= 2

def find_candidate(board, prev_score, prev_cp, score, post_cp, move_number, board_pre_blunder, depths, engine, verbose=False, progress=None):
    """
    Analisa a posição para verificar se é candidato a puzzle, aplicando filtros sequenciais.

    Retorna: (is_candidate, candidate_data, reason)
        is_candidate: Boolean indicando se é um candidato válido
        candidate_data: Dicionário com dados do candidato ou None
        reason: Razão da rejeição ou None
    """
    # 1. Filtro de Queda de Avaliação (Blunder Detection)
    blunder, solver_color = detect_eval_drop(board, prev_cp, post_cp)

    if not blunder:
        return False, None, None

    # Log do candidato encontrado se verbose estiver ativo
    if verbose and progress:
        side_to_move = "White" if board.turn == chess.BLACK else "Black"
        diff = abs(post_cp - prev_cp)
        diff_pawn = diff / 100.0
        solver_side = "Brancas" if solver_color == chess.WHITE else "Pretas"
        prev_str = utils.format_eval(prev_score)
        post_str = utils.format_eval(score)
        progress.log(f"[bold yellow]Candidato a puzzle detectado no lance {move_number}[/bold yellow]\n"
                     f"{side_to_move} cometeu erro: avaliação {prev_str} → {post_str}\n"
                     f"Diferença: {diff_pawn:.2f} peões")

    # Obter o último lance jogado (o blunder)
    last_move = None
    for move in board_pre_blunder.legal_moves:
        new_board = board_pre_blunder.copy()
        new_board.push(move)
        if new_board.fen() == board.fen():
            last_move = move
            break

    if last_move is None:
        return False, None, "movimento não identificado"

    # 2. Filtro de Avanço de Posição Inicial (Skip Forced Moves)
    adjusted_board, forced_sequence, is_valid = skip_forced_moves(
        board, engine, solver_color, depths['quick']
    )

    if not is_valid:
        if verbose and progress:
            progress.log("[yellow]Filtro: Sequência completamente forçada detectada[/yellow]")
        return False, None, "sequência forçada"

    # 3. Filtro de Peça Solta (Hanging Piece)
    if check_hanging_piece(board, engine, last_move, depths['quick']):
        if verbose and progress:
            progress.log("[yellow]Filtro: Peça solta detectada[/yellow]")
        return False, None, "peça solta"

    # 4. Filtro de Sequência de Capturas Diretas
    is_blunder_capture = board.is_capture(last_move)

    if is_blunder_capture:
        if check_captures_sequence(board, engine, depths['quick']):
            if verbose and progress:
                progress.log("[yellow]Filtro: Sequência de capturas diretas detectada[/yellow]")
            return False, None, "apenas capturas"

    # Passou por todos os filtros, retorna informações do candidato
    candidate_data = {
        "board_post": board.copy(),
        "board_pre": board_pre_blunder,
        "adjusted_board": adjusted_board,
        "solver_color": solver_color,
        "post_cp": post_cp,
        "forced_sequence": forced_sequence,
        "blunder_move": last_move
    }

    return True, candidate_data, None
