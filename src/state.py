"""
state.py - Gerenciamento de estado para retomar análises.
"""
import os
import json

STATE_FILE = "analysis_state.json"

def save_state(last_game_index):
    """
    Salva o estado (índice da última partida processada) em um arquivo.
    """
    state = {"last_game_index": last_game_index}
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Error saving state: {e}")

def load_state():
    """
    Carrega o estado de um arquivo, se existir.
    Retorna o índice da última partida processada, ou None se não encontrado.
    """
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get("last_game_index")
        except Exception as e:
            print(f"Error loading state: {e}")
            return None
    return None
