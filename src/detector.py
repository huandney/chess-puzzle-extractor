"""
detector.py - Detecção de candidatos a puzzles nas partidas.
"""
import chess
import chess.pgn

def find_candidates(game, engine, include_blunder=False):
    """
    Encontra posições candidatas a puzzles na partida fornecida.
    Retorna uma lista de nós (posições) candidatos.
    Se include_blunder=True, inclui posições onde houve um blunder (grande erro).
    """
    candidates = []
    # Configura o motor na posição inicial da partida
    initial_fen = game.headers.get("FEN", chess.STARTING_FEN)
    engine.set_fen_position(initial_fen)
    # Avalia a posição inicial
    prev_eval = engine.get_evaluation()
    # Percorre todos os lances da partida
    node = game
    while not node.is_end():
        next_node = node.variation(0)
        move = next_node.move
        # Aplica o lance no motor
        engine.make_moves_from_current_position([move.uci()])
        # Obtém a avaliação após o lance
        eval_after = engine.get_evaluation()
        if include_blunder:
            # Se existe avaliação anterior e ambas são em centipawns
            if prev_eval and prev_eval.get('Type') == 'cp' and eval_after.get('Type') == 'cp':
                cp_before = prev_eval.get('Value')
                cp_after = eval_after.get('Value')
                # Verifica grande queda ou subida na avaliação (indicando blunder)
                if (cp_before is not None and cp_after is not None and
                        ((cp_before > 100 and cp_after < -100) or (cp_before < -100 and cp_after > 100))):
                    # Marca a posição antes do lance como candidata a puzzle
                    candidates.append(node)
        # (Possível extensão para outros critérios de detecção de puzzle)
        prev_eval = eval_after
        node = next_node
    return candidates
