"""active_teams is imported by the team order form at process start."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import active_teams, suggest_teams


class TestActiveTeams(unittest.TestCase):
    def test_uses_persisted_lag(self):
        self.assertEqual(active_teams({"lag": ["Alfa", "Media"]}), ["Alfa", "Media"])

    def test_infers_from_player_count_when_lag_missing(self):
        self.assertEqual(active_teams({"antal_spelare": 20}), suggest_teams(20))
        self.assertEqual(active_teams({}), suggest_teams(20))


if __name__ == "__main__":
    unittest.main()
