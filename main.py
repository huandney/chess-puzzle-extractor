import argparse
from src import generator
import shutil
import subprocess
import os

def ensure_stockfish_available():
    if shutil.which("stockfish") is None and not os.path.isfile("./stockfish"):
        print("Stockfish não encontrado. Baixando binário otimizado...")
        subprocess.run(["bash", "build_stockfish.sh"], check=True)

ensure_stockfish_available()

parser = argparse.ArgumentParser(description="Extrair puzzles táticos de partidas de xadrez em PGN")
parser.add_argument("input", help="Arquivo PGN de entrada com partidas")
parser.add_argument("--output", "-o", help="Arquivo de saída para puzzles (padrão: puzzles.pgn)", default="puzzles.pgn")
parser.add_argument("--depth", "-d", type=int, help="Profundidade da análise do motor (padrão: 12)", default=12)
parser.add_argument("--max-variants", "-m", type=int, help="Máximo de variantes alternativas na solução (padrão: 2)", default=2)
parser.add_argument("--resume", "-r", action="store_true", help="Retomar do último progresso salvo (não reanalisar jogos já processados)")
parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar saída verbosa (detalhes da análise)")
args = parser.parse_args()

# Chamar a geração de puzzles com os parâmetros fornecidos
total_games, puzzles_found, puzzles_rejected, reason_stats = generator.generate_puzzles(
    args.input, args.output, depth=args.depth, max_variants=args.max_variants, verbose=args.verbose, resume=args.resume
)

print(f"Puzzles encontrados: {puzzles_found} (descartados: {puzzles_rejected})")
