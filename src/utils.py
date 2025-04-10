import chess.pgn

def iterate_games(input_path):
    """
    Abre o arquivo PGN especificado e gera, um a um, os jogos contidos nele.

    Args:
        input_path (str): Caminho para o arquivo PGN.

    Yields:
        chess.pgn.Game: Um objeto representando cada partida.

    Raises:
        FileNotFoundError: Se o arquivo não puder ser aberto.
    """
    try:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                yield game
    except FileNotFoundError:
        raise


def count_games(input_path):
    """
    Conta o número de jogos contidos no arquivo PGN.
    Utiliza a função iterate_games para percorrer todas as partidas e retorna a contagem.

    Args:
        input_path (str): Caminho para o arquivo PGN.

    Returns:
        int: Número total de jogos. Se ocorrer algum erro, retorna 1.
    """
    total_game_count = 0
    try:
        for _ in iterate_games(input_path):
            total_game_count += 1
    except Exception:
        total_game_count = 1
    return max(1, total_game_count)


def format_eval(score):
    """
    Formata a pontuação do motor de xadrez para um formato legível.

    Args:
        score: Objeto Score do python-chess, contendo a avaliação

    Returns:
        str: String formatada representando a avaliação (ex: "1.45" ou "M5")
    """
    if score is None:
        return "?"
    try:
        if score.is_mate():
            mate = score.white().mate()
            return f"M{abs(mate)}" if mate else "0"
        cp = score.white().score()
        return f"{cp / 100:.2f}"
    except Exception:
        return "?"
