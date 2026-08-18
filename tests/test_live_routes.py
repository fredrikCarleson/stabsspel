"""Focused HTTP regressions for auth, order integrity, and mutation locking."""

import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from app import app
from models import create_game_session, game_lock_for
from tests.game_fixtures import activity, create_game_state, order_record


class TestLiveRoutes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.spel_id = "route-test"
        self.token = "alfa-secret-token"
        self.game = create_game_state(
            id=self.spel_id,
            datum="2026-08-18",
            plats="Test",
            antal_spelare=20,
            team_tokens={"Alfa": self.token},
        )
        self.patchers = [
            patch("models.DATA_DIR", self.temp_dir.name),
            patch("admin_routes.DATA_DIR", self.temp_dir.name),
            patch("game_management.DATA_DIR", self.temp_dir.name),
        ]
        for patcher in self.patchers:
            patcher.start()
        app.config.update(TESTING=True, SECRET_KEY="route-test-secret")
        self._write_game(self.game)

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.temp_dir.cleanup()

    def _path(self):
        return os.path.join(self.temp_dir.name, f"game_{self.spel_id}.json")

    def _write_game(self, data):
        with open(self._path(), "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False)

    def _read_game(self):
        with open(self._path(), encoding="utf-8") as handle:
            return json.load(handle)

    def _admin_client(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session[f"game_session_{self.spel_id}"] = create_game_session(self.spel_id)
        return client

    def test_gm_live_state_requires_admin_session(self):
        secret = "hemlig order"
        data = self._read_game()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(name=secret, hp=5)], final=True)
            }
        }
        self._write_game(data)

        response = app.test_client().get(f"/admin/{self.spel_id}/live")

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(secret, response.get_data(as_text=True))

    def test_gm_live_state_is_available_with_admin_session(self):
        response = self._admin_client().get(f"/admin/{self.spel_id}/live")
        self.assertEqual(response.status_code, 200)

    def test_team_cannot_overwrite_an_already_submitted_order(self):
        data = self._read_game()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(name="Original", hp=5, id=1)], final=True)
            }
        }
        self._write_game(data)

        response = app.test_client().post(
            f"/team/{self.spel_id}/{self.token}/submit_order",
            json={"activities": [activity(name="Ersatt", hp=5, id=2)]},
        )

        self.assertEqual(response.status_code, 403)
        saved = self._read_game()["team_orders"]["orders_round_1"]["Alfa"]
        self.assertEqual(saved["orders"]["activities"][0]["aktivitet"], "Original")

    def test_final_submit_rejects_an_empty_order(self):
        response = app.test_client().post(
            f"/team/{self.spel_id}/{self.token}/submit_order",
            json={"activities": []},
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_edit_page_keeps_admin_mode_in_save_urls(self):
        data = self._read_game()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(name="Original", hp=5, id=1)], final=True)
            }
        }
        self._write_game(data)

        response = self._admin_client().get(
            f"/team/{self.spel_id}/{self.token}/enter_order?admin_edit=true"
        )
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("/submit_order", html)
        self.assertIn("/save_order", html)
        self.assertIn("+ '?admin_edit=true'", html)

    def test_admin_can_edit_a_submitted_order(self):
        data = self._read_game()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(name="Original", hp=5, id=1)], final=True)
            }
        }
        self._write_game(data)

        response = self._admin_client().post(
            f"/team/{self.spel_id}/{self.token}/submit_order?admin_edit=true",
            json={"activities": [activity(name="GM ändrade", hp=5, id=1)]},
        )

        self.assertEqual(response.status_code, 200)
        saved = self._read_game()["team_orders"]["orders_round_1"]["Alfa"]
        self.assertTrue(saved["final"])
        self.assertTrue(saved["edited_by_gm"])
        self.assertEqual(saved["orders"]["activities"][0]["aktivitet"], "GM ändrade")

    def test_team_mutation_waits_for_the_per_game_lock(self):
        lock = game_lock_for(self.spel_id)
        started = threading.Event()
        finished = threading.Event()
        result = {}

        def save_draft():
            started.set()
            response = app.test_client().post(
                f"/team/{self.spel_id}/{self.token}/save_order",
                json={"activities": [activity(name="Låst", hp=5, id=1)]},
            )
            result["status"] = response.status_code
            finished.set()

        lock.acquire()
        try:
            thread = threading.Thread(target=save_draft)
            thread.start()
            self.assertTrue(started.wait(1))
            time.sleep(0.05)
            self.assertFalse(finished.is_set())
            self.assertEqual(self._read_game().get("team_orders"), {})
        finally:
            lock.release()

        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result.get("status"), 200)
        self.assertEqual(
            self._read_game()["team_orders"]["orders_round_1"]["Alfa"]
            ["orders"]["activities"][0]["aktivitet"],
            "Låst",
        )

    def test_reset_clears_old_llm_state_and_undo_restores_it(self):
        data = self._read_game()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(name="Gammal", hp=5, id=1)], final=True)
            }
        }
        data["llm_resolution"] = {
            "1": {"rolls": {"Alfa-1": 77}, "result": {"utfall": []}}
        }
        data["llm_forslag"] = {"1": {"nyheter": [{"rubrik": "Gammal"}]}}
        data["timer_bonus"] = 90
        self._write_game(data)
        client = self._admin_client()

        response = client.post(f"/admin/{self.spel_id}/reset")
        self.assertEqual(response.status_code, 302)
        reset = self._read_game()
        self.assertEqual(reset.get("llm_resolution"), {})
        self.assertEqual(reset.get("llm_forslag"), {})
        self.assertEqual(reset.get("timer_bonus"), 0)

        response = client.post(f"/admin/{self.spel_id}/undo")
        self.assertEqual(response.status_code, 302)
        restored = self._read_game()
        self.assertEqual(restored["llm_resolution"]["1"]["rolls"]["Alfa-1"], 77)
        self.assertEqual(restored["llm_forslag"]["1"]["nyheter"][0]["rubrik"], "Gammal")
        self.assertEqual(restored["timer_bonus"], 90)

    def test_repeated_llm_apply_posts_only_change_state_once(self):
        data = self._read_game()
        data["fas"] = "Diplomatifas"
        data["llm_forslag"] = {
            "1": {
                "runda": 1,
                "nyheter": [],
                "utfall": [],
                "warnings": [],
                "hp": [{"lag": "Alfa", "delta": -5, "orsak": "Test"}],
                "milstolpar": [{
                    "lag": "Alfa",
                    "uppgift": "alfa_1",
                    "fas": None,
                    "delta_hp": 5,
                    "orsak": "Test",
                }],
                "hp_applied": False,
                "milestones_applied": False,
            }
        }
        self._write_game(data)
        client = self._admin_client()

        first_hp = client.post(f"/admin/{self.spel_id}/llm_apply", data={"op": "hp"})
        second_hp = client.post(f"/admin/{self.spel_id}/llm_apply", data={"op": "hp"})
        first_mile = client.post(
            f"/admin/{self.spel_id}/llm_apply", data={"op": "milstolpar"}
        )
        second_mile = client.post(
            f"/admin/{self.spel_id}/llm_apply", data={"op": "milstolpar"}
        )

        self.assertEqual(first_hp.status_code, 303)
        self.assertEqual(second_hp.status_code, 303)
        self.assertEqual(first_mile.status_code, 303)
        self.assertEqual(second_mile.status_code, 303)
        self.assertIn("llm_view=hp", first_hp.headers["Location"])
        self.assertIn("#gm-llm-results", first_hp.headers["Location"])
        saved = self._read_game()
        self.assertEqual(saved["poang"]["Alfa"]["aktuell"], 25)
        self.assertEqual(saved["hp_pending"][0]["lag"], "Alfa")
        self.assertEqual(saved["hp_pending"][0]["delta"], -5)
        task = next(item for item in saved["backlog"]["Alfa"] if item["id"] == "alfa_1")
        self.assertEqual(task["spenderade_hp"], 5)
        self.assertTrue(saved["llm_forslag"]["1"]["hp_applied"])
        self.assertTrue(saved["llm_forslag"]["1"]["milestones_applied"])


if __name__ == "__main__":
    unittest.main()
