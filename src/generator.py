"""
generator.py - Geração e verificação de puzzles.
"""
import chess

def generate_puzzle(game, candidate_node, engine):
    """
    Gera um puzzle a partir de uma posição candidata (nó da partida).
    No momento, retorna simplesmente uma representação de puzzle (dicionário)
    contendo a posição FEN e a sequência de solução.
    """
    # Gera um puzzle a partir da posição candidata.
    board = candidate_node.board()
    # Usa o motor para obter a melhor continuação a partir da posição candidata.
    engine.set_fen_position(board.fen())
    best_move = engine.get_best_move()
    if best_move is None:
        return None
    # Simplesmente cria um puzzle com um lance (o melhor lance segundo o motor).
    puzzle_fen = board.fen()
    puzzle_solution = [best_move]
    # Representa o puzzle como um dicionário com FEN e a sequência de solução (movimentos em UCI).
    puzzle = {
        "fen": puzzle_fen,
        "solution": puzzle_solution
    }
    return puzzle
