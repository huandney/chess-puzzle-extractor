import logging
import chess
from chess.engine import Cp

from src.utils import material_count, material_value

def find_puzzle_candidates(game, engine, scan_depth):
    """Encontra possíveis posições de puzzles em um jogo"""
    candidates = []
    prev_score = Cp(0)
    node = game

    logging.debug(f"Escaneando jogo com profundidade {scan_depth}...")

    while not node.is_end():
        next_node = node.variation(0)
        next_board = next_node.board()

        # Obter avaliação atual
        curr_score = engine.evaluate_position(next_board, scan_depth)

        # Verificar se é uma posição interessante
        if should_investigate(prev_score, curr_score, node.board()):
            logging.debug(f"Posição encontrada após {node.board().san(next_node.move)}")
            candidates.append({
                'board': node.board().copy(),
                'move': next_node.move,
                'prev_score': prev_score,
                'curr_score': curr_score
            })

        prev_score = curr_score
        node = next_node

    return candidates

def should_investigate(prev_score, curr_score, board):
    """
    Determina se a posição é interessante para um puzzle.

    Esta função combina os melhores critérios dos três projetos.
    """
    # Ignorar se há poucas peças (exceto em mates)
    if material_count(board) < 5 and not (prev_score.is_mate() or curr_score.is_mate()):
        return False

    # Casos de mate
    if curr_score.is_mate():
        # De uma posição equilibrada para um mate
        if not prev_score.is_mate() and abs(prev_score.score()) < 150:
            return True
        # De uma posição vantajosa para um mate do adversário
        if not prev_score.is_mate() and sign(prev_score) != sign(curr_score):
            return True

    # Casos de mudança significativa de avaliação
    if not prev_score.is_mate() and not curr_score.is_mate():
        prev_cp = prev_score.score()
        curr_cp = curr_score.score()

        # Mudança significativa na avaliação
        if abs(curr_cp - prev_cp) >= 150:
            return True

        # De vantagem significativa para posição equilibrada
        if abs(prev_cp) > 300 and abs(curr_cp) < 90:
            return True

        # De vantagem para desvantagem (ou vice-versa)
        if sign(prev_cp) != sign(curr_cp) and abs(prev_cp) > 100 and abs(curr_cp) > 100:
            return True

    # Mudança entre mate e não mate
    if prev_score.is_mate() and not curr_score.is_mate():
        # Perdeu um mate
        if sign(prev_score) != sign(curr_score):
            return True
        # De mate para posição equilibrada
        if abs(curr_score.score()) < 150:
            return True

    return False

def sign(score):
    """Retorna o sinal da avaliação"""
    if isinstance(score, int):
        return 1 if score > 0 else -1
    elif score.is_mate():
        return 1 if score.mate() > 0 else -1
    else:
        return 1 if score.score() > 0 else -1
