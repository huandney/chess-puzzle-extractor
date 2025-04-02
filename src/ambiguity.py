"""
ambiguity.py - Verificação de ambiguidade nas soluções dos puzzles.
"""
def check(puzzle, engine, max_ambiguity=0):
    """
    Verifica se um puzzle possui no máximo `max_ambiguity` lances alternativos também vencedores.
    Retorna True se o puzzle for aceitável (ambiguidade dentro do limite), False caso contrário.
    """
    if not puzzle or "fen" not in puzzle:
        return False
    fen = puzzle["fen"]
    engine.set_fen_position(fen)
    try:
        top_moves = engine.get_top_moves(2)
    except Exception:
        return True
    if not top_moves or len(top_moves) < 2:
        # Menos de 2 lances possíveis (ex: posição de xeque-mate), sem ambiguidade
        return True
    best = top_moves[0]
    second = top_moves[1]
    def is_winning(move_info):
        if move_info.get("Mate") is not None:
            # Qualquer valor de mate indica um lance ganhador
            return True
        cp = move_info.get("Centipawn")
        if cp is not None and cp > 100:
            return True
        return False
    best_is_winning = is_winning(best)
    second_is_winning = is_winning(second)
    if not best_is_winning:
        # Se o melhor lance não for vencedor, não é um puzzle válido (não deveria ocorrer aqui).
        return False
    if second_is_winning:
        # Se max_ambiguity == 0, requer solução única -> puzzle ambíguo, retorna False
        if max_ambiguity < 1:
            return False
        # Se permitir uma alternativa (max_ambiguity >= 1), considera aceitável.
    return True
