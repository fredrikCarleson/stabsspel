"""
Game management functions for the Stabsspel application.
This module contains functions for managing game data and operations.
"""

import os
import json
from models import DATA_DIR, save_game_data, load_game_data, game_lock_for


def save_checkbox_state(spel_id, checkbox_id, checked):
    """
    Save checkbox state to game data.

    Args:
        spel_id (str): The ID of the game
        checkbox_id (str): The ID of the checkbox
        checked (bool): Whether the checkbox is checked
    """
    data = load_game_data(spel_id)
    if not data:
        return
    
    if "checkbox_states" not in data:
        data["checkbox_states"] = {}
    
    data["checkbox_states"][checkbox_id] = checked
    save_game_data(spel_id, data)


def get_checkbox_state(data, checkbox_id):
    """
    Get checkbox state from game data.

    Args:
        data (dict): Game data dictionary
        checkbox_id (str): The ID of the checkbox

    Returns:
        bool: True if checkbox is checked, False otherwise
    """
    if "checkbox_states" not in data:
        return False
    return data["checkbox_states"].get(checkbox_id, False)


def delete_game(spel_id):
    """
    Delete a game file from the data directory.

    Args:
        spel_id (str): The ID of the game to delete

    Returns:
        bool: True if a file was removed, False if it was already missing
    """
    try:
        filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
        removed = False
        with game_lock_for(spel_id):
            for path in (filnamn, filnamn + ".backup"):
                if os.path.exists(path):
                    os.remove(path)
                    removed = True
        if removed:
            print(f"Successfully deleted game files for: {spel_id}")
        else:
            print(f"Game file not found: {filnamn}")
        return removed
    except Exception as e:
        print(f"Error deleting game {spel_id}: {e}")
        raise


def nollstall_regeringsstod(data):
    """
    Reset all team government support (regeringsstöd) to False.

    Args:
        data (dict): Game data dictionary

    Returns:
        dict: Modified game data with all regeringsstod set to False
    """
    if "poang" in data:
        for lag in data["poang"]:
            data["poang"][lag]["regeringsstod"] = False
    return data
