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

    def render_statistics(self, visual_module, was_interrupted=False, output_path=None):
        """Renderiza todas as estatísticas usando o módulo visual."""
        total_time = self.get_elapsed_time()
        avg_time = self.get_average_time_per_game()

        visual_module.render_end_statistics(
            self.total_games, self.puzzles_found, self.puzzles_rejected,
            total_time, avg_time,
            dict(self.rejection_reasons), dict(self.objective_stats), dict(self.phase_stats),
            None if was_interrupted else output_path
        )

        return total_time, avg_time
