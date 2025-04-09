"""
Módulo de visualização responsável por toda a lógica de estilo visual e exibição no console.
Utiliza a biblioteca Rich para formatação de texto, painéis, tabelas, barras de progresso, etc.
O objetivo é manter o código principal mais limpo e modular, centralizando toda a apresentação.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.text import Text

# Inicializa o console compartilhado para exibição
console = Console()

# Classe customizada para exibir o tempo decorrido somando um offset de execuções anteriores
class CustomTimeElapsedColumn(TimeElapsedColumn):
    def __init__(self, elapsed_offset=0, **kwargs):
        super().__init__(**kwargs)
        # Offset de tempo acumulado (em segundos)
        self.elapsed_offset = elapsed_offset

    def _format_time(self, seconds):
        # Formata o tempo em h:mm:ss ou m:ss
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:d}:{s:02d}"

    def render(self, task):
        # Calcula o tempo total somando o offset e o tempo atual da task
        total_elapsed = (task.elapsed if task.elapsed is not None else 0) + self.elapsed_offset
        return Text(self._format_time(total_elapsed), style="green")

# Cria e configura a barra de progresso
def create_progress(elapsed_offset=0):
    progress = Progress(
        SpinnerColumn(),  # Ícone de carregamento
        TextColumn("[bold blue]{task.description}"),  # Descrição da tarefa
        BarColumn(bar_width=50, complete_style="green", finished_style="green"),  # Barra de progresso
        TextColumn("[bold]{task.completed}/{task.total}"),  # Texto com contagem
        TextColumn("{task.percentage:>3.1f}%"),  # Percentual de conclusão
        CustomTimeElapsedColumn(elapsed_offset=elapsed_offset),  # Exibição de tempo com offset
        "[cyan]ETA:[/]",  # Rótulo para ETA
        TimeRemainingColumn(),  # Coluna com tempo restante
        console=console,
        transient=True,  # A barra desaparece ao término
        refresh_per_second=5  # Atualização 5 vezes por segundo
    )
    return progress

# Mostra no console o caminho do motor de xadrez
def print_stockfish_info(engine_path):
    console.print(f"[bold blue]Usando Stockfish em:[/] {engine_path}")

# Informa quantos jogos já foram processados na retomada
def print_resume_info(skip_games):
    console.print(f"[green]Retomando análise a partir do jogo {skip_games}...[/]")

# Cabeçalho inicial com detalhes do arquivo e configurações
def print_initial_analysis_info(input_path, file_size, total_games, resume=False, skip_games=0, depth=None, depths=None, max_variants=None):
    console.print("[bold cyan]Iniciando análise tática das partidas...[/]")
    console.print(f"Arquivo de entrada: [magenta]{input_path}[/] ([cyan]{file_size}[/])")
    console.print(f"Total de jogos a analisar: [cyan]{total_games}[/]")
    if resume and skip_games > 0:
        console.print(f"Retomando a partir do jogo: [green]{skip_games}[/] ([cyan]{(skip_games/total_games)*100:.1f}%[/] concluído)")
    if depth is not None and depths is not None:
        console.print(f"Profundidade de análise: {depth} (scan: [bold cyan]{depths['scan']}[/bold cyan], solve: [bold cyan]{depths['solve']}[/bold cyan])")
    if max_variants is not None:
        console.print(f"Variantes máximas permitidas: [cyan]{max_variants}[/]\n")

# Mostra o puzzle encontrado no modo não verbose
def print_puzzle_found(progress, puzzles_found, puzzle_game):
    progress.print(f"[bold yellow]Puzzle #{puzzles_found} Encontrado[/bold yellow]")
    pgn_text = str(puzzle_game)
    parts = pgn_text.split("\n\n", 1)
    if len(parts) == 2:
        progress.print(f"{pgn_text}\n")
    else:
        progress.print(f"{pgn_text}\n")

# Exibe mensagem detalhada em modo verbose
def print_verbose_puzzle_generated(progress, message, puzzle_game=None):
    progress.log(message)
    if puzzle_game:
        progress.print(str(puzzle_game) + "\n")

# Estilo para erro
def print_error(message):
    console.print(f"[bold red]{message}[/bold red]")

# Estilo para sucesso
def print_success(message):
    console.print(f"[bold green]{message}[/bold green]")

# Cabeçalho principal do programa
def print_main_header():
    console.print("\n[bold blue]♟️  Chess Puzzles Extractor[/bold blue]", justify="center")

# Configurações utilizadas
def print_configurations(args):
    console.print("[bold cyan]⚙️  Configurações:[/bold cyan]")
    console.print(f"📥 Entrada:         [cyan]{args.input}[/cyan]")
    console.print(f"📤 Saída:           [cyan]{args.output}[/cyan]")
    console.print(f"🔍 Profundidade:    [cyan]{args.depth}[/cyan]")
    console.print(f"🌿 Variantes máx.:  [cyan]{args.max_variants}[/cyan]")
    console.print(f"🗣️  Verbose:         [cyan]{'Sim' if args.verbose else 'Não'}[/cyan]")
    console.print(f"⏯️  Retomar:         [cyan]{'Sim' if args.resume else 'Não'}[/cyan]\n")

# Renderiza as estatísticas finais da análise
def render_end_statistics(game_count, puzzles_found, puzzles_rejected, total_time, average_time_per_game, rejection_reasons, objective_stats, phase_stats, output_path=None):
    print_end_stats(game_count, puzzles_found, puzzles_rejected)
    print_performance_stats(total_time, average_time_per_game, game_count, puzzles_found)
    if puzzles_rejected > 0:
        print_rejection_reasons(rejection_reasons, puzzles_rejected)
    if puzzles_found > 0:
        print_puzzle_categories(objective_stats, phase_stats, puzzles_found)
    if output_path:
        print_output_file_info(output_path)

# Painel com estatísticas de jogos, puzzles encontrados e rejeitados
def print_end_stats(game_count, puzzles_found, puzzles_rejected):
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

# Painel de desempenho com tempo total, tempo médio e taxa de extração
def print_performance_stats(total_time, average_time_per_game, game_count, puzzles_found):
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

# Painel dos motivos de rejeição
def print_rejection_reasons(rejection_reasons, puzzles_rejected):
    if puzzles_rejected > 0:
        reasons_table = Table(box=None, show_header=True, width=76)
        reasons_table.add_column("Motivo", style="bold", justify="left")
        reasons_table.add_column("Quantidade", justify="center")
        reasons_table.add_column("Porcentagem", justify="right")
        for reason, count in rejection_reasons.items():
            if count > 0:
                percent = (count / puzzles_rejected) * 100
                # Define estilo com base no motivo
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
        details_panel = Panel(
            reasons_table,
            title="[bold red]Motivos de Rejeição[/]",
            border_style="red",
            padding=(1, 1),
            width=80,
            title_align="center"
        )
        console.print(details_panel)

# Painel de estatísticas dos puzzles por categoria (objetivo e fase)
def print_puzzle_categories(objective_stats, phase_stats, puzzles_found):
    if puzzles_found > 0:
        puzzles_stat_table = Table(box=None, show_header=True, width=76)
        puzzles_stat_table.add_column("Categoria", style="bold", justify="left")
        puzzles_stat_table.add_column("Quantidade", justify="center")
        puzzles_stat_table.add_column("Porcentagem", justify="right")
        # Seção por objetivo
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
        # Seção por fase do jogo
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

# Exibe a informação do arquivo de saída
def print_output_file_info(output_path):
    console.print(f"\n[bold blue]Puzzles salvos em:[/] [magenta]{output_path}[/]")
