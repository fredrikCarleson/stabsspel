"""Tests for Game Master live-console helpers."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gm_console import (
    add_timer_seconds,
    adjust_hp,
    apply_new_round,
    apply_next_phase,
    apply_previous_phase,
    apply_undo,
    build_inbox,
    build_live_state,
    get_previous_phase,
    missing_order_teams,
    push_undo,
    team_order_status,
    transfer_hp,
)
from models import get_phase_timer


def sample_game():
    return {
        "id": "g1",
        "fas": "Orderfas",
        "runda": 1,
        "lag": ["Alfa", "Bravo", "STT"],
        "poang": {
            "Alfa": {"bas": 25, "aktuell": 25, "regeringsstod": False},
            "Bravo": {"bas": 25, "aktuell": 25, "regeringsstod": False},
            "STT": {"bas": 25, "aktuell": 25, "regeringsstod": False},
        },
        "orderfas_min": 10,
        "diplomatifas_min": 10,
        "resultatfas_min": 10,
        "timer_status": "stopped",
        "timer_elapsed": 0,
        "timer_bonus": 0,
        "fashistorik": [{"runda": 1, "fas": "Orderfas", "status": "pågående"}],
        "team_orders": {},
        "gm_log": [],
        "gm_undo": [],
    }


class TestGmConsole(unittest.TestCase):
    def test_previous_phase_cycle(self):
        self.assertIsNone(get_previous_phase("Orderfas", 1))
        self.assertEqual(get_previous_phase("Diplomatifas", 1), ("Orderfas", 1))
        self.assertEqual(get_previous_phase("Resultatfas", 1), ("Diplomatifas", 1))
        self.assertEqual(get_previous_phase("Orderfas", 2), ("Resultatfas", 1))

    def test_next_phase_does_not_require_orders(self):
        data = sample_game()
        data = apply_next_phase(data)
        self.assertEqual(data["fas"], "Diplomatifas")
        self.assertEqual(data["runda"], 1)

    def test_previous_phase_restores_orderfas(self):
        data = sample_game()
        data = apply_next_phase(data)
        data = apply_previous_phase(data)
        self.assertEqual(data["fas"], "Orderfas")
        self.assertEqual(data["runda"], 1)

    def test_new_round_from_result(self):
        data = sample_game()
        data["fas"] = "Resultatfas"
        data = apply_new_round(data)
        self.assertEqual(data["runda"], 2)
        self.assertEqual(data["fas"], "Orderfas")

    def test_hp_adjust_and_transfer(self):
        data = sample_game()
        adjust_hp(data, "Alfa", -5, "spion")
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 20)
        transfer_hp(data, "Alfa", "Bravo", 5, "regering")
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 15)
        self.assertEqual(data["poang"]["Bravo"]["aktuell"], 30)
        self.assertTrue(data["gm_log"])

    def test_undo_restores_hp(self):
        data = sample_game()
        push_undo(data, "HP")
        adjust_hp(data, "Alfa", 10, "bonus")
        data, label = apply_undo(data)
        self.assertEqual(label, "HP")
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 25)

    def test_missing_and_inbox_conflicts(self):
        data = sample_game()
        self.assertEqual(missing_order_teams(data), ["Alfa", "Bravo", "STT"])
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": {
                    "final": True,
                    "submitted_at": 1,
                    "orders": {
                        "activities": [{
                            "aktivitet": "DDOS",
                            "syfte": "ner",
                            "hp": 8,
                            "typ": "forstora",
                            "paverkar": ["STT"],
                        }]
                    },
                },
                "Bravo": {
                    "final": False,
                    "orders": {
                        "activities": [{
                            "aktivitet": "Hårdning",
                            "syfte": "skydd",
                            "hp": 10,
                            "typ": "bygga",
                            "paverkar": ["STT"],
                        }]
                    },
                },
            }
        }
        self.assertEqual(team_order_status(data, "Alfa"), "submitted")
        self.assertEqual(team_order_status(data, "Bravo"), "draft")
        self.assertEqual(team_order_status(data, "STT"), "empty")
        inbox = build_inbox(data)
        self.assertTrue(any(row["conflict"] for row in inbox))
        state = build_live_state(data)
        self.assertIn("Bravo", state["missing_teams"])
        self.assertIn("STT", state["missing_teams"])
        self.assertNotIn("Alfa", state["missing_teams"])
        self.assertTrue(any(team["team"] == "Alfa" for team in state["backlog"]))
        inbox_row = next(row for row in state["inbox"] if row["team"] == "Alfa")
        self.assertIn("can_apply_backlog", inbox_row)

    def test_add_minutes_does_not_restart_elapsed(self):
        data = sample_game()
        data["timer_elapsed"] = 120
        before = get_phase_timer(data)
        add_timer_seconds(data, 60)
        after = get_phase_timer(data)
        self.assertEqual(after, before + 60)
        self.assertEqual(data["timer_elapsed"], 120)


class TestGmConsoleHtml(unittest.TestCase):
    def test_console_includes_backlog_board_and_live_hooks(self):
        from gm_console_ui import create_gm_console_html, live_html_fragments
        from gm_console import add_backlog_spend, build_live_state

        data = sample_game()
        html = create_gm_console_html("g1", data)
        self.assertIn('id="gm-inbox-root"', html)
        self.assertIn('id="gm-backlog-root"', html)
        self.assertIn("Teamens arbete", html)
        self.assertIn("Inloggning val", html)

        add_backlog_spend(data, "Alfa", "alfa_1", 5)
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": {
                    "final": True,
                    "submitted_at": 1,
                    "orders": {
                        "activities": [{
                            "aktivitet": "Inloggning val",
                            "syfte": "klar",
                            "hp": 5,
                            "typ": "bygga",
                            "paverkar": [],
                            "backlog_selected": "alfa_1",
                        }]
                    },
                }
            }
        }
        fragments = live_html_fragments("g1", build_live_state(data))
        self.assertIn("Lägg +5 HP", fragments["inbox"])
        self.assertIn("5/15", fragments["backlog"])


if __name__ == "__main__":
    unittest.main()
