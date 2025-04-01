import os
import logging

def export_puzzle(puzzle, output_file, headers=None):
    """Exporta um puzzle para um arquivo PGN"""
    pgn_text = puzzle.to_pgn(headers)

    try:
        with open(output_file, 'w') as f:
            f.write(pgn_text)

        logging.info(f"Puzzle salvo em: {output_file}")
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar puzzle: {e}")
        return False
