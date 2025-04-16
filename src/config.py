# src/config.py
# Configurações centralizadas para o extrator de puzzles de xadrez

# Configurações padrão para argumentos da linha de comando
DEFAULT_OUTPUT = "puzzles.pgn"     # Arquivo de saída padrão
DEFAULT_DEPTH = 14                # Profundidade padrão para análise
DEFAULT_MAX_VARIANTS = 2           # Número máximo de variantes alternativas

# Para uma varredura ainda mais rápida com soluções muito profundas
SCAN_DEPTH_MULTIPLIER = 1.0        # 50% da profundidade base
SOLVE_DEPTH_MULTIPLIER = 1.2       # 150% da profundidade base

# Limiares para determinar a qualidade/unicidade de puzzles
PUZZLE_UNICITY_THRESHOLD = 200     # Margem mínima para próximo lance pior (1.5 peão)
BLUNDER_THRESHOLD = 150            # Queda mínima na avaliação para detectar um blunder (1.5 peão)
ALT_THRESHOLD = 25                 # Diferença máxima (em cp) para considerar lances equivalentes (0.25 peão)

# Constantes de valor em peões para avaliações
WINNING_ADVANTAGE = 150            # Vantagem considerada decisiva (1.5 peão)
DRAWING_RANGE = 100                # Intervalo para considerar posição como aproximadamente igualada (-1 a +1)

# config.py
DEFAULT_STOCKFISH_PARAMETERS = {
    "Threads": 4,
    "Hash": 1024,
    # outros parâmetros se desejar...
}
