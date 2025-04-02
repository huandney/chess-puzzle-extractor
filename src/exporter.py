"""
exporter.py - Exportação de puzzles para o formato PGN.
"""
import chess
import chess.pgn
import os

def export_puzzles(puzzles, output_path):
    """
    Exporta uma lista de puzzles para um arquivo PGN.
    Cada puzzle é um dicionário com 'fen' (posição inicial) e 'solution' (lista de lances em UCI).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as pgn_file:
        for idx, puzzle in enumerate(puzzles, start=1):
            fen = puzzle.get("fen")
            moves = puzzle.get("solution", [])
            board = chess.Board(fen)
            game = chess.pgn.Game()
            if fen and fen != chess.STARTING_FEN:
                game.setup(board)
            game.headers["Event"] = f"Puzzle {idx}"
            game.headers["FEN"] = fen
            game.headers["SetUp"] = "1" if fen and fen != chess.STARTING_FEN else "0"
            game.headers["Result"] = "*"
            node = game
            for uci_move in moves:
                move = chess.Move.from_uci(uci_move)
                node = node.add_variation(move)
            exporter = chess.pgn.FileExporter(pgn_file)
            game.accept(exporter)
            pgn_file.write("\n\n")
