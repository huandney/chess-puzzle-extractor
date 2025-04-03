#!/bin/bash
# Script para clonar e compilar a versão mais recente do Stockfish
set -e

REPO_URL="https://github.com/official-stockfish/Stockfish.git"
TARGET_DIR="Stockfish"
BIN_NAME="stockfish"

ROOT_DIR="$(pwd)"  # <- raiz do projeto (onde está o script)

if [ ! -d "$TARGET_DIR" ]; then
    echo "Clonando o repositório do Stockfish..."
    git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
else
    echo "Repositório Stockfish já existe. Atualizando..."
    cd "$TARGET_DIR" && git pull && cd "$ROOT_DIR"
fi

echo "🔧 Compilando Stockfish (isso pode levar alguns segundos)..."
cd "$TARGET_DIR/src"
make build ARCH=x86-64 > /dev/null  # Oculta stdout, mas mostra stderr
echo "Compilação concluída."

echo "Movendo o binário compilado para a raiz do projeto..."
cp stockfish "$ROOT_DIR/$BIN_NAME"
chmod +x "$ROOT_DIR/$BIN_NAME"

cd "$ROOT_DIR"
echo "Removendo diretório de compilação..."
rm -rf "$TARGET_DIR"

echo "✔️ Stockfish pronto em $ROOT_DIR/$BIN_NAME"
