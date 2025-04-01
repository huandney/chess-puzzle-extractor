import logging
import os
import chess
from chess.engine import SimpleEngine, Limit, Score, PovScore

class AnalysisEngine:
    _instance = None

    @classmethod
    def initialize(cls, threads=4, memory=2048):
        """Inicializa o engine de análise"""
        if cls._instance:
            cls._instance.quit()

        # Localizar Stockfish
        stockfish_path = find_stockfish()
        if not stockfish_path:
            raise RuntimeError("Stockfish não encontrado. Execute ./build_stockfish.sh primeiro.")

        logging.info(f"Usando Stockfish em: {stockfish_path}")
        engine = SimpleEngine.popen_uci(stockfish_path)
        engine.configure({"Threads": threads, "Hash": memory})

        # Adicionar o método evaluate_position ao objeto engine
        def evaluate_position(board, depth):
            result = engine.analyse(board, Limit(depth=depth))
            return result["score"].relative

        engine.evaluate_position = evaluate_position

        cls._instance = engine
        return cls._instance

    @classmethod
    def instance(cls):
        """Retorna a instância atual do engine"""
        if not cls._instance:
            return cls.initialize()
        return cls._instance

    @classmethod
    def quit(cls):
        """Finaliza o engine"""
        if cls._instance:
            cls._instance.quit()
            cls._instance = None

    @classmethod
    def analyze(cls, board, depth, multipv=1):
        """Analisa a posição atual com opção multipv"""
        try:
            result = cls.instance().analyse(
                board,
                Limit(depth=depth),
                multipv=multipv
            )
            return result
        except Exception as e:
            logging.error(f"Erro de análise: {e}")
            # Reiniciar engine se necessário
            cls.initialize()
            return cls.instance().analyse(
                board,
                Limit(depth=depth),
                multipv=multipv
            )

    @classmethod
    def evaluate_position(cls, board, depth):
        """Retorna a avaliação da posição atual"""
        result = cls.analyze(board, depth)
        return result["score"].relative

def find_stockfish():
    """Encontra o binário do Stockfish"""
    # Procura em locais comuns
    search_paths = [
        "./stockfish-*",                # Compilado localmente
        "/usr/local/bin/stockfish",     # Instalado no sistema
        "/usr/bin/stockfish",
        os.path.expanduser("~/stockfish-*")
    ]

    for path in search_paths:
        import glob
        matches = glob.glob(path)
        if matches:
            return matches[0]

    return None

def score_is_better(score1, score2, threshold=60):
    """Verifica se score1 é significativamente melhor que score2"""
    if score1.is_mate() and not score2.is_mate():
        return True
    elif not score1.is_mate() and score2.is_mate():
        return score2.mate() < 0
    elif score1.is_mate() and score2.is_mate():
        if score1.mate() > 0 and score2.mate() < 0:
            return True
        if score1.mate() > 0 and score2.mate() > 0:
            return score1.mate() < score2.mate()
        if score1.mate() < 0 and score2.mate() < 0:
            return score1.mate() > score2.mate()
    else:
        return score1.score() - score2.score() > threshold
