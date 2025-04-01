import logging
import chess
from collections import namedtuple
from chess.engine import Limit

from src.utils import is_ambiguous

# Estrutura para um movimento analisado
AnalyzedMove = namedtuple('AnalyzedMove', ['move', 'san', 'score'])

class Puzzle:
    """Representa um puzzle de xadrez"""

    def __init__(self, initial_board, initial_move=None):
        self.initial_board = initial_board.copy()
        self.initial_move = initial_move
        self.positions = []  # Lista de posições
        self.category = None  # "Mate", "Material", "Equalize"
        self.player_moves_first = False
        self.final_score = None
        self.initial_score = None

    def is_complete(self):
        """Verifica se o puzzle está completo"""
        # Verificar tamanho mínimo (pelo menos 2 movimentos do jogador)
        player_moves = sum(1 for p in self.positions if p['is_player_move'])
        if player_moves < 2:
            return False

        # Verificar se termina com movimento do jogador
        if self.positions and not self.positions[-1]['is_player_move']:
            return False

        # Verificar categoria
        return self.category is not None

    def to_pgn(self, headers=None):
        """Converte o puzzle para notação PGN"""
        # Implementação da exportação para PGN
        import chess.pgn

        # Criar jogo a partir da posição inicial
        game = chess.pgn.Game()
        game.setup(self.initial_board)
        node = game

        # Adicionar movimentos
        for position in self.positions:
            node = node.add_variation(position['move'])
            if position['evaluation']:
                node.comment = f"Eval: {format_score(position['evaluation'])}"

        # Adicionar headers
        if headers:
            for key, value in headers.items():
                if key != 'FEN' and key != 'SetUp':
                    game.headers[key] = value

        # Adicionar metadados do puzzle
        game.headers['PuzzleCategory'] = self.category or "Unknown"
        if self.player_moves_first:
            game.headers['PuzzlePlayerMovesFirst'] = "1"

        return str(game)

def generate_puzzle(candidate, engine, depth=18, multipv=3, end_with_player_move=True):
    """Gera um puzzle a partir de uma posição candidata"""

    board = candidate['board'].copy()
    initial_move = candidate['move']

    # Criar objeto puzzle
    puzzle = Puzzle(board, initial_move)
    puzzle.initial_score = candidate['prev_score']

    # Determinar quem move primeiro no puzzle
    puzzle.player_moves_first = should_player_move_first(candidate)

    # Fazer o movimento inicial
    if initial_move:
        board.push(initial_move)

    # Alternar entre jogador e oponente
    is_player_move = not puzzle.player_moves_first
    positions = []

    while True:
        # Analisar posição
        analyzed_moves = analyze_position(board, engine, depth, multipv, is_player_move)

        if not analyzed_moves:
            break

        # Verificar se a posição é ambígua
        if is_player_move and is_ambiguous(analyzed_moves):
            logging.debug("Posição ambígua detectada")
            break

        # Selecionar o melhor movimento
        best_move = analyzed_moves[0]

        # Adicionar posição ao puzzle
        positions.append({
            'move': best_move.move,
            'san': best_move.san,
            'evaluation': best_move.score,
            'is_player_move': is_player_move,
            'board': board.copy()
        })

        # Avançar para a próxima posição
        board.push(best_move.move)

        # Verificar se o jogo acabou
        if board.is_game_over():
            break

        # Alternar jogador
        is_player_move = not is_player_move

        # Se queremos terminar com movimento do jogador e não é jogada do jogador
        if end_with_player_move and not is_player_move and len(positions) >= 3:
            # Verificar se já há um resultado claro
            if is_puzzle_resolved(puzzle, positions, board):
                break

    # Definir as posições do puzzle
    puzzle.positions = positions

    # Determinar a categoria do puzzle
    puzzle.category = determine_category(puzzle)

    # Definir avaliação final
    if positions:
        puzzle.final_score = positions[-1]['evaluation']

    return puzzle

def analyze_position(board, engine, depth, multipv, is_player_move):
    """Analisa a posição atual e retorna os melhores movimentos"""
    if board.is_game_over():
        return []

    # Analisar com multipv para jogadas do jogador
    if is_player_move:
        results = engine.analyse(board, Limit(depth=depth), multipv=multipv)
        return [
            AnalyzedMove(
                move=info['pv'][0],
                san=board.san(info['pv'][0]),
                score=info['score'].relative
            )
            for info in results
        ]
    else:
        # Para jogadas do oponente, precisamos apenas do melhor movimento
        info = engine.analyse(board, Limit(depth=depth), multipv=multipv)[0]
        return [
            AnalyzedMove(
                move=info['pv'][0],
                san=board.san(info['pv'][0]),
                score=info['score'].relative
            )
        ]

def should_player_move_first(candidate):
    """Determina se o jogador deve fazer o primeiro movimento no puzzle"""
    # Se a avaliação após o movimento inicial é claramente vantajosa
    # para o jogador, então o jogador deve mover primeiro
    prev_score = candidate['prev_score']
    curr_score = candidate['curr_score']

    # Se é mate após o movimento, o jogador não move primeiro
    if curr_score.is_mate() and curr_score.mate() > 0:
        return False

    # Se a posição era equilibrada e agora é ruim, o oponente blundered
    if not prev_score.is_mate() and abs(prev_score.score()) < 100:
        if curr_score.is_mate() and curr_score.mate() < 0:
            return False
        if not curr_score.is_mate() and curr_score.score() < -250:
            return False

    # Por padrão, o jogador move primeiro (mates, vantagem material)
    return True

def is_puzzle_resolved(puzzle, positions, board):
    """Verifica se o puzzle já tem um resultado claro"""
    if not positions:
        return False

    last_position = positions[-1]

    # Se é xeque-mate
    if board.is_checkmate():
        return True

    # Se é empate
    if board.is_stalemate() or board.is_insufficient_material():
        return True

    # Vantagem material significativa
    if last_position['evaluation'].score() and abs(last_position['evaluation'].score()) > 300:
        # Verificar mudança significativa desde o início
        if puzzle.initial_score and puzzle.initial_score.score():
            change = abs(last_position['evaluation'].score() - puzzle.initial_score.score())
            if change > 200:
                return True

    return False

def determine_category(puzzle):
    """Determina a categoria do puzzle"""
    if not puzzle.positions:
        return None

    final_board = puzzle.positions[-1]['board']
    final_score = puzzle.positions[-1]['evaluation']

    # Mate
    if final_board.is_checkmate():
        return "Mate"

    # Verificar para empate
    if final_board.is_stalemate() or final_board.is_insufficient_material():
        return "Draw"

    # Verificar para vantagem material
    if final_score and puzzle.initial_score:
        if final_score.score() and puzzle.initial_score.score():
            # Ganho significativo de material
            diff = final_score.score() - puzzle.initial_score.score()
            if abs(diff) > 200:
                return "Material"

            # Equilibrando de uma posição ruim
            if puzzle.initial_score.score() < -300 and final_score.score() > -100:
                return "Equalize"

    return None

def format_score(score):
    """Formata a avaliação para exibição"""
    if score.is_mate():
        return f"M{score.mate()}"
    else:
        cp = score.score() / 100.0
        return f"{'+' if cp > 0 else ''}{cp:.2f}"
