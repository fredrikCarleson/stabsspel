"""
Game management functions for the Stabsspel application.
This module contains functions for managing game data and operations.
"""

import os
from flask import redirect, url_for
from models import DATA_DIR


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