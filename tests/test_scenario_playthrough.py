"""Four-round playthrough: testdata orders, seeded dice, imported scenario LLM JSON."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.scenario_runner import SCENARIO_SEED, play_scenario

ABSENT_IN_SEVEN = ("SÄPO", "USA", "Säpo")


def _news_blobs(result):
    blobs = []
    for report in result.get("rounds") or []:
        for item in report.get("nyheter") or []:
            blobs.append(f"{item.get('rubrik') or ''} {item.get('upplasning') or ''}")
    return blobs


class TestScenarioPlaythrough(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = play_scenario(seed=SCENARIO_SEED)

    def test_plays_all_four_rounds_and_ends(self):
        self.assertIsNone(self.result["missing_llm_round"])
        self.assertTrue(self.result["finished"])
        self.assertEqual(len(self.result["rounds"]), 4)
        self.assertEqual([item["runda"] for item in self.result["rounds"]], [1, 2, 3, 4])
        for report in self.result["rounds"]:
            self.assertFalse(report.get("stopped"))
            self.assertGreaterEqual(len(report.get("utfall") or []), 1)
            self.assertGreaterEqual(len(report.get("nyheter") or []), 3)
            self.assertLessEqual(len(report.get("nyheter") or []), 6)

    def test_seed_locks_the_first_roll(self):
        self.assertEqual(self.result["rounds"][0]["rolls"]["Alfa-1"], 59)

    def test_replay_is_deterministic(self):
        again = play_scenario(seed=SCENARIO_SEED)
        first_rolls = [report["rolls"] for report in self.result["rounds"]]
        second_rolls = [report["rolls"] for report in again["rounds"]]
        self.assertEqual(first_rolls, second_rolls)
        self.assertEqual(self.result["final_wallets"], again["final_wallets"])

    def test_imported_utfall_reuses_frozen_rolls(self):
        for report in self.result["rounds"]:
            rolls = report["rolls"]
            for item in report.get("utfall") or []:
                self.assertEqual(item["slump"], rolls[item["order_ref"]])
                if item["resultat"] in ("framgång", "delvis framgång"):
                    self.assertLessEqual(item["slump"], item["sannolikhet"])
                else:
                    self.assertGreater(item["slump"], item["sannolikhet"])

    def test_hp_queue_lands_on_the_next_round_wallet(self):
        r1 = self.result["rounds"][0]
        self.assertEqual(r1["pending_hp"]["Alfa"], -3)
        self.assertEqual(r1["pending_hp"]["Bravo"], 4)
        self.assertEqual(r1["wallets_this_round"]["Alfa"], 25)
        self.assertEqual(r1["wallets_next_round"]["Alfa"], 22)
        self.assertEqual(r1["wallets_next_round"]["Bravo"], 29)

    def test_last_round_hp_is_applied_when_the_game_ends(self):
        r4 = self.result["rounds"][3]
        self.assertEqual(r4["pending_hp"]["STT"], 7)
        self.assertEqual(r4["pending_hp"]["Alfa"], -5)
        self.assertEqual(self.result["final_wallets"]["STT"], 37)
        self.assertEqual(self.result["final_wallets"]["Alfa"], 20)
        self.assertEqual(r4["wallets_next_round"]["STT"], 37)
        self.assertEqual(r4["wallets_next_round"]["Alfa"], 20)

    def test_autofill_spends_the_current_wallet(self):
        over = [item for item in self.result["findings"] if item["kind"] == "over_budget"]
        self.assertEqual(over, [])
        r1 = self.result["rounds"][0]
        spent = {}
        for order in r1["orders"]:
            spent[order["lag"]] = spent.get(order["lag"], 0) + int(order["hp"] or 0)
        for team, wallet in r1["wallets_this_round"].items():
            self.assertEqual(spent.get(team, 0), wallet, team)
        r2 = self.result["rounds"][1]
        spent2 = {}
        for order in r2["orders"]:
            spent2[order["lag"]] = spent2.get(order["lag"], 0) + int(order["hp"] or 0)
        self.assertEqual(spent2["Alfa"], r2["wallets_this_round"]["Alfa"])
        self.assertEqual(spent2["Bravo"], r2["wallets_this_round"]["Bravo"])

    def test_backlog_progress_and_recurring_second_attempt(self):
        by_id = {item["id"]: item for item in self.result["final_backlog"]}
        self.assertTrue(by_id["alfa_4"]["done"])
        self.assertEqual(by_id["alfa_4"]["spent"], 20)
        self.assertEqual(by_id["bravo_1_Test"]["spent"], 10)
        self.assertEqual(by_id["stt_6"]["spent"], 10)
        self.assertEqual(by_id["stt_4"]["spent"], 10)
        r4 = self.result["rounds"][3]
        self.assertTrue(
            any(item.get("uppgift") == "stt_4" for item in r4.get("milstolpar") or [])
        )

    def test_projector_and_news_do_not_leak_resolution(self):
        kinds = {item["kind"] for item in self.result["findings"]}
        self.assertNotIn("public_leak", kinds)
        self.assertNotIn("news_leak", kinds)


class TestScenarioPlaythroughSeven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = play_scenario(seed=SCENARIO_SEED, variant="seven")

    def test_roster_is_seven_teams_without_sapo_or_usa(self):
        self.assertEqual(self.result["variant"], "seven")
        self.assertEqual(
            self.result["teams"],
            ["Alfa", "Bravo", "STT", "FM", "BS", "Media", "Regeringen"],
        )
        for name in ABSENT_IN_SEVEN:
            self.assertNotIn(name, self.result["teams"])
            self.assertNotIn(name, self.result["final_wallets"])

    def test_plays_all_four_rounds_and_ends(self):
        self.assertIsNone(self.result["missing_llm_round"])
        self.assertTrue(self.result["finished"])
        self.assertEqual(len(self.result["rounds"]), 4)
        self.assertEqual([item["runda"] for item in self.result["rounds"]], [1, 2, 3, 4])
        for report in self.result["rounds"]:
            self.assertFalse(report.get("stopped"))
            self.assertGreaterEqual(len(report.get("utfall") or []), 1)
            self.assertGreaterEqual(len(report.get("nyheter") or []), 3)
            self.assertLessEqual(len(report.get("nyheter") or []), 6)

    def test_seed_locks_the_first_roll(self):
        self.assertEqual(self.result["rounds"][0]["rolls"]["Alfa-1"], 59)

    def test_round_two_dice_diverge_from_the_nine_team_year(self):
        nine = play_scenario(seed=SCENARIO_SEED, variant="nine")
        self.assertEqual(self.result["rounds"][0]["rolls"]["Alfa-1"], nine["rounds"][0]["rolls"]["Alfa-1"])
        self.assertNotEqual(
            self.result["rounds"][1]["rolls"],
            nine["rounds"][1]["rolls"],
        )

    def test_imported_utfall_reuses_frozen_rolls(self):
        for report in self.result["rounds"]:
            rolls = report["rolls"]
            for item in report.get("utfall") or []:
                self.assertNotIn(item.get("lag"), ABSENT_IN_SEVEN)
                self.assertEqual(item["slump"], rolls[item["order_ref"]])
                if item["resultat"] in ("framgång", "delvis framgång"):
                    self.assertLessEqual(item["slump"], item["sannolikhet"])
                else:
                    self.assertGreater(item["slump"], item["sannolikhet"])

    def test_hp_queue_lands_on_the_next_round_wallet(self):
        r1 = self.result["rounds"][0]
        self.assertEqual(r1["pending_hp"]["Alfa"], -3)
        self.assertEqual(r1["pending_hp"]["Bravo"], 4)
        self.assertEqual(r1["wallets_this_round"]["Alfa"], 25)
        self.assertEqual(r1["wallets_next_round"]["Alfa"], 22)
        self.assertEqual(r1["wallets_next_round"]["Bravo"], 29)

    def test_last_round_hp_is_applied_when_the_game_ends(self):
        r4 = self.result["rounds"][3]
        self.assertEqual(r4["pending_hp"]["STT"], 5)
        self.assertEqual(r4["pending_hp"]["Alfa"], -5)
        self.assertEqual(self.result["final_wallets"]["STT"], 35)
        self.assertEqual(self.result["final_wallets"]["Alfa"], 20)
        self.assertEqual(r4["wallets_next_round"]["STT"], 35)
        self.assertEqual(r4["wallets_next_round"]["Alfa"], 20)

    def test_round_three_retargets_sapo_orders_onto_regeringen(self):
        r3 = self.result["rounds"][2]
        stt3 = next(order for order in r3["orders"] if order["order_ref"] == "STT-3")
        self.assertIn("Regeringen", stt3["aktivitet"])
        self.assertNotIn("SÄPO", stt3["aktivitet"])
        self.assertNotIn("Säpo", stt3["aktivitet"])

    def test_autofill_spends_the_current_wallet(self):
        over = [item for item in self.result["findings"] if item["kind"] == "over_budget"]
        self.assertEqual(over, [])
        r1 = self.result["rounds"][0]
        spent = {}
        for order in r1["orders"]:
            spent[order["lag"]] = spent.get(order["lag"], 0) + int(order["hp"] or 0)
        for team, wallet in r1["wallets_this_round"].items():
            self.assertEqual(spent.get(team, 0), wallet, team)

    def test_projector_and_news_do_not_leak_resolution(self):
        kinds = {item["kind"] for item in self.result["findings"]}
        self.assertNotIn("public_leak", kinds)
        self.assertNotIn("news_leak", kinds)

    def test_news_does_not_name_absent_table_teams(self):
        for blob in _news_blobs(self.result):
            lowered = blob.lower()
            self.assertNotIn("säpo", lowered, blob)
            self.assertNotIn("usa", lowered, blob)


if __name__ == "__main__":
    unittest.main()
