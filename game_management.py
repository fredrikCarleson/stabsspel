"""
Game management functions for the Stabsspel application.
This module contains functions for managing game data and operations.
"""

import os
import json
from flask import redirect, url_for
from models import DATA_DIR, save_game_data


def load_game_data(spel_id):
    """
    Load game data from file.

    Args:
        spel_id (str): The ID of the game to load

    Returns:
        dict or None: Game data dictionary if file exists, None otherwise
    """
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if not os.path.exists(filnamn):
        return None
    with open(filnamn, encoding="utf-8") as f:
        return json.load(f)


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
        Flask redirect: Redirects to admin start page
    """
    filnamn = os.path.join(DATA_DIR, f"game_{spel_id}.json")
    if os.path.exists(filnamn):
        os.remove(filnamn)
        return redirect(url_for("admin.admin_start"))
    return redirect(url_for("admin.admin_start"))


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