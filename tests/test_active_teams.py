"""active_teams is imported by the team order form at process start."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import active_teams, suggest_teams
from gm_console import (
    _fordelning_items,
    can_submit_orders,
    can_withdraw_orders,
    effective_hp,
    sync_regeringen_fordelning,
    validate_order_hp,
    withdraw_order,
)


class TestActiveTeams(unittest.TestCase):
    def test_uses_persisted_lag(self):
        self.assertEqual(active_teams({"lag": ["Alfa", "Media"]}), ["Alfa", "Media"])

    def test_infers_from_player_count_when_lag_missing(self):
        self.assertEqual(active_teams({"antal_spelare": 20}), suggest_teams(20))
        self.assertEqual(active_teams({}), suggest_teams(20))

    def test_order_form_can_import_gm_console_helpers(self):
        self.assertTrue(callable(sync_regeringen_fordelning))
        self.assertTrue(callable(_fordelning_items))
        self.assertTrue(callable(can_submit_orders))
        self.assertTrue(callable(can_withdraw_orders))
        self.assertTrue(callable(validate_order_hp))
        self.assertTrue(callable(withdraw_order))
        self.assertTrue(callable(effective_hp))

    def test_fordelning_skips_teams_not_in_the_roster(self):
        items = _fordelning_items(
            {"hp_fordelning": [{"lag": "Alfa", "hp": 5}, {"lag": "USA", "hp": 3}]},
            ["Alfa", "Bravo"],
            "Regeringen",
        )
        self.assertEqual(items, [{"lag": "Alfa", "hp": 5}])


if __name__ == "__main__":
    unittest.main()
