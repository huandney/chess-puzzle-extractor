"""
analysis.py - Motor de análise e integração com o Stockfish
"""
import chess
from stockfish import Stockfish

def create_engine(depth=15, threads=2, memory=256):
    """
    Inicializa uma instância do motor Stockfish com os parâmetros fornecidos.
    Retorna um objeto Stockfish pronto para uso.
    """
    params = {
        "Threads": threads,
        "Hash": memory,
        "MultiPV": 1
    }
    try:
        engine = Stockfish(parameters=params)
    except Exception:
        engine = Stockfish(path="./Stockfish/src/stockfish", parameters=params)
    engine.set_depth(depth)
    return engine

def analyze_position(engine, board_fen):
    """
    Analisa uma posição dada (FEN) usando o motor Stockfish.
    Retorna informações de avaliação (centipawn ou mate).
    """
    engine.set_fen_position(board_fen)
    return engine.get_evaluation()

def close_engine(engine):
    """
    Encerra corretamente o processo do motor Stockfish, se necessário.
    """
    try:
        del engine
    except Exception:
        pass
