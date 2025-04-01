#!/usr/bin/env python3

"""Chess Puzzle Extractor - Cria puzzles de xadrez de alta qualidade a partir de PGNs"""

import argparse
import logging
import sys
import os
from datetime import datetime

from src.analysis import AnalysisEngine
from src.detector import find_puzzle_candidates
from src.generator import generate_puzzle
from src.exporter import export_puzzle

def main():
    parser = argparse.ArgumentParser(description=__doc__)

    # Opções de input
    parser.add_argument("--pgn", type=str, required=True,
                      help="Arquivo PGN para analisar")

    # Opções do engine
    parser.add_argument("--threads", type=int, default=4,
                      help="Número de threads para o Stockfish")
    parser.add_argument("--memory", type=int, default=2048,
                      help="Memória em MB para tabelas hash do engine")
    parser.add_argument("--depth", type=int, default=18,
                      help="Profundidade principal de análise")
    parser.add_argument("--scan-depth", type=int, default=12,
                      help="Profundidade para varredura inicial")
    parser.add_argument("--multipv", type=int, default=3,
                      help="Número de variações a considerar")

    # Opções de output
    parser.add_argument("--output-dir", type=str, default="puzzles",
                      help="Diretório para salvar os puzzles")
    parser.add_argument("--quiet", action="store_true",
                      help="Reduzir mensagens de log")

    args = parser.parse_args()

    # Configurar logging
    log_level = logging.INFO if args.quiet else logging.DEBUG
    logging.basicConfig(format="%(message)s", level=log_level, stream=sys.stdout)

    # Verificar se o arquivo existe
    if not os.path.exists(args.pgn):
        logging.error(f"Arquivo PGN não encontrado: {args.pgn}")
        return 1

    # Verificar diretório de saída
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Inicializar engine
    engine = AnalysisEngine.initialize(threads=args.threads, memory=args.memory)

    # Processar PGN
    n_puzzles = process_pgn(args.pgn, engine, args)

    logging.info(f"Total de puzzles gerados: {n_puzzles}")
    engine.quit()
    return 0

def process_pgn(pgn_file, engine, args):
    """Processa um arquivo PGN e gera puzzles"""
    import chess.pgn

    n_puzzles = 0
    game_id = 0

    with open(pgn_file) as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            game_id += 1
            logging.info(f"Analisando jogo #{game_id}: {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}")

            # Detectar candidatos
            candidates = find_puzzle_candidates(game, engine, args.scan_depth)
            logging.info(f"Encontrados {len(candidates)} candidatos a puzzles")

            for i, candidate in enumerate(candidates):
                logging.debug(f"Gerando puzzle {i+1}/{len(candidates)}")

                # Gerar puzzle
                puzzle = generate_puzzle(
                    candidate,
                    engine,
                    depth=args.depth,
                    multipv=args.multipv,
                    end_with_player_move=True
                )

                if puzzle and puzzle.is_complete():
                    # Exportar puzzle
                    output_file = os.path.join(
                        args.output_dir,
                        f"puzzle_{game_id}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pgn"
                    )
                    export_puzzle(puzzle, output_file, game.headers)

                    # Mostrar PGN no terminal
                    pgn_text = puzzle.to_pgn(game.headers)
                    print("\n" + pgn_text + "\n")

                    n_puzzles += 1

    return n_puzzles

if __name__ == "__main__":
    sys.exit(main())
