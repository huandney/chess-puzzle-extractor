"""
Módulo de visualização responsável por toda a lógica de estilo visual e exibição no console.
Utiliza a biblioteca Rich para formatação de texto, painéis, tabelas, barras de progresso, etc.
O objetivo é manter o código principal mais limpo e modular, centralizando toda a apresentação.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn, SpinnerColumn
from rich.text import Text

# Inicializa o console compartilhado para exibição
console = Console()


def print_stockfish_info(engine_path):
    # Exibe o caminho do Stockfish (usado para exibir qual executável está sendo utilizado)
    console.print(f"[bold blue]Usando Stockfish em:[/] {engine_path}")


def print_resume_info(skip_games):
    # Mensagem de retomada caso a análise seja reiniciada
    console.print(f"[green]Retomando análise a partir do jogo {skip_games}...[/]")


def print_initial_analysis_info(input_path, file_size, total_games, resume=False, skip_games=0, depth=None, depths=None, max_variants=None):
    """
    Exibe informações iniciais sobre o arquivo de entrada e configurações de análise.

    Args:
        input_path (str): Caminho do arquivo PGN de entrada.
        file_size (str): Tamanho do arquivo em formato já formatado (ex.: "125.50 KB" ou "1.23 MB").
        total_games (int): Total de jogos a analisar.
        resume (bool): Indica se a análise será retomada.
        skip_games (int): Número de jogos já processados.
        depth (int): Profundidade definida para análise.
        depths (dict): Dicionário com as diferentes profundidades calculadas.
        max_variants (int): Máximo de variantes alternativas permitidas.
    """
    # Cabeçalho inicial e informações do arquivo de entrada
    console.print("[bold cyan]Iniciando análise tática das partidas...[/]")
    console.print(f"Arquivo de entrada: [magenta]{input_path}[/] ([cyan]{file_size}[/])")
    console.print(f"Total de jogos a analisar: [cyan]{total_games}[/]")
    if resume and skip_games > 0:
        console.print(f"Retomando a partir do jogo: [green]{skip_games}[/] ([cyan]{(skip_games/total_games)*100:.1f}%[/] concluído)")
    if depth is not None and depths is not None:
        console.print(f"Profundidade de análise: {depth} (scan: [bold cyan]{depths['scan']}[/bold cyan], solve: [bold cyan]{depths['solve']}[/bold cyan])")
    if max_variants is not None:
        console.print(f"Variantes máximas permitidas: [cyan]{max_variants}[/]\n")


def create_progress():
    # Configura o objeto Progress para exibir uma barra de progresso detalhada e fluida
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=50, complete_style="green", finished_style="green"),
        TextColumn("[bold]{task.completed}/{task.total}"),
        TextColumn("{task.percentage:>3.1f}%"),
        TimeElapsedColumn(),
        "[cyan]ETA:[/]",
        TimeRemainingColumn(),
        console=console,
        transient=True,            # A barra desaparece ao término
        refresh_per_second=5       # Atualiza 5x por segundo para mais fluidez
    )
    return progress


def print_puzzle_found(progress, puzzles_found, puzzle_game):
    """
    Exibe mensagem e PGN do puzzle encontrado.

    Args:
        progress: Objeto Progress usado para impressão sem interferir na barra.
        puzzles_found (int): Número do puzzle encontrado.
        puzzle_game: Objeto chess.pgn.Game representando o puzzle.
    """
    # Usar progress.print para exibir sem afetar a formatação do PGN
    progress.print(f"[bold yellow]Puzzle #{puzzles_found} Encontrado[/bold yellow]")
    pgn_text = str(puzzle_game)
    parts = pgn_text.split("\n\n", 1)
    if len(parts) == 2:
        progress.print(f"{pgn_text}\n")
    else:
        # Caso não consiga dividir, exibir o texto completo
        progress.print(f"{pgn_text}\n")


def print_verbose_puzzle_generated(progress, message, puzzle_game=None):
    """
    Exibe mensagens em modo verbose, podendo incluir o PGN do puzzle.

    Args:
        progress: Objeto Progress para log.
        message (str): Mensagem de log a ser exibida.
        puzzle_game (opcional): Objeto chess.pgn.Game, se houver PGN para exibir.
    """
    progress.log(message)
    if puzzle_game:
        progress.print(str(puzzle_game) + "\n")


def print_error(message):
    # Mensagem de erro a ser exibida.
    console.print(f"[bold red]{message}[/bold red]")


def print_success(message):
    # Mensagem de sucesso a ser exibida.
    console.print(f"[bold green]{message}[/bold green]")


def print_main_header():
    """
    Exibe o cabeçalho principal do programa.
    """
    console.print("\n[bold blue]♟️  Chess Puzzles Extractor[/bold blue]", justify="center")


def print_configurations(args):
    """
    Exibe as configurações de forma minimalista e elegante.

    Args:
        args: Objeto com os argumentos da linha de comando.
    """
    console.print("[bold cyan]⚙️  Configurações:[/bold cyan]")
    console.print(f"📥 Entrada:         [cyan]{args.input}[/cyan]")
    console.print(f"📤 Saída:           [cyan]{args.output}[/cyan]")
    console.print(f"🔍 Profundidade:    [cyan]{args.depth}[/cyan]")
    console.print(f"🌿 Variantes máx.:  [cyan]{args.max_variants}[/cyan]")
    console.print(f"🗣️  Verbose:         [cyan]{'Sim' if args.verbose else 'Não'}[/cyan]")
    console.print(f"⏯️  Retomar:         [cyan]{'Sim' if args.resume else 'Não'}[/cyan]\n")


def print_end_stats(game_count, puzzles_found, puzzles_rejected):
    """
    Exibe o painel principal com estatísticas da análise.

    Args:
        game_count (int): Número total de jogos analisados.
        puzzles_found (int): Número de puzzles encontrados.
        puzzles_rejected (int): Número de puzzles rejeitados.
    """
    # Painel principal com números centrais em destaque
    stats_panel = Panel(
        f"[bold cyan]Jogos analisados:[/] [white]{game_count}[/]  •  "
        f"[bold green]Puzzles encontrados:[/] [white]{puzzles_found}[/]  •  "
        f"[bold red]Puzzles rejeitados:[/] [white]{puzzles_rejected}[/]",
        title="[bold cyan]Estatísticas da Análise[/]",
        border_style="cyan",
        padding=(1, 2),
        width=80,
        title_align="center"
    )
    console.print(stats_panel)


def print_performance_stats(total_time, average_time_per_game, game_count, puzzles_found):
    """
    Exibe o painel de desempenho com métricas de tempo e taxa de extração.

    Args:
        total_time (float): Tempo total de análise.
        average_time_per_game (float): Tempo médio por jogo.
        game_count (int): Número total de jogos analisados.
        puzzles_found (int): Número de puzzles encontrados.
    """
    # Formatação do tempo
    h, m = divmod(total_time / 60, 60)
    s = total_time % 60
    time_formatted = f"{int(h):02d}h {int(m):02d}m {int(s):02d}s"

    perf_table = Table(box=None, show_header=False, width=76)
    perf_table.add_column("Métrica", style="bold cyan", justify="right", width=40)
    perf_table.add_column("Valor", style="white", justify="left")
    perf_table.add_row("Tempo total de análise:", time_formatted)
    perf_table.add_row("Tempo médio por jogo:", f"{average_time_per_game:.2f}s")
    if game_count > 0:
        success_rate = (puzzles_found / game_count) * 100
        perf_table.add_row("Taxa de extração:", f"{success_rate:.1f}% (puzzles/jogos)")

    perf_panel = Panel(
        perf_table,
        title="[bold blue]Desempenho da Análise[/]",
        border_style="blue",
        padding=(1, 1),
        width=80,
        title_align="center"
    )
    console.print(perf_panel)


def print_rejection_reasons(reason_stats, puzzles_rejected):
    """
    Exibe o painel contendo as razões para rejeição dos puzzles.

    Args:
        reason_stats (dict): Dicionário com os motivos de rejeição e suas contagens.
        puzzles_rejected (int): Número total de puzzles rejeitados.
    """
    if puzzles_rejected > 0:
        # Cria uma tabela para os motivos de rejeição
        reasons_table = Table(box=None, show_header=True, width=76)
        reasons_table.add_column("Motivo", style="bold", justify="left")
        reasons_table.add_column("Quantidade", justify="center")
        reasons_table.add_column("Porcentagem", justify="right")
        # Adiciona linhas à tabela com as cores originais para cada motivo
        for reason, count in reason_stats.items():
            if count > 0:
                percent = (count / puzzles_rejected) * 100
                if "ganho não instrutivo" in reason.lower():
                    row_style = "green"
                elif "múltiplas soluções" in reason.lower():
                    row_style = "magenta"
                elif "sequência muito curta" in reason.lower():
                    row_style = "cyan"
                elif "peça solta" in reason.lower():
                    row_style = "blue"
                elif "apenas capturas" in reason.lower():
                    row_style = "yellow"
                else:
                    row_style = "white"
                reasons_table.add_row(reason.capitalize(), str(count), f"{percent:.1f}%", style=row_style)
        # Painel contendo a tabela de rejeições
        details_panel = Panel(
            reasons_table,
            title="[bold red]Motivos de Rejeição[/]",
            border_style="red",
            padding=(1, 1),
            width=80,
            title_align="center"
        )
        console.print(details_panel)


def print_puzzle_categories(objective_stats, phase_stats, puzzles_found):
    """
    Exibe o painel contendo as categorias de puzzles encontrados, por objetivo e fase do jogo.

    Args:
        objective_stats (dict): Estatísticas dos puzzles por objetivo.
        phase_stats (dict): Estatísticas dos puzzles por fase do jogo.
        puzzles_found (int): Número total de puzzles encontrados.
    """
    if puzzles_found > 0:
        puzzles_stat_table = Table(box=None, show_header=True, width=76)
        puzzles_stat_table.add_column("Categoria", style="bold", justify="left")
        puzzles_stat_table.add_column("Quantidade", justify="center")
        puzzles_stat_table.add_column("Porcentagem", justify="right")

        # Seção para Objetivos
        puzzles_stat_table.add_row("", "", "", style="bold cyan")
        puzzles_stat_table.add_row("[bold]Por Objetivo[/]", "", "")
        for objective, count in sorted(objective_stats.items(), key=lambda x: x[1], reverse=True):
            percent = (count / puzzles_found) * 100
            if objective == "Mate":
                row_style = "red"
            elif objective == "Reversão":
                row_style = "green"
            elif objective == "Equalização":
                row_style = "yellow"
            elif objective == "Defesa":
                row_style = "blue"
            elif objective == "Blunder":
                row_style = "bright_red"
            else:
                row_style = "white"
            puzzles_stat_table.add_row(objective, str(count), f"{percent:.1f}%", style=row_style)

        # Seção para Fases
        puzzles_stat_table.add_row("", "", "", style="bold magenta")
        puzzles_stat_table.add_row("[bold]Por Fase do Jogo[/]", "", "")
        for phase, count in sorted(phase_stats.items(), key=lambda x: x[1], reverse=True):
            percent = (count / puzzles_found) * 100
            if phase == "Abertura":
                row_style = "yellow"
            elif phase == "Meio-jogo":
                row_style = "green"
            elif phase == "Final":
                row_style = "cyan"
            else:
                row_style = "white"
            puzzles_stat_table.add_row(phase, str(count), f"{percent:.1f}%", style=row_style)

        puzzles_panel = Panel(
            puzzles_stat_table,
            title="[bold green]Categorias de Puzzles Encontrados[/]",
            border_style="green",
            padding=(1, 1),
            width=80,
            title_align="center"
        )
        console.print(puzzles_panel)


def print_output_file_info(output_path):
    """
    Exibe a informação do arquivo de saída onde os puzzles foram salvos.

    Args:
        output_path (str): Caminho para o arquivo de saída.
    """
    console.print(f"\n[bold blue]Puzzles salvos em:[/] [magenta]{output_path}[/]")


def render_end_statistics(game_count, puzzles_found, puzzles_rejected, total_time, average_time_per_game, reason_stats, objective_stats, phase_stats, output_path=None):
    """
    Exibe um resumo final da análise, englobando estatísticas gerais, desempenho,
    motivos de rejeição, categorias dos puzzles e informação do arquivo de saída.

    Args:
        game_count (int): Número total de jogos analisados.
        puzzles_found (int): Número de puzzles encontrados.
        puzzles_rejected (int): Número de puzzles rejeitados.
        total_time (float): Tempo total de análise.
        average_time_per_game (float): Tempo médio por jogo.
        reason_stats (dict): Dicionário com os motivos de rejeição e suas contagens.
        objective_stats (dict): Estatísticas dos puzzles por objetivo.
        phase_stats (dict): Estatísticas dos puzzles por fase do jogo.
        output_path (str, optional): Caminho para o arquivo de saída dos puzzles.
    """
    print_end_stats(game_count, puzzles_found, puzzles_rejected)
    print_performance_stats(total_time, average_time_per_game, game_count, puzzles_found)
    if puzzles_rejected > 0:
        print_rejection_reasons(reason_stats, puzzles_rejected)
    if puzzles_found > 0:
        print_puzzle_categories(objective_stats, phase_stats, puzzles_found)
    if output_path:
        print_output_file_info(output_path)
