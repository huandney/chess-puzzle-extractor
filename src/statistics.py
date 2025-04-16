import time
from collections import defaultdict

class PuzzleStatistics:
    def __init__(self):
        self.start_time = time.time()
        self.total_games = 0
        self.puzzles_found = 0
        self.puzzles_rejected = 0
        self.objective_stats = defaultdict(int)
        self.phase_stats = defaultdict(int)
        self.rejection_reasons = defaultdict(int)

    @classmethod
    def from_resume_data(cls, resume_data):
        """Cria objeto PuzzleStatistics a partir dos dados carregados do resume."""
        obj = cls()
        stats = resume_data.get("stats", {})
        obj.total_games = stats.get("total_games", 0)
        obj.puzzles_found = stats.get("puzzles_found", 0)
        obj.puzzles_rejected = stats.get("puzzles_rejected", 0)
        obj.objective_stats = defaultdict(int, stats.get("objective_stats", {}))
        obj.phase_stats = defaultdict(int, stats.get("phase_stats", {}))
        obj.rejection_reasons = defaultdict(int, stats.get("rejection_reasons", {}))
        elapsed_time = resume_data.get("elapsed_time", 0)
        obj.start_time = time.time() - elapsed_time
        return obj

    def increment_games(self, count=1):
        self.total_games += count

    def add_found(self, count=1):
        self.puzzles_found += count

    def add_rejected(self, reason, count=1):
        self.puzzles_rejected += count
        self.rejection_reasons[reason] += count

    def update_objective(self, objective, count=1):
        self.objective_stats[objective] += count

    def update_phase(self, phase, count=1):
        self.phase_stats[phase] += count

    def get_elapsed_time(self):
        return time.time() - self.start_time

    def get_average_time_per_game(self):
        if self.total_games == 0:
            return 0
        return self.get_elapsed_time() / self.total_games


class AnalysisResult:
    """Encapsula o resultado completo de uma análise de xadrez."""

    def __init__(self, stats, was_interrupted=False):
        # Dados principais
        self.total_games = stats.total_games
        self.puzzles_found = stats.puzzles_found
        self.puzzles_rejected = stats.puzzles_rejected
        self.rejection_reasons = dict(stats.rejection_reasons)

        # Metadados sobre a execução
        self.was_interrupted = was_interrupted
        self.elapsed_time = stats.get_elapsed_time()
        self.avg_time_per_game = stats.get_average_time_per_game()

        # Armazena referência para uso futuro, se necessário
        self.stats = stats

    def successful(self):
        """Verifica se a operação foi completada com sucesso."""
        return not self.was_interrupted

    def display_statistics(self, visual_module, output_path=None):
        """Exibe estatísticas da análise."""
        visual_module.render_end_statistics(
            self.total_games, self.puzzles_found, self.puzzles_rejected,
            self.elapsed_time, self.avg_time_per_game,
            self.rejection_reasons,
            dict(self.stats.objective_stats),
            dict(self.stats.phase_stats),
            None if self.was_interrupted else output_path
        )

        if self.was_interrupted:
            visual_module.print_error("\nInterrompido pelo usuário.")
