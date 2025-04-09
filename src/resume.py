import json
import os
import time

def get_resume_file(input_path, puzzles_dir="puzzles"):
    """
    Constrói o caminho do arquivo de resume baseado no input_path e na pasta de puzzles.
    O arquivo de resume ficará em puzzles/.resume/<base_name>.json,
    onde base_name é o nome do arquivo PGN.

    Args:
        input_path (str): Caminho para o arquivo PGN.
        puzzles_dir (str): Diretório onde os puzzles (e o resume) serão armazenados.

    Returns:
        str: O caminho completo para o arquivo de resume.
    """
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    resume_dir = os.path.join(puzzles_dir, ".resume")
    if not os.path.exists(resume_dir):
        os.makedirs(resume_dir)
    return os.path.join(resume_dir, base_name + ".json")

def load_resume(input_path, puzzles_dir="puzzles"):
    """
    Carrega os dados de resume a partir do arquivo JSON na pasta puzzles/.resume.

    Args:
        input_path (str): Caminho para o arquivo PGN.
        puzzles_dir (str): Diretório onde os puzzles (e o resume) são armazenados.

    Returns:
        dict: Dados de progresso e estatísticas salvos previamente. Se não existir ou houver erro, retorna {}.
    """
    resume_path = get_resume_file(input_path, puzzles_dir)
    if os.path.exists(resume_path):
        try:
            with open(resume_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError:
            return {}
    return {}

def save_resume(input_path, resume_data, puzzles_dir="puzzles"):
    """
    Salva os dados de resume (progresso, estatísticas e tempo decorrido) em um arquivo JSON na pasta puzzles/.resume.

    Args:
        input_path (str): Caminho para o arquivo PGN.
        resume_data (dict): Dicionário contendo o progresso e as estatísticas.
        puzzles_dir (str): Diretório onde os puzzles (e o resume) são armazenados.
    """
    resume_path = get_resume_file(input_path, puzzles_dir)
    with open(resume_path, "w", encoding="utf-8") as f:
        json.dump(resume_data, f, indent=4)

def update_resume_data(input_path, game_count, stats, puzzles_dir="puzzles"):
    """
    Atualiza os dados do resume com os dados atuais de progresso, estatísticas e tempo decorrido,
    e salva em um arquivo JSON.

    Args:
        input_path (str): Caminho para o arquivo PGN.
        game_count (int): Número de jogos processados.
        stats: Objeto de estatísticas (ex.: PuzzleStatistics) com os contadores atualizados.
        puzzles_dir (str): Diretório onde os puzzles (e o resume) são armazenados.
    """
    resume_data = load_resume(input_path, puzzles_dir)
    resume_data["skip_games"] = game_count
    resume_data["stats"] = {
         "total_games": stats.total_games,
         "puzzles_found": stats.puzzles_found,
         "puzzles_rejected": stats.puzzles_rejected,
         "objective_stats": dict(stats.objective_stats),
         "phase_stats": dict(stats.phase_stats),
         "rejection_reasons": dict(stats.rejection_reasons)
    }
    resume_data["elapsed_time"] = time.time() - stats.start_time
    save_resume(input_path, resume_data, puzzles_dir)
