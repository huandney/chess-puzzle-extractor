import chess.pgn
import os
import shutil

# Abre o arquivo PGN e gera um jogo por vez
def iterate_games(input_path):
    try:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                yield game
    except FileNotFoundError:
        raise

# Conta o número de jogos no arquivo PGN utilizando iterate_games
def count_games(input_path):
    total_game_count = 0
    try:
        for _ in iterate_games(input_path):
            total_game_count += 1
    except Exception:
        total_game_count = 1
    return max(1, total_game_count)

# Formata a avaliação do engine para uma string legível
def format_eval(score):
    if score is None:
        return "?"
    try:
        if score.is_mate():
            mate = score.white().mate()
            return f"M{abs(mate)}" if mate else "0"
        cp = score.white().score()
        return f"{cp / 100:.2f}"
    except Exception:
        return "?"

# Retorna uma string com o tamanho do arquivo formatado
def format_size(input_path: str) -> str:
    try:
        size = os.path.getsize(input_path)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 ** 2):.2f} MB"
    except OSError:
        return "0.00 B"

# Detecta o caminho do Stockfish usando o binário local ou o instalado no sistema
def detect_stockfish_path():
    local_stockfish = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stockfish"))
    if os.path.isfile(local_stockfish):
        return local_stockfish  # Usa o binário local
    elif shutil.which("stockfish"):
        return "stockfish"      # Usa o Stockfish instalado no sistema
    else:
        raise Exception("Nenhum executável do Stockfish foi encontrado. Compile ou instale o Stockfish.")

# Inicia o Stockfish a partir do engine_path fornecido
def start_stockfish(engine_path: str):
    try:
        return chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as e:
        raise Exception(f"Não foi possível iniciar o Stockfish em '{engine_path}'. Erro: {e}")

# Determina o caminho de saída padrão ("<nome_do_arquivo>_puzzles.pgn) ou personalizado
def get_default_output_path(input_path: str, output: str = None, puzzles_dir: str = "puzzles") -> str:
    if output is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        os.makedirs(puzzles_dir, exist_ok=True)
        return os.path.join(puzzles_dir, f"{base_name}_puzzles.pgn")
    return output
