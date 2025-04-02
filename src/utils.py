"""
utils.py - Funções utilitárias para o projeto chess-puzzle-extractor.
"""
import chess.pgn

def load_pgn(file_path):
    """
    Carrega um arquivo PGN e retorna uma lista de objetos chess.pgn.Game.
    """
    games = []
    try:
        with open(file_path, 'r', encoding='utf-8') as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                games.append(game)
    except FileNotFoundError:
        print(f"PGN file not found: {file_path}")
    return games

def ensure_directory(path):
    """
    Garante que o diretório especificado em `path` existe.
    Se não existir, cria o diretório.
    """
    import os
    os.makedirs(path, exist_ok=True)
