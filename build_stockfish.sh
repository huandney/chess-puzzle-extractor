#!/bin/bash

echo "- Obtendo Stockfish mais recente..."

if [ -d Stockfish/src ]; then
    cd Stockfish/src
    make clean > /dev/null
    git pull
else
    git clone --depth 1 https://github.com/official-stockfish/Stockfish.git
    cd Stockfish/src
fi

echo "- Determinando arquitetura da CPU..."

ARCH=x86-64
EXE=stockfish-x86_64

if [ -f /proc/cpuinfo ]; then
    if grep "^flags" /proc/cpuinfo | grep -q popcnt ; then
        ARCH=x86-64-modern
        EXE=stockfish-x86_64-modern
    fi

    if grep "^flags" /proc/cpuinfo | grep bmi2 | grep -q popcnt ; then
        ARCH=x86-64-bmi2
        EXE=stockfish-x86_64-bmi2
    fi
else
    # Verificar Apple Silicon
    arch_name="$(uname -m)"
    if [ "${arch_name}" = "arm64" ]; then
        echo "Executando em ARM"
        ARCH=apple-silicon
        EXE=stockfish-arm64
    fi
fi

echo "- Compilando $EXE... (seja paciente)"
make profile-build ARCH=$ARCH EXE=../../$EXE > /dev/null

cd ../..
echo "- Concluído! Stockfish disponível em: ./$EXE"
