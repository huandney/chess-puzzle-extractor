# src/analysis.py (anteriormente ambiguity.py)
import chess
import chess.engine
from src import config
from src import utils

def analyze_solutions(engine, board, solver_color, max_variants, depth=None):
    depth = depth or config.DEFAULT_DEPTH
    multipv = max_variants + 2

    try:
        infos = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=multipv)
        if isinstance(infos, dict):
            infos = [infos]
    except chess.engine.EngineError:
        return None

    if not infos:
        return None

    scores = [utils.score_to_centipawn(info["score"], solver_color) for info in infos]
    best_score = scores[0]

    candidate_moves = [
        info["pv"][0] for info, score in zip(infos, scores)
        if best_score - score <= config.ALT_THRESHOLD
    ]

    if len(candidate_moves) > max_variants + 1:
        return None

    if len(scores) > 1 and best_score - scores[1] < config.PUZZLE_UNICITY_THRESHOLD:
        return None

    return {"best": candidate_moves[0], "alternatives": candidate_moves[1:]}

def opponent_response (engine, board, depth):
    try:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        return info["pv"][0] if "pv" in info and info["pv"] else None
    except chess.engine.EngineError:
        legal_moves = list(board.legal_moves)
        return legal_moves[0] if legal_moves else None
