import argparse
import shutil
import subprocess
import os
from src import generator
from src import config
from src import visual

def ensure_stockfish_available():
    # Verifica se Stockfish está disponível localmente ou instalado no sistema
    if shutil.which("stockfish") is None and not os.path.isfile("./stockfish"):
        visual.console.print("[yellow]Stockfish não encontrado. Baixando binário otimizado...[/yellow]")
        try:
            subprocess.run(["bash", "build_stockfish.sh"], check=True)
            visual.print_success("[bold green]Stockfish instalado com sucesso![/bold green]")
        except subprocess.CalledProcessError as e:
            visual.print_error(f"Erro ao instalar Stockfish: {e}")
            exit(1)
    else:
        visual.print_success("[bold green]Stockfish: Disponível[/bold green]\n")

def main():
    parser = argparse.ArgumentParser(description="Extrair puzzles táticos de partidas de xadrez em PGN")
    parser.add_argument("input", help="Arquivo PGN de entrada com partidas")
    parser.add_argument("--output", "-o", help=f"Arquivo de saída para puzzles (padrão: {config.DEFAULT_OUTPUT})", default=config.DEFAULT_OUTPUT)
    parser.add_argument("--depth", "-d", type=int, help=f"Profundidade da análise do motor (padrão: {config.DEFAULT_DEPTH})", default=config.DEFAULT_DEPTH)
    parser.add_argument("--max-variants", "-m", type=int, help=f"Máximo de variantes alternativas na solução (padrão: {config.DEFAULT_MAX_VARIANTS})", default=config.DEFAULT_MAX_VARIANTS)
    parser.add_argument("--resume", "-r", action="store_true", help="Retomar do último progresso salvo (não reanalisar jogos já processados)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar saída verbosa (detalhes da análise)")
    args = parser.parse_args()

    # Exibe cabeçalho e configurações usando o módulo visual
    visual.print_main_header()
    ensure_stockfish_available()
    visual.print_configurations(args)

    try:
        total_games, puzzles_found, puzzles_rejected, reason_stats = generator.generate_puzzles(
            args.input, args.output, depth=args.depth, max_variants=args.max_variants,
            verbose=args.verbose, resume=args.resume
        )
        visual.print_success("[bold green]Processo concluído com sucesso![/bold green]")
    except FileNotFoundError:
        visual.print_error(f"Erro: O arquivo {args.input} não foi encontrado!")
        exit(1)
    except Exception as e:
        visual.print_error(f"Erro durante a execução: {e}")
        exit(1)

if __name__ == "__main__":
    main()
