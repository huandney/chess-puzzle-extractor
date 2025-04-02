#!/bin/bash
# Script para clonar e compilar a versão mais recente do Stockfish
set -e
REPO_URL="https://github.com/official-stockfish/Stockfish.git"
TARGET_DIR="Stockfish"
if [ ! -d "$TARGET_DIR" ]; then
    echo "Clonando o repositório do Stockfish..."
    git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
else
    echo "Repositório Stockfish já existe. Atualizando..."
    cd "$TARGET_DIR" && git pull && cd ..
fi
echo "Compilando o Stockfish..."
cd "$TARGET_DIR/src"
make build ARCH=x86-64
echo "Stockfish compilado com sucesso."
