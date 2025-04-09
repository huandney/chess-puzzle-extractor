import json
import os
import time
from src.statistics import PuzzleStatistics

def get_resume_file(input_path, puzzles_dir="puzzles"):
    # Constrói o caminho do arquivo de resume na pasta puzzles/.resume com o nome base do PGN
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    resume_dir = os.path.join(puzzles_dir, ".resume")
    os.makedirs(resume_dir, exist_ok=True)
    return os.path.join(resume_dir, base_name + ".json")

def load_resume(input_path, puzzles_dir="puzzles"):
    # Carrega os dados do arquivo JSON, se existir
    resume_path = get_resume_file(input_path, puzzles_dir)
    if os.path.exists(resume_path):
        with open(resume_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_resume(input_path, resume_data, puzzles_dir="puzzles"):
    # Salva os dados de resume no arquivo JSON
    resume_path = get_resume_file(input_path, puzzles_dir)
    with open(resume_path, "w", encoding="utf-8") as f:
        json.dump(resume_data, f, indent=4, ensure_ascii=False)

def initialize_resume(input_path, puzzles_dir="puzzles", resume_flag=False):
    if not resume_flag:
        resume_data = {
            "skip_games": 0,
            "elapsed_time": 0,
            "stats": {
                "total_games": 0,
                "puzzles_found": 0,
                "puzzles_rejected": 0,
                "objective_stats": {},
                "phase_stats": {},
                "rejection_reasons": {}
            }
        }
        save_resume(input_path, resume_data, puzzles_dir)
        skip_games = 0
        # Criar um novo objeto de estatísticas para uma nova análise
        stats = PuzzleStatistics()
    else:
        resume_data = load_resume(input_path, puzzles_dir)
        skip_games = resume_data.get("skip_games", 0)
        # Usar o método from_resume_data para carregar estatísticas anteriores
        stats = PuzzleStatistics.from_resume_data(resume_data)

    # Retorna os três valores: resume_data, skip_games e stats (estatísticas iniciadas ou carregadas)
    return resume_data, skip_games, stats

def update_resume_data(input_path, game_count, stats, puzzles_dir="puzzles"):
    # Atualiza o resume com os dados atuais de progresso e estatísticas, incluindo tempo decorrido
    resume_data = {
        "skip_games": game_count,
        "elapsed_time": time.time() - stats.start_time,
        "stats": {
            "total_games": stats.total_games,
            "puzzles_found": stats.puzzles_found,
            "puzzles_rejected": stats.puzzles_rejected,
            "objective_stats": dict(stats.objective_stats),
            "phase_stats": dict(stats.phase_stats),
            "rejection_reasons": dict(stats.rejection_reasons)
        }
    }
    save_resume(input_path, resume_data, puzzles_dir)
