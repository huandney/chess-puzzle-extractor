import time
from collections import defaultdict

class PuzzleStatistics:
    def __init__(self):
        self.start_time = time.time()
        self.total_games = 0
        self.puzzles_found = 0
        self.puzzles_rejected = 0
        self.objective_stats = defaultdict(int)  # Contagem por tipo de objetivo
        self.phase_stats = defaultdict(int)      # Contagem por fase de jogo
        self.rejection_reasons = defaultdict(int)  # Armazena rejeições por motivo

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

    def as_dict(self):
        """
        Retorna um dicionário com todas as estatísticas para facilitar
        a integração com módulos de visualização.
        """
        return {
            "total_games": self.total_games,
            "puzzles_found": self.puzzles_found,
            "puzzles_rejected": self.puzzles_rejected,
            "objective_stats": dict(self.objective_stats),
            "phase_stats": dict(self.phase_stats),
            "rejection_reasons": dict(self.rejection_reasons),
            "total_time": self.get_elapsed_time(),
            "average_time_per_game": self.get_average_time_per_game()
        }
