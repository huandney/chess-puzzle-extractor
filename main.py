#!/usr/bin/env python3
"""
Script principal do projeto chess-puzzle-extractor.
Faz o parsing de argumentos e coordena a análise de partidas e geração de puzzles.
"""
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from src import analysis, detector, generator, exporter, ambiguity, state, utils

def process_game(game, depth, threads, memory, include_blunder, max_ambiguity):
    """
    Analisa uma única partida para encontrar puzzles.
    Retorna uma lista de puzzles encontrados na partida.
    """
    engine = analysis.create_engine(depth=depth, threads=threads, memory=memory)
    puzzles = []
    try:
        candidatos = detector.find_candidates(game, engine, include_blunder=include_blunder)
        for candidato in candidatos:
            puzzle = generator.generate_puzzle(game, candidato, engine)
            if puzzle:
                # Verifica ambiguidade (se o puzzle tem solução única dentro do limite)
                if ambiguity.check(puzzle, engine, max_ambiguity=max_ambiguity):
                    puzzles.append(puzzle)
                else:
                    # Se puzzle ambíguo (mais soluções do que o permitido), ignora
                    pass
    finally:
        analysis.close_engine(engine)
    return puzzles

def main():
    parser = argparse.ArgumentParser(description="Chess Puzzle Extractor - extrai puzzles táticos de partidas de xadrez.")
    parser.add_argument("--depth", type=int, default=15, help="Profundidade de busca para análise do Stockfish.")
    parser.add_argument("--threads", type=int, default=2, help="Número de threads do motor de análise.")
    parser.add_argument("--memory", type=int, default=256, help="Memória de hash (MB) para o motor.")
    parser.add_argument("--quiet", action="store_true", help="Executar sem mostrar progresso ou saída detalhada.")
    parser.add_argument("--include-blunder", action="store_true", help="Incluir puzzles originados por erros graves (blunders).")
    parser.add_argument("--pgn", type=str, required=True, help="Caminho do arquivo PGN de entrada (ou diretório de PGNs).")
    parser.add_argument("--resume", action="store_true", help="Retomar do último estado de análise salvo.")
    parser.add_argument("--max-ambiguity", type=int, default=0, help="Número máximo de lances alternativos vencedores permitidos (0 para solução única).")
    args = parser.parse_args()

    output_dir = os.path.join(os.getcwd(), "puzzles")
    os.makedirs(output_dir, exist_ok=True)

    last_processed = None
    if args.resume:
        last_processed = state.load_state()
        if last_processed is not None and not args.quiet:
            print(f"Retomando a partir da partida de índice {last_processed+1}")

    games = []
    if os.path.isdir(args.pgn):
        for filename in os.listdir(args.pgn):
            if filename.lower().endswith(".pgn"):
                file_path = os.path.join(args.pgn, filename)
                games.extend(utils.load_pgn(file_path))
    else:
        games = utils.load_pgn(args.pgn)
    if not games:
        print("Nenhuma partida encontrada para analisar.")
        sys.exit(0)

    puzzles_todos = []
    game_iter = games
    if not args.quiet:
        try:
            from tqdm import tqdm
            game_iter = tqdm(games, desc="Analyzing games", unit="game")
        except ImportError:
            pass
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for idx, game in enumerate(games):
            if last_processed is not None and idx <= last_processed:
                continue
            futures.append(executor.submit(process_game, game, args.depth, args.threads, args.memory, args.include_blunder, args.max_ambiguity))
        for future in as_completed(futures):
            game_puzzles = future.result()
            puzzles_todos.extend(game_puzzles)
            if not args.quiet:
                try:
                    game_iter.update(1)
                except Exception:
                    pass
    if not args.quiet:
        try:
            game_iter.close()
        except Exception:
            pass

    state.save_state(len(games)-1)
    if puzzles_todos:
        output_file = os.path.join(output_dir, "puzzles.pgn")
        exporter.export_puzzles(puzzles_todos, output_file)
        if not args.quiet:
            print(f"{len(puzzles_todos)} puzzles gerados. Verifique o arquivo {output_file}")
    else:
        if not args.quiet:
            print("Nenhum puzzle foi gerado.")

if __name__ == "__main__":
    main()
