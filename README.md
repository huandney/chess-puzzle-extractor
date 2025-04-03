# Chess Puzzles Extractor - Gerador de Puzzles de Xadrez

É uma ferramenta que analisa arquivos PGN de partidas de xadrez e gera automaticamente puzzles táticos identificando momentos onde um jogador cometeu um erro (blunder) e há uma série de lances táticos precisos para capitalizar esse erro.

## Características

- Analisa arquivos PGN com múltiplas partidas
- Identifica automaticamente blunders táticos
- Gera puzzles com múltiplas variantes de solução
- Filtra puzzles ambíguos ou pouco instrutivos
- Classifica puzzles por objetivo e fase da partida
- Capacidade de retomar análises interrompidas

## Requisitos

- Python 3.7+
- Stockfish 15+ (instalado ou compilado automaticamente)
- Bibliotecas Python: python-chess, stockfish, tqdm

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/huandney/chess-puzzle-extractor
   cd chess-puzzle-extractor
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

## Uso Básico

```
python main.py arquivo_de_jogos.pgn
```

Este comando analisará todas as partidas no arquivo PGN e gerará puzzles no arquivo `puzzles.pgn`.
> Caso seja a primeira execução o script tentará usar uma instalação existente do Stockfish ou compilará automaticamente uma versão otimizada.

## Opções Avançadas

```
python main.py arquivo_de_jogos.pgn --output puzzles_personalizados.pgn --depth 15 --max-variants 3 --verbose
```

Parâmetros disponíveis:

- `--output`, `-o`: Arquivo de saída para os puzzles (padrão: puzzles.pgn)
- `--depth`, `-d`: Profundidade da análise do motor (padrão: 12)
- `--max-variants`, `-m`: Máximo de variantes alternativas na solução (padrão: 2)
- `--resume`, `-r`: Retomar do último progresso salvo
- `--verbose`, `-v`: Mostrar saída detalhada da análise

## Como Funcionam os Puzzles Gerados

Cada puzzle gerado segue este fluxo:

1. Identifica um blunder no jogo original (mudança significativa na avaliação)
2. Verifica se existe uma sequência tática clara para explorar o erro
3. Gera a linha principal e variantes aceitáveis
4. Categoriza o puzzle por objetivo (mate, reversão, etc.)
5. Adiciona metadados como fase do jogo e dificuldade

## Estrutura do Projeto

- `main.py`: Ponto de entrada do programa
- `build_stockfish.sh`: Script para compilar o Stockfish
- `src/`: Módulos principais
  - `generator.py`: Geração dos puzzles
  - `ambiguity.py`: Detecção de ambiguidade nas soluções
  - `exporter.py`: Exportação dos puzzles para PGN
  - `state.py`: Gerenciamento de estado para retomada

## Exemplos de Saída

Os puzzles gerados incluem headers PGN com informações úteis:

```
[Event "Exemplo de Puzzle"]
[Site "?"]
[Date "2023.05.15"]
[Round "?"]
[White "Jogador A"]
[Black "Jogador B"]
[Result "1-0"]
[SetUp "1"]
[FEN "r1bqkb1r/ppp2ppp/2n5/3np3/2B5/5N2/PPPP1PPP/RNBQ1RK1 w kq - 0 1"]
[Objetivo "Mate"]
[Fase "Meio-jogo"]

1. ....
```

## Contribuindo

Contribuições são bem-vindas! Por favor, sinta-se à vontade para enviar pull requests ou abrir issues para reportar bugs ou sugerir melhorias.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
