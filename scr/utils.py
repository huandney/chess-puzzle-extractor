import chess

def material_count(board):
    """Retorna o número total de peças no tabuleiro"""
    return chess.popcount(board.occupied)

def material_value(board):
    """Calcula o valor material total no tabuleiro"""
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0  # O rei não conta para valor material
    }

    total = 0
    for piece_type in values:
        total += values[piece_type] * len(board.pieces(piece_type, chess.WHITE))
        total += values[piece_type] * len(board.pieces(piece_type, chess.BLACK))

    return total

def material_difference(board):
    """Calcula a diferença material entre brancas e pretas"""
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }

    white_value = 0
    black_value = 0

    for piece_type in values:
        white_value += values[piece_type] * len(board.pieces(piece_type, chess.WHITE))
        black_value += values[piece_type] * len(board.pieces(piece_type, chess.BLACK))

    return white_value - black_value

def is_ambiguous(analyzed_moves, threshold=90):
    """
    Verifica se a posição é ambígua (não há um único melhor movimento claro).

    Combinando as melhores abordagens do PuzzleMaker e Chess Tactic Finder.
    """
    if len(analyzed_moves) <= 1:
        return False

    best_move = analyzed_moves[0]
    second_best = analyzed_moves[1]

    # Comparar avaliações
    if best_move.score.is_mate() and second_best.score.is_mate():
        # Se ambos são mates, verificar se são equivalentes
        if best_move.score.mate() > 0 and second_best.score.mate() > 0:
            # Se os dois levam a mate, verificar diferença de movimentos
            return abs(best_move.score.mate() - second_best.score.mate()) <= 1
        # Diferentes sinais de mate (um positivo, outro negativo)
        return False

    elif best_move.score.is_mate() and not second_best.score.is_mate():
        # Mate vs avaliação numérica
        # Não é ambíguo se o mate é positivo
        if best_move.score.mate() > 0:
            return False
        # Se o mate é negativo, verificar se segunda melhor é boa
        return second_best.score.score() > 0

    elif not best_move.score.is_mate() and second_best.score.is_mate():
        # Avaliação numérica vs mate
        # Não é ambíguo se o mate é negativo
        if second_best.score.mate() < 0:
            return False
        # Se mate é positivo, é ambíguo se melhor avaliação é boa
        return best_move.score.score() > 0

    else:
        # Comparar avaliações numéricas
        diff = abs(best_move.score.score() - second_best.score.score())

        # Não ambíguo se diferença é significativa
        if diff > threshold:
            return False

        # Posições equilibradas ou ligeiramente vantajosas
        if abs(best_move.score.score()) < 150:
            return diff < 50

        # Posições com vantagem significativa
        return diff < 150
