import chess.pgn

def export_puzzle(puzzle_game, output_file_handle):
    """
    Escreve o puzzle (objeto chess.pgn.Game) no arquivo especificado.
    """
    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=False)
    pgn_text = puzzle_game.accept(exporter)
    output_file_handle.write(pgn_text + "\n\n")
    output_file_handle.flush()
