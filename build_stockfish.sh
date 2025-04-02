#!/bin/bash
# Script para obter o binário Stockfish otimizado para a arquitetura local (sem compilar do código-fonte)
set -e

# Detectar sistema e arquitetura
OS=$(uname -s)
ARCH=$(uname -m)
FILE_NAME=""

if [[ "$OS" == "Linux" ]]; then
    if [[ "$ARCH" == "x86_64" ]]; then
        # Verificar recursos da CPU x86_64
        CPU_FLAGS=$(grep -m1 -o -E 'avx2|bmi2|popcnt' /proc/cpuinfo | tr '\n' ' ')
        if [[ "$CPU_FLAGS" == *"bmi2"* ]]; then
            FILE_NAME="stockfish-ubuntu-x86-64-bmi2.tar"
        elif [[ "$CPU_FLAGS" == *"avx2"* ]]; then
            FILE_NAME="stockfish-ubuntu-x86-64-avx2.tar"
        elif [[ "$CPU_FLAGS" == *"popcnt"* ]]; then
            FILE_NAME="stockfish-ubuntu-x86-64-popcnt.tar"
        else
            FILE_NAME="stockfish-ubuntu-x86-64.tar"
        fi
    elif [[ "$ARCH" == "aarch64" ]]; then
        # ARMv8 (64-bit)
        if grep -q 'asimddp' /proc/cpuinfo; then
            FILE_NAME="stockfish-android-armv8-dotprod.tar"
        else
            FILE_NAME="stockfish-android-armv8.tar"
        fi
    elif [[ "$ARCH" == "armv7l" ]] || [[ "$ARCH" == "armv7" ]]; then
        # ARMv7 (32-bit)
        if grep -q 'neon' /proc/cpuinfo; then
            FILE_NAME="stockfish-android-armv7-neon.tar"
        else
            FILE_NAME="stockfish-android-armv7.tar"
        fi
    else
        echo "Arquitetura $ARCH não suportada por este script."
        exit 1
    fi
elif [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "x86_64" ]]; then
        # macOS em Intel
        FILE_NAME="stockfish-macos-x86-64-avx2.tar"
    elif [[ "$ARCH" == "arm64" ]]; then
        # macOS em Apple Silicon (M1/M2)
        FILE_NAME="stockfish-macos-m1-apple-silicon.tar"
    else
        echo "Arquitetura macOS $ARCH não suportada."
        exit 1
    fi
else
    echo "Sistema operacional $OS não suportado por este script."
    exit 1
fi

# URL de download para o release mais recente do Stockfish
FILE_URL="https://github.com/official-stockfish/Stockfish/releases/latest/download/$FILE_NAME"

echo "Baixando $FILE_NAME..."
if command -v wget > /dev/null; then
    wget -q -O "$FILE_NAME" "$FILE_URL"
elif command -v curl > /dev/null; then
    curl -L -o "$FILE_NAME" "$FILE_URL"
else
    echo "Por favor, instale wget ou curl para realizar o download."
    exit 1
fi

echo "Extraindo binário do Stockfish..."
# Extrair o binário (remover diretório interno 'stockfish/')
tar -xf "$FILE_NAME" --strip-components=1 "stockfish/${FILE_NAME%.tar}"

# Renomear binário para 'stockfish' e garantir permissão de execução
mv "${FILE_NAME%.tar}" stockfish
chmod +x stockfish

# Instalar em /usr/local/bin se tiver permissões, senão instruir usuário
if [[ $(id -u) -eq 0 ]]; then
    install -m 755 stockfish /usr/local/bin/stockfish
    echo "Stockfish instalado em /usr/local/bin/stockfish"
else
    echo "Binário 'stockfish' pronto. Mova-o para um diretório no PATH (ex: /usr/local/bin) para uso geral."
fi

# Limpar arquivo baixado
rm -f "$FILE_NAME"
