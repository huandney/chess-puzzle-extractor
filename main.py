import argparse
from src import generator
import shutil
import subprocess
import os
from rich.console import Console
from rich.panel import Panel
from src import config

console = Console()

def ensure_stockfish_available():
    if shutil.which("stockfish") is None and not os.path.isfile("./stockfish"):
        console.print("[yellow]Stockfish não encontrado. Baixando binário otimizado...[/yellow]")
        try:
            subprocess.run(["bash", "build_stockfish.sh"], check=True)
            console.print("[bold green]Stockfish instalado com sucesso![/bold green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Erro ao instalar Stockfish: {e}[/red]")
            exit(1)
    else:
        console.print("[bold green]Stockfish: Disponível[/bold green]\n")

def main():
    parser = argparse.ArgumentParser(description="Extrair puzzles táticos de partidas de xadrez em PGN")
    parser.add_argument("input", help="Arquivo PGN de entrada com partidas")
    parser.add_argument("--output", "-o", help=f"Arquivo de saída para puzzles (padrão: {config.DEFAULT_OUTPUT})", default=config.DEFAULT_OUTPUT)
    parser.add_argument("--depth", "-d", type=int, help=f"Profundidade da análise do motor (padrão: {config.DEFAULT_DEPTH})", default=config.DEFAULT_DEPTH)
    parser.add_argument("--max-variants", "-m", type=int, help=f"Máximo de variantes alternativas na solução (padrão: {config.DEFAULT_MAX_VARIANTS})", default=config.DEFAULT_MAX_VARIANTS)
    parser.add_argument("--resume", "-r", action="store_true", help="Retomar do último progresso salvo (não reanalisar jogos já processados)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar saída verbosa (detalhes da análise)")
    args = parser.parse_args()

    # Cabeçalho
    console.print("\n[bold blue]♟️  Chess Puzzles Extractor[/bold blue]", justify="center")

    ensure_stockfish_available()

    # Exibir configurações de forma minimalista e elegante
    console.print("[bold cyan]⚙️  Configurações:[/bold cyan]")
    console.print(f"📥 Entrada:         [cyan]{args.input}[/cyan]")
    console.print(f"📤 Saída:           [cyan]{args.output}[/cyan]")
    console.print(f"🔍 Profundidade:    [cyan]{args.depth}[/cyan]")
    console.print(f"🌿 Variantes máx.:  [cyan]{args.max_variants}[/cyan]")
    console.print(f"🗣️  Verbose:         [cyan]{'Sim' if args.verbose else 'Não'}[/cyan]")
    console.print(f"⏯️  Retomar:         [cyan]{'Sim' if args.resume else 'Não'}[/cyan]\n")

    try:
        total_games, puzzles_found, puzzles_rejected, reason_stats = generator.generate_puzzles(
            args.input, args.output, depth=args.depth, max_variants=args.max_variants,
            verbose=args.verbose, resume=args.resume
        )
        console.print(f"[bold green]Processo concluído com sucesso![/bold green]")
    except FileNotFoundError:
        console.print(f"[bold red]Erro: O arquivo {args.input} não foi encontrado![/bold red]")
        exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro durante a execução: {e}[/bold red]")
        exit(1)

if __name__ == "__main__":
    main()
