"""
High-value domain tests for Stabsspel.

These protect game-state rules that would silently corrupt a live event:
phases, HP, order budgets, undo, timers, and roster size.
They do not render the GUI.
"""
import time
import json
import tempfile
import unittest
from datetime import datetime as real_datetime
from unittest.mock import patch
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gm_console import (
    UNDO_LIMIT,
    add_backlog_spend,
    adjust_hp,
    append_gm_log,
    apply_activity_hp_to_backlog,
    apply_llm_hp,
    apply_llm_milestones,
    apply_new_round,
    apply_next_phase,
    apply_previous_phase,
    apply_undo,
    build_inbox,
    build_live_state,
    build_llm_export_text,
    build_public_state,
    build_team_strip,
    can_submit_orders,
    current_order_refs,
    effective_hp,
    end_game,
    ensure_round_rolls,
    format_json_error,
    get_llm_forslag,
    get_round_rolls,
    get_round_utfall,
    hp_delta_from_fields,
    import_llm_forslag,
    LlmJsonSyntaxError,
    make_order_ref,
    missing_order_teams,
    parse_llm_forslag,
    parse_positive_amount,
    push_undo,
    set_regeringsstod,
    spent_hp_for_team,
    team_order_status,
    transfer_hp,
    update_activity,
    validate_order_hp,
    withdraw_order,
)
from models import (
    MAX_RUNDA,
    SESSION_TIMEOUT_SECONDS,
    create_game_session,
    encrypt_password,
    get_next_fas,
    get_phase_timer,
    get_team_base_hp,
    is_declaration_period,
    is_game_session_valid,
    is_large_game,
    refresh_game_session,
    skapa_nytt_spel,
    suggest_teams,
    verify_password,
)
from tests.game_fixtures import activity, create_game_state, order_record


class TestPhaseMachine(unittest.TestCase):
    def test_full_round_advances_order_diplomacy_result_then_next_round(self):
        data = create_game_state()
        data = apply_next_phase(data)
        self.assertEqual(data["fas"], "Diplomatifas")
        self.assertEqual(data["runda"], 1)
        data = apply_next_phase(data)
        self.assertEqual(data["fas"], "Resultatfas")
        self.assertEqual(data["runda"], 1)
        data = apply_new_round(data)
        self.assertEqual(data["fas"], "Orderfas")
        self.assertEqual(data["runda"], 2)

    def test_refuses_to_advance_from_result_with_next_phase(self):
        data = create_game_state(fas="Resultatfas")
        with self.assertRaises(ValueError):
            apply_next_phase(data)

    def test_ended_game_does_not_accept_orders_even_in_order_phase(self):
        self.assertFalse(can_submit_orders(create_game_state(avslutat=True)))

    def test_empty_draft_is_not_auto_submitted_on_phase_change(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([], final=False),
            }
        }
        apply_next_phase(data)
        self.assertFalse(data["team_orders"]["orders_round_1"]["Alfa"].get("final"))
        self.assertIn("Alfa", missing_order_teams(data))

    def test_refuses_a_fifth_round(self):
        data = create_game_state(fas="Resultatfas", runda=MAX_RUNDA)
        with self.assertRaises(ValueError):
            apply_new_round(data)

    def test_cannot_go_back_before_round_one_order(self):
        data = create_game_state()
        with self.assertRaises(ValueError):
            apply_previous_phase(data)

    def test_going_back_from_round_two_order_returns_to_round_one_result(self):
        data = create_game_state(fas="Orderfas", runda=2)
        data = apply_previous_phase(data)
        self.assertEqual(data["fas"], "Resultatfas")
        self.assertEqual(data["runda"], 1)

    def test_last_round_result_does_not_open_round_five(self):
        self.assertEqual(get_next_fas("Resultatfas", 4), "Resultatfas")

    def test_unknown_phase_restarts_at_order(self):
        self.assertEqual(get_next_fas("InteEnFas", 1), "Orderfas")

    def test_ending_the_game_marks_it_finished_and_stops_the_timer(self):
        data = create_game_state(fas="Resultatfas", runda=4, timer_status="running")
        data = end_game(data)
        self.assertTrue(data["avslutat"])
        self.assertEqual(data["timer_status"], "stopped")
        self.assertEqual(data["timer_elapsed"], 0)


class TestActionPoints(unittest.TestCase):
    def test_effective_hp_adds_government_support_without_changing_aktuell(self):
        entry = {"aktuell": 25, "regeringsstod": True}
        self.assertEqual(effective_hp(entry), 35)
        self.assertEqual(entry["aktuell"], 25)

    def test_removing_points_clamps_at_zero(self):
        data = create_game_state()
        adjust_hp(data, "Alfa", -100, "straff")
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 0)

    def test_adding_points_increases_aktuell(self):
        data = create_game_state()
        adjust_hp(data, "Alfa", 5, "bonus")
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 30)

    def test_hp_delta_from_fields_accepts_any_integer(self):
        self.assertEqual(hp_delta_from_fields("plus5"), 5)
        self.assertEqual(hp_delta_from_fields("minus5"), -5)
        self.assertEqual(hp_delta_from_fields("adjust", 7, "minus"), -7)
        self.assertEqual(hp_delta_from_fields("adjust", 3, "plus"), 3)
        self.assertEqual(hp_delta_from_fields("adjust", -8), -8)
        self.assertEqual(hp_delta_from_fields("adjust", "", "minus"), -1)
        self.assertIsNone(hp_delta_from_fields("transfer", 5))
        with self.assertRaises(ValueError):
            hp_delta_from_fields("adjust", 0)
        self.assertEqual(parse_positive_amount(""), 1)
        self.assertEqual(parse_positive_amount("4"), 4)

    def test_transfer_moves_points_between_teams(self):
        data = create_game_state()
        transfer_hp(data, "Alfa", "Bravo", 5, "spion")
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 20)
        self.assertEqual(data["poang"]["Bravo"]["aktuell"], 30)

    def test_transfer_rejects_more_than_the_sender_has(self):
        data = create_game_state()
        with self.assertRaises(ValueError):
            transfer_hp(data, "Alfa", "Bravo", 26, "för mycket")
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 25)
        self.assertEqual(data["poang"]["Bravo"]["aktuell"], 25)

    def test_transfer_rejects_zero_negative_and_same_team(self):
        data = create_game_state()
        with self.assertRaises(ValueError):
            transfer_hp(data, "Alfa", "Bravo", 0)
        with self.assertRaises(ValueError):
            transfer_hp(data, "Alfa", "Bravo", -5)
        with self.assertRaises(ValueError):
            transfer_hp(data, "Alfa", "Alfa", 5)

    def test_transfer_cannot_move_government_support_bonus(self):
        data = create_game_state()
        set_regeringsstod(data, "Alfa", True)
        self.assertEqual(effective_hp(data["poang"]["Alfa"]), 35)
        with self.assertRaises(ValueError) as ctx:
            transfer_hp(data, "Alfa", "Bravo", 30, "stöd")
        self.assertIn("överförbar", str(ctx.exception))
        self.assertIn("kan inte flyttas", str(ctx.exception))
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 25)

    def test_unknown_team_cannot_receive_points(self):
        data = create_game_state()
        with self.assertRaises(ValueError):
            adjust_hp(data, "Media", 5)

    def test_new_round_clears_government_support(self):
        data = create_game_state(fas="Resultatfas")
        set_regeringsstod(data, "Alfa", True)
        self.assertTrue(data["poang"]["Alfa"]["regeringsstod"])
        data = apply_new_round(data)
        self.assertFalse(data["poang"]["Alfa"]["regeringsstod"])
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 25)


class TestOrderBudgets(unittest.TestCase):
    def test_accepts_spending_exactly_available_hp(self):
        data = create_game_state()
        result = validate_order_hp(data, "Alfa", {"activities": [activity(hp=25)]})
        self.assertTrue(result["valid"])
        self.assertEqual(result["used_hp"], 25)

    def test_rejects_spending_one_point_over_budget(self):
        data = create_game_state()
        result = validate_order_hp(data, "Alfa", {"activities": [activity(hp=26)]})
        self.assertFalse(result["valid"])

    def test_sums_multiple_activities_against_the_budget(self):
        data = create_game_state()
        result = validate_order_hp(
            data,
            "Alfa",
            {"activities": [activity(name="A", hp=10), activity(name="B", hp=16)]},
        )
        self.assertFalse(result["valid"])

    def test_government_support_raises_the_order_budget_by_ten(self):
        data = create_game_state()
        data["poang"]["Alfa"]["regeringsstod"] = True
        result = validate_order_hp(data, "Alfa", {"activities": [activity(hp=35)]})
        self.assertTrue(result["valid"])
        self.assertEqual(result["max_hp"], 35)

    def test_rejects_negative_and_malformed_hp(self):
        data = create_game_state()
        self.assertFalse(validate_order_hp(data, "Alfa", {"activities": [activity(hp=-1)]})["valid"])
        self.assertFalse(
            validate_order_hp(data, "Alfa", {"activities": [{"hp": "tio"}]})["valid"]
        )

    def test_orders_cannot_be_submitted_during_result_phase(self):
        self.assertTrue(can_submit_orders(create_game_state(fas="Orderfas")))
        self.assertTrue(can_submit_orders(create_game_state(fas="Diplomatifas")))
        self.assertFalse(can_submit_orders(create_game_state(fas="Resultatfas")))

    def test_advancing_phase_auto_submits_drafts_but_leaves_empty_teams_empty(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(hp=10)], final=False),
            }
        }
        data = apply_next_phase(data)
        alfa = data["team_orders"]["orders_round_1"]["Alfa"]
        self.assertTrue(alfa["final"])
        self.assertTrue(alfa["auto_submitted"])
        self.assertEqual(team_order_status(data, "STT"), "empty")
        self.assertIn("STT", missing_order_teams(data))
        self.assertNotIn("Alfa", missing_order_teams(data))

    def test_inbox_only_shows_the_current_round(self):
        data = create_game_state(runda=2, fas="Orderfas")
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(name="Gammal", hp=5)], final=True),
            },
            "orders_round_2": {
                "Alfa": order_record([activity(name="Ny", hp=8)], final=True),
            },
        }
        names = [row["aktivitet"] for row in build_inbox(data)]
        self.assertEqual(names, ["Ny"])

    def test_gm_edit_after_submit_is_marked_changed(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record(
                    [activity(hp=10)],
                    final=True,
                    submitted_at=1,
                    updated_at=10,
                    edited_by_gm=True,
                )
            }
        }
        self.assertEqual(team_order_status(data, "Alfa"), "changed")

    def test_spent_hp_counts_current_round_activities(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record(
                    [activity(name="A", hp=10), activity(name="B", hp=5)],
                    final=True,
                )
            }
        }
        self.assertEqual(spent_hp_for_team(data, "Alfa"), 15)
        strip = {row["team"]: row for row in build_team_strip(data)}
        self.assertEqual(strip["Alfa"]["remaining"], 10)


class TestTimer(unittest.TestCase):
    def test_stopped_timer_subtracts_elapsed_from_phase_length(self):
        data = create_game_state(timer_elapsed=120)
        self.assertEqual(get_phase_timer(data), 480)

    def test_result_phase_uses_its_own_duration(self):
        data = create_game_state(fas="Resultatfas", resultatfas_min=10, timer_elapsed=0)
        self.assertEqual(get_phase_timer(data), 600)

    def test_bonus_minutes_do_not_clear_elapsed(self):
        data = create_game_state(timer_elapsed=120)
        from gm_console import add_timer_seconds
        add_timer_seconds(data, 60)
        self.assertEqual(data["timer_elapsed"], 120)
        self.assertEqual(get_phase_timer(data), 540)

    def test_remaining_time_never_goes_negative(self):
        data = create_game_state(timer_elapsed=9999)
        self.assertEqual(get_phase_timer(data), 0)

    def test_running_timer_uses_wall_clock_from_start(self):
        data = create_game_state(
            timer_status="running",
            timer_start=1000,
            timer_elapsed=0,
        )
        with patch("models.time.time", return_value=1060):
            self.assertEqual(get_phase_timer(data), 540)


class TestUndo(unittest.TestCase):
    def test_undo_with_empty_stack_leaves_state_alone(self):
        data = create_game_state()
        restored, label = apply_undo(data)
        self.assertIsNone(label)
        self.assertEqual(restored["poang"]["Alfa"]["aktuell"], 25)

    def test_undo_after_phase_change_restores_round_and_phase(self):
        data = create_game_state()
        push_undo(data, "Nästa fas")
        data = apply_next_phase(data)
        data, label = apply_undo(data)
        self.assertEqual(label, "Nästa fas")
        self.assertEqual(data["fas"], "Orderfas")
        self.assertEqual(data["runda"], 1)

    def test_undo_stack_is_capped(self):
        data = create_game_state()
        for i in range(UNDO_LIMIT + 5):
            push_undo(data, f"step {i}")
        self.assertEqual(len(data["gm_undo"]), UNDO_LIMIT)


class TestRosterAndCalendar(unittest.TestCase):
    def test_small_games_have_five_teams_large_games_have_nine(self):
        self.assertEqual(len(suggest_teams(20)), 5)
        self.assertEqual(len(suggest_teams(27)), 9)
        self.assertFalse(is_large_game({"lag": suggest_teams(20)}))
        self.assertTrue(is_large_game({"lag": suggest_teams(27)}))

    def test_stt_base_hp_increases_in_a_large_game(self):
        small = {"lag": suggest_teams(20)}
        large = {"lag": suggest_teams(27)}
        self.assertEqual(get_team_base_hp("STT", small), 25)
        self.assertEqual(get_team_base_hp("STT", large), 30)
        self.assertEqual(get_team_base_hp("Alfa", large), 25)

    def test_declaration_period_is_only_round_three(self):
        self.assertFalse(is_declaration_period(1))
        self.assertFalse(is_declaration_period(2))
        self.assertTrue(is_declaration_period(3))
        self.assertFalse(is_declaration_period(4))


class TestBacklogSpend(unittest.TestCase):
    def test_adding_hp_marks_a_simple_task_complete(self):
        data = create_game_state()
        add_backlog_spend(data, "Alfa", "alfa_1", 15)
        task = data["backlog"]["Alfa"][0]
        self.assertEqual(task["id"], "alfa_1")
        self.assertEqual(task["spenderade_hp"], 15)
        self.assertTrue(task["slutford"])

    def test_spend_never_goes_below_zero(self):
        data = create_game_state()
        add_backlog_spend(data, "Alfa", "alfa_1", 5)
        add_backlog_spend(data, "Alfa", "alfa_1", -20)
        self.assertEqual(data["backlog"]["Alfa"][0]["spenderade_hp"], 0)
        self.assertFalse(data["backlog"]["Alfa"][0]["slutford"])

    def test_spend_never_exceeds_task_total(self):
        data = create_game_state()
        add_backlog_spend(data, "Alfa", "alfa_1", 100)
        self.assertEqual(data["backlog"]["Alfa"][0]["spenderade_hp"], 15)
        self.assertTrue(data["backlog"]["Alfa"][0]["slutford"])

    def test_bravo_phase_spend_never_exceeds_phase_total(self):
        data = create_game_state()
        add_backlog_spend(data, "Bravo", "bravo_1_Krav", 100)
        krav = data["backlog"]["Bravo"][0]["faser"][0]
        self.assertEqual(krav["spenderade_hp"], 10)
        self.assertTrue(krav["slutford"])

    def test_recurring_task_progress_is_capped_per_occurrence(self):
        data = create_game_state()
        add_backlog_spend(data, "STT", "stt_4", 100)
        task = next(item for item in data["backlog"]["STT"] if item["id"] == "stt_4")
        self.assertEqual(task["spenderade_hp"], 10)
        self.assertFalse(task["slutford"])

    def test_bravo_phase_completes_only_when_all_phases_are_done(self):
        data = create_game_state()
        add_backlog_spend(data, "Bravo", "bravo_1_Krav", 10)
        uppgift = data["backlog"]["Bravo"][0]
        self.assertTrue(uppgift["faser"][0]["slutford"])
        self.assertFalse(uppgift["slutford"])
        for fas in uppgift["faser"]:
            need = int(fas["estimaterade_hp"]) - int(fas["spenderade_hp"])
            if need:
                add_backlog_spend(data, "Bravo", "bravo_1", need, phase=fas["namn"])
        self.assertTrue(data["backlog"]["Bravo"][0]["slutford"])

    def test_apply_order_hp_once_to_linked_task(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([
                    activity(
                        "Inloggning val",
                        hp=8,
                        backlog_selected="alfa_1",
                        backlog_item="alfa_1",
                    )
                ], final=True)
            }
        }
        apply_activity_hp_to_backlog(data, "Alfa", 0)
        self.assertEqual(data["backlog"]["Alfa"][0]["spenderade_hp"], 8)
        self.assertTrue(
            data["team_orders"]["orders_round_1"]["Alfa"]["orders"]["activities"][0]["backlog_applied"]
        )
        with self.assertRaises(ValueError):
            apply_activity_hp_to_backlog(data, "Alfa", 0)
        inbox = build_inbox(data)
        self.assertFalse(inbox[0]["can_apply_backlog"])
        self.assertTrue(inbox[0]["backlog_applied"])

    def test_apply_bravo_phase_from_selected_id(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Bravo": order_record([
                    activity(
                        "Grafisk visning valet - Krav",
                        hp=10,
                        backlog_selected="bravo_1_Krav",
                    )
                ], final=True)
            }
        }
        apply_activity_hp_to_backlog(data, "Bravo", 0)
        self.assertEqual(data["backlog"]["Bravo"][0]["faser"][0]["spenderade_hp"], 10)

    def test_custom_activity_cannot_be_applied(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([
                    activity("Hemligt", hp=5, backlog_selected="custom")
                ], final=True)
            }
        }
        with self.assertRaises(ValueError):
            apply_activity_hp_to_backlog(data, "Alfa", 0)

    def test_undo_restores_backlog_spend(self):
        data = create_game_state()
        add_backlog_spend(data, "Alfa", "alfa_1", 5)
        push_undo(data, "Backlog")
        add_backlog_spend(data, "Alfa", "alfa_1", 5)
        data, label = apply_undo(data)
        self.assertEqual(label, "Backlog")
        self.assertEqual(data["backlog"]["Alfa"][0]["spenderade_hp"], 5)

    def test_live_state_includes_backlog_board(self):
        data = create_game_state()
        add_backlog_spend(data, "Alfa", "alfa_1", 5)
        state = build_live_state(data)
        alfa = next(team for team in state["backlog"] if team["team"] == "Alfa")
        self.assertEqual(alfa["items"][0]["spent"], 5)
        self.assertGreater(alfa["estimated"], 0)


class TestOrderWithdrawAndEdit(unittest.TestCase):
    def test_team_can_withdraw_during_order_phase(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(hp=8)], final=True),
            }
        }
        withdraw_order(data, "Alfa")
        self.assertFalse(data["team_orders"]["orders_round_1"]["Alfa"]["final"])
        self.assertEqual(team_order_status(data, "Alfa"), "draft")

    def test_cannot_withdraw_during_diplomacy(self):
        data = create_game_state(fas="Diplomatifas")
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(hp=8)], final=True),
            }
        }
        with self.assertRaises(ValueError):
            withdraw_order(data, "Alfa")

    def test_gm_can_edit_activity_without_leaving_budget(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(name="API", hp=8, syfte="bygga")], final=True),
            }
        }
        update_activity(data, "Alfa", 0, {"hp": 12, "aktivitet": "API hårdning", "syfte": "skydd"})
        row = data["team_orders"]["orders_round_1"]["Alfa"]["orders"]["activities"][0]
        self.assertEqual(row["hp"], 12)
        self.assertEqual(row["aktivitet"], "API hårdning")
        self.assertTrue(data["team_orders"]["orders_round_1"]["Alfa"]["edited_by_gm"])

    def test_gm_edit_rejects_over_budget(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(hp=8)], final=True),
            }
        }
        with self.assertRaises(ValueError):
            update_activity(data, "Alfa", 0, {"hp": 40})
        self.assertEqual(
            data["team_orders"]["orders_round_1"]["Alfa"]["orders"]["activities"][0]["hp"],
            8,
        )


class TestPublicProjector(unittest.TestCase):
    def test_public_state_has_hp_but_not_orders_or_log(self):
        data = create_game_state()
        set_regeringsstod(data, "Alfa", True)
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record([activity(name="Hemlig DDOS", hp=8)], final=True),
            }
        }
        append_gm_log(data, "hp", "hemlig justering")
        public = build_public_state(data)
        self.assertEqual(public["fas"], "Orderfas")
        alfa = next(t for t in public["teams"] if t["team"] == "Alfa")
        self.assertEqual(alfa["hp"], 35)
        self.assertTrue(alfa["regeringsstod"])
        dumped = str(public)
        self.assertNotIn("Hemlig DDOS", dumped)
        self.assertNotIn("hemlig justering", dumped)
        self.assertNotIn("inbox", public)
        self.assertNotIn("log", public)
        self.assertNotIn("history", public)
        self.assertNotIn("test_mode", public)
        self.assertNotIn("llm", public)
        self.assertNotIn("llm_forslag", public)
        self.assertIn("progress", public)
        alfa_progress = next(team for team in public["progress"] if team["team"] == "Alfa")
        self.assertIn("Inloggning val", [item["name"] for item in alfa_progress["items"]])
        self.assertNotIn("id", alfa_progress["items"][0])

    def test_public_progress_tracks_spent_hp_without_orders(self):
        data = create_game_state()
        add_backlog_spend(data, "Alfa", "alfa_1", 8)
        public = build_public_state(data)
        alfa = next(team for team in public["progress"] if team["team"] == "Alfa")
        login = next(item for item in alfa["items"] if item["name"] == "Inloggning val")
        self.assertEqual(login["spent"], 8)
        self.assertEqual(login["estimated"], 15)
        self.assertGreater(login["percent"], 0)
        dumped = str(public)
        self.assertNotIn("HP per klick", dumped)


class TestRoundTestdata(unittest.TestCase):
    def test_round_files_exist_and_differ(self):
        from gm_console import load_round_testdata

        round1 = load_round_testdata(1)
        round2 = load_round_testdata(2)
        round3 = load_round_testdata(3)
        round4 = load_round_testdata(4)
        self.assertEqual(round1["runda"], 1)
        self.assertIn("Alfa", round1["orders"])
        self.assertIn("Inloggning val", round1["orders"]["Alfa"][0]["aktivitet"])
        self.assertIn("Sökfunktion", round2["orders"]["Alfa"][0]["aktivitet"])
        self.assertTrue(any("deklaration" in (a.get("syfte") or "").lower() or "deklaration" in (a.get("aktivitet") or "").lower()
                           for a in round3["orders"]["STT"]))
        self.assertTrue(any(a.get("backlog_selected") == "stt_6" for a in round4["orders"]["STT"]))
        self.assertNotEqual(
            round1["orders"]["Alfa"][0]["aktivitet"],
            round2["orders"]["Alfa"][0]["aktivitet"],
        )

    def test_apply_test_orders_fills_current_round(self):
        from gm_console import apply_test_orders

        data = create_game_state()
        data["test_mode"] = True
        data, processed = apply_test_orders(data)
        self.assertIn("Alfa", processed)
        alfa = data["team_orders"]["orders_round_1"]["Alfa"]
        self.assertTrue(alfa["final"])
        self.assertEqual(alfa["orders"]["activities"][0]["backlog_selected"], "alfa_1")
        self.assertEqual(team_order_status(data, "Alfa"), "submitted")

    def test_apply_test_orders_uses_round_two_file(self):
        from gm_console import apply_test_orders

        data = create_game_state(runda=2)
        data["test_mode"] = True
        data, _processed = apply_test_orders(data)
        alfa = data["team_orders"]["orders_round_2"]["Alfa"]
        self.assertIn("Sökfunktion", alfa["orders"]["activities"][0]["aktivitet"])
        self.assertNotIn("orders_round_1", data["team_orders"])

    def test_apply_test_orders_requires_test_mode(self):
        from gm_console import apply_test_orders

        data = create_game_state()
        with self.assertRaises(ValueError):
            apply_test_orders(data)

    def test_missing_round_file_raises(self):
        from gm_console import load_round_testdata

        with self.assertRaises(ValueError):
            load_round_testdata(9)


class TestLlmForslag(unittest.TestCase):
    def _example_json(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testdata",
            "llm-svar-exempel.json",
        )
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def test_old_games_without_llm_key_still_load(self):
        data = create_game_state()
        self.assertIsNone(get_llm_forslag(data))
        live = build_live_state(data)
        self.assertIsNone(live.get("llm"))
        public = build_public_state(data)
        self.assertNotIn("llm", public)
        self.assertNotIn("llm_forslag", public)
        with self.assertRaises(ValueError):
            apply_llm_hp(data)

    def test_export_contains_instructions_and_schema(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": order_record(
                    [activity(name="Inloggning val", hp=10, backlog_selected="alfa_1")],
                    final=True,
                ),
            }
        }
        text = build_llm_export_text(data, data["team_orders"]["orders_round_1"], randint=lambda: 44)
        self.assertIn("Svara ENDAST", text)
        self.assertIn("JSON-SCHEMA", text)
        self.assertIn("Inloggning val", text)
        self.assertIn("alfa_1", text)
        self.assertIn("order_ref: Alfa-1", text)
        self.assertIn("Alfa-1: 44", text)
        self.assertIn("inte att ordern måste få ett sannolikhetsutfall", text)
        self.assertIn("BACKLOGARBETE ÄR INTE ETT SANNOLIKHETSSLAG", text)
        self.assertIn("FALL A", text)
        self.assertIn('"utfall"', text)
        self.assertIn('"nyheter"', text)
        self.assertIn('"milstolpar"', text)
        self.assertIn("TIDIGARE RELEVANTA UTFALL", text)
        self.assertEqual(get_round_rolls(data)["Alfa-1"], 44)
        again = build_llm_export_text(data, data["team_orders"]["orders_round_1"], randint=lambda: 1)
        self.assertEqual(get_round_rolls(data)["Alfa-1"], 44)
        self.assertIn("Alfa-1: 44", again)

    def test_parse_strips_fences_and_aliases(self):
        data = create_game_state()
        raw = (
            "```json\n"
            + json.dumps({
                "runda": 1,
                "nyheter": [{"rubrik": "Rubrik", "upplasning": "Text", "lag": ["Lag Alfa"]}],
                "hp": [{"lag": "alfa", "delta": -5, "orsak": "Press"}],
                "milstolpar": [{"lag": "Alfa", "uppgift": "Inloggning val", "delta_hp": 8}],
            })
            + "\n```"
        )
        parsed = parse_llm_forslag(raw, data)
        self.assertEqual(parsed["nyheter"][0]["lag"], ["Alfa"])
        self.assertEqual(parsed["hp"][0]["lag"], "Alfa")
        self.assertEqual(parsed["milstolpar"][0]["uppgift"], "alfa_1")
        self.assertFalse(parsed["hp_applied"])

    def test_skips_unknown_team_and_unknown_milestone(self):
        data = create_game_state()
        parsed = parse_llm_forslag(json.dumps({
            "hp": [
                {"lag": "Narnia", "delta": -9},
                {"lag": "Alfa", "delta": 4},
            ],
            "milstolpar": [
                {"lag": "Alfa", "uppgift": "finns_inte", "delta_hp": 5},
                {"lag": "Alfa", "uppgift": "alfa_1", "delta_hp": 6},
            ],
        }), data)
        self.assertEqual(parsed["hp"], [{"lag": "Alfa", "delta": 4, "orsak": ""}])
        self.assertEqual(len(parsed["milstolpar"]), 1)
        self.assertEqual(parsed["milstolpar"][0]["uppgift"], "alfa_1")
        self.assertTrue(parsed["warnings"])

    def test_import_apply_hp_and_milestones_then_undo(self):
        data = create_game_state()
        import_llm_forslag(data, self._example_json())
        self.assertEqual(get_llm_forslag(data)["nyheter"][0]["rubrik"][:14], "Valmyndigheten")
        public = build_public_state(data)
        dumped = str(public)
        self.assertNotIn("Valmyndigheten", dumped)
        self.assertNotIn("llm", public)

        apply_llm_hp(data)
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 20)
        self.assertEqual(data["poang"]["Bravo"]["aktuell"], 30)
        self.assertTrue(get_llm_forslag(data)["hp_applied"])
        with self.assertRaises(ValueError):
            apply_llm_hp(data)

        apply_llm_milestones(data)
        alfa_task = next(
            item for item in data["backlog"]["Alfa"] if item["id"] == "alfa_1"
        )
        self.assertEqual(alfa_task["spenderade_hp"], 10)
        bravo_krav = next(
            fas for fas in next(
                item for item in data["backlog"]["Bravo"] if item["id"] == "bravo_1"
            )["faser"]
            if fas["namn"] == "Krav"
        )
        self.assertEqual(bravo_krav["spenderade_hp"], 10)

        data, label = apply_undo(data)
        self.assertEqual(label, "Tillämpa LLM-milstolpar")
        alfa_task = next(
            item for item in data["backlog"]["Alfa"] if item["id"] == "alfa_1"
        )
        self.assertEqual(alfa_task["spenderade_hp"], 0)
        data, _label = apply_undo(data)
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 25)
        self.assertFalse(get_llm_forslag(data)["hp_applied"])


class TestLlmResolution(unittest.TestCase):
    def _submit(self, data, team="Alfa", activities=None, runda=None):
        runda = runda or data.get("runda") or 1
        activities = activities or [activity(name="API", hp=10)]
        key = f"orders_round_{runda}"
        orders = dict(data.get("team_orders") or {})
        round_orders = dict(orders.get(key) or {})
        round_orders[team] = order_record(activities, final=True)
        orders[key] = round_orders
        data["team_orders"] = orders
        return data

    def _utfall(self, **overrides):
        item = {
            "lag": "Alfa",
            "order_ref": "Alfa-1",
            "order": "API",
            "satsad_hp": 10,
            "motstand_hp": 5,
            "sannolikhet": 75,
            "slump": 44,
            "resultat": "framgång",
            "motivering": "Alfa hade ungefär dubbelt så stor relevant satsning.",
        }
        item.update(overrides)
        return item

    def test_order_refs_are_deterministic(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name="A", hp=5), activity(name="B", hp=5)])
        self._submit(data, "STT", [activity(name="C", hp=8)])
        refs = current_order_refs(data)
        self.assertEqual(refs, ["Alfa-1", "Alfa-2", "STT-1"])
        self.assertEqual(make_order_ref("FM", 1), "FM-1")
        self.assertEqual(current_order_refs(data), refs)

    def test_rolls_are_one_to_hundred_and_stable(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name="A", hp=5), activity(name="B", hp=5)])
        seq = iter([11, 22, 33])
        rolls = ensure_round_rolls(data, randint=lambda: next(seq))
        self.assertEqual(rolls, {"Alfa-1": 11, "Alfa-2": 22})
        self.assertTrue(all(1 <= value <= 100 for value in rolls.values()))
        again = ensure_round_rolls(data, randint=lambda: 99)
        self.assertEqual(again, {"Alfa-1": 11, "Alfa-2": 22})

    def test_new_order_gets_roll_without_changing_old(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name="A", hp=5)])
        ensure_round_rolls(data, randint=lambda: 40)
        self._submit(data, "Alfa", [activity(name="A", hp=5), activity(name="B", hp=7)])
        rolls = ensure_round_rolls(data, randint=lambda: 81)
        self.assertEqual(rolls["Alfa-1"], 40)
        self.assertEqual(rolls["Alfa-2"], 81)

    def test_deleting_an_activity_does_not_move_existing_order_refs(self):
        data = create_game_state()
        first = activity(name="A", hp=5, id=101)
        second = activity(name="B", hp=5, id=202)
        self._submit(data, "Alfa", [first, second])
        ensure_round_rolls(data, randint=iter([40, 60]).__next__)

        third = activity(name="C", hp=5, id=303)
        self._submit(data, "Alfa", [second, third])
        ensure_round_rolls(data, randint=lambda: 81)

        self.assertEqual(current_order_refs(data), ["Alfa-2", "Alfa-3"])
        self.assertEqual(
            get_round_rolls(data),
            {"Alfa-1": 40, "Alfa-2": 60, "Alfa-3": 81},
        )

    def test_second_round_gets_independent_rolls(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name="A", hp=5)], runda=1)
        ensure_round_rolls(data, randint=lambda: 12)
        data["runda"] = 2
        self._submit(data, "Alfa", [activity(name="B", hp=5)], runda=2)
        ensure_round_rolls(data, randint=lambda: 90)
        self.assertEqual(get_round_rolls(data, 1), {"Alfa-1": 12})
        self.assertEqual(get_round_rolls(data, 2), {"Alfa-1": 90})

    def test_undo_does_not_reroll(self):
        data = create_game_state()
        self._submit(data)
        push_undo(data, "HP")
        adjust_hp(data, "Alfa", -1, "test")
        ensure_round_rolls(data, randint=lambda: 55)
        data, _label = apply_undo(data)
        self.assertEqual(data["poang"]["Alfa"]["aktuell"], 25)
        self.assertEqual(get_round_rolls(data), {"Alfa-1": 55})
        ensure_round_rolls(
            data,
            randint=lambda: self.fail("undo försökte skapa ett nytt slag"),
        )
        self.assertEqual(current_order_refs(data), ["Alfa-1"])

    def test_valid_utfall_is_accepted(self):
        data = create_game_state()
        self._submit(data)
        ensure_round_rolls(data, randint=lambda: 44)
        parsed = parse_llm_forslag(json.dumps({
            "runda": 1,
            "utfall": [self._utfall()],
            "nyheter": [],
            "hp": [],
            "milstolpar": [],
        }), data)
        self.assertEqual(parsed["utfall"][0]["resultat"], "framgång")
        import_llm_forslag(data, json.dumps({
            "utfall": [self._utfall()],
            "nyheter": [{"rubrik": "Störning", "upplasning": "Belastning.", "lag": ["Alfa"]}],
        }))
        self.assertEqual(get_round_utfall(data)[0]["slump"], 44)

    def test_old_response_without_utfall_still_imports(self):
        data = create_game_state()
        parsed = parse_llm_forslag(json.dumps({
            "runda": 1,
            "nyheter": [{"rubrik": "Rubrik", "upplasning": "Text", "lag": ["Alfa"]}],
            "hp": [],
            "milstolpar": [],
        }), data)
        self.assertEqual(parsed["utfall"], [])

    def test_old_game_without_llm_resolution_loads(self):
        data = create_game_state()
        self.assertEqual(get_round_rolls(data), {})
        self.assertEqual(get_round_utfall(data), [])
        live = build_live_state(data)
        self.assertIsNone(live.get("llm"))

    def test_old_rolls_without_activity_refs_are_reused(self):
        data = create_game_state()
        self._submit(
            data,
            "Alfa",
            [activity(name="A", hp=5), activity(name="B", hp=5)],
        )
        data["llm_resolution"] = {
            "1": {"rolls": {"Alfa-1": 12, "Alfa-2": 34}, "result": None}
        }
        ensure_round_rolls(
            data,
            randint=lambda: self.fail("ett gammalt fryst slag ersattes"),
        )
        self.assertEqual(current_order_refs(data), ["Alfa-1", "Alfa-2"])
        self.assertEqual(get_round_rolls(data), {"Alfa-1": 12, "Alfa-2": 34})

    def test_rejects_probability_out_of_range(self):
        data = create_game_state()
        self._submit(data)
        ensure_round_rolls(data, randint=lambda: 44)
        with self.assertRaises(ValueError):
            parse_llm_forslag(json.dumps({"utfall": [self._utfall(sannolikhet=9)]}), data)
        with self.assertRaises(ValueError):
            parse_llm_forslag(json.dumps({"utfall": [self._utfall(sannolikhet=91)]}), data)
        self.assertIsNone(get_llm_forslag(data))

    def test_rejects_invalid_result_unknown_team_and_ref(self):
        data = create_game_state()
        self._submit(data)
        ensure_round_rolls(data, randint=lambda: 44)
        with self.assertRaises(ValueError):
            parse_llm_forslag(json.dumps({"utfall": [self._utfall(resultat="vinst")]}), data)
        with self.assertRaises(ValueError):
            parse_llm_forslag(json.dumps({"utfall": [self._utfall(lag="Narnia")]}), data)
        with self.assertRaises(ValueError):
            parse_llm_forslag(json.dumps({"utfall": [self._utfall(order_ref="Alfa-9")]}), data)

    def test_rejects_team_that_does_not_own_order_ref(self):
        data = create_game_state()
        self._submit(data)
        ensure_round_rolls(data, randint=lambda: 44)
        with self.assertRaises(ValueError) as ctx:
            parse_llm_forslag(
                json.dumps({"utfall": [self._utfall(lag="Bravo")]}),
                data,
            )
        self.assertIn("Alfa-1", str(ctx.exception))
        self.assertIn("Alfa", str(ctx.exception))

    def test_rejects_llm_invented_roll(self):
        data = create_game_state()
        self._submit(data)
        ensure_round_rolls(data, randint=lambda: 44)
        with self.assertRaises(ValueError) as ctx:
            parse_llm_forslag(json.dumps({"utfall": [self._utfall(slump=81)]}), data)
        self.assertIn("Alfa-1", str(ctx.exception))
        self.assertIn("44", str(ctx.exception))
        self.assertIsNone(get_llm_forslag(data))

    def test_invalid_utfall_does_not_store_hp_suggestions(self):
        data = create_game_state()
        self._submit(data)
        ensure_round_rolls(data, randint=lambda: 44)
        payload = {
            "utfall": [self._utfall(slump=1)],
            "hp": [{"lag": "Alfa", "delta": -9, "orsak": "ska inte sparas"}],
        }
        with self.assertRaises(ValueError):
            import_llm_forslag(data, json.dumps(payload))
        self.assertIsNone(get_llm_forslag(data))

    def test_previous_outcomes_appear_in_later_prompt(self):
        data = create_game_state()
        self._submit(data)
        ensure_round_rolls(data, randint=lambda: 44)
        import_llm_forslag(data, json.dumps({"utfall": [self._utfall()]}))
        data["runda"] = 2
        self._submit(data, runda=2)
        text = build_llm_export_text(
            data, data["team_orders"]["orders_round_2"], randint=lambda: 70
        )
        self.assertIn("TIDIGARE RELEVANTA UTFALL", text)
        self.assertIn("Runda 1:", text)
        self.assertIn("Alfa-1", text)
        self.assertIn("framgång", text)

    def test_public_state_hides_resolution(self):
        data = create_game_state()
        self._submit(data)
        ensure_round_rolls(data, randint=lambda: 44)
        import_llm_forslag(data, json.dumps({
            "utfall": [self._utfall()],
            "nyheter": [{"rubrik": "Störningar drabbar tekniska system", "upplasning": "Belastning.", "lag": ["Alfa"]}],
        }))
        public = build_public_state(data)
        dumped = str(public)
        self.assertNotIn("llm_resolution", public)
        self.assertNotIn("utfall", public)
        self.assertNotIn("rolls", public)
        self.assertNotIn("sannolikhet", dumped)
        self.assertNotIn("Alfa-1", dumped)
        self.assertNotIn("dubbelt så stor", dumped)
        self.assertNotIn("llm_forslag", public)


class TestLlmDeterministicBacklog(unittest.TestCase):
    def _submit(self, data, team, activities, runda=None):
        runda = runda or data.get("runda") or 1
        key = f"orders_round_{runda}"
        orders = dict(data.get("team_orders") or {})
        round_orders = dict(orders.get(key) or {})
        round_orders[team] = order_record(activities, final=True)
        orders[key] = round_orders
        data["team_orders"] = orders
        return data

    def test_prompt_says_unused_rolls_must_be_ignored(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name="Inloggning val", hp=10, backlog_selected="alfa_1")])
        text = build_llm_export_text(data, data["team_orders"]["orders_round_1"], randint=lambda: 66)
        self.assertIn("Alfa-1: 66", text)
        self.assertIn("slumpvärdet ignoreras", text)
        self.assertIn("10/20 färdig", text)
        self.assertIn("base_progress", text)

    def test_pure_backlog_work_imports_without_utfall(self):
        data = create_game_state()
        self._submit(data, "Bravo", [activity(
            name="Grafisk visning valet - Design",
            hp=10,
            backlog_selected="bravo_1_Design",
        )])
        ensure_round_rolls(data, randint=lambda: 66)
        parsed = parse_llm_forslag(json.dumps({
            "runda": 1,
            "utfall": [],
            "nyheter": [],
            "hp": [],
            "milstolpar": [{
                "lag": "Bravo",
                "uppgift": "bravo_1_Design",
                "delta_hp": 10,
                "orsak": "10 HP designarbete. Inget slump.",
            }],
        }), data)
        self.assertEqual(parsed["utfall"], [])
        self.assertEqual(parsed["milstolpar"][0]["delta_hp"], 10)
        self.assertEqual(get_round_rolls(data)["Bravo-1"], 66)
        import_llm_forslag(data, json.dumps({
            "utfall": [],
            "milstolpar": [{
                "lag": "Bravo",
                "uppgift": "bravo_1_Design",
                "delta_hp": 10,
            }],
        }))
        self.assertEqual(get_round_utfall(data), [])
        apply_llm_milestones(data)
        design = next(
            fas for fas in next(
                item for item in data["backlog"]["Bravo"] if item["id"] == "bravo_1"
            )["faser"]
            if fas["namn"] == "Design"
        )
        self.assertEqual(design["spenderade_hp"], 10)

    def test_full_remaining_milestone_needs_no_probability(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name="Sökfunktion", hp=10, backlog_selected="alfa_3")])
        ensure_round_rolls(data, randint=lambda: 12)
        add_backlog_spend(data, "Alfa", "alfa_3", 10)
        parsed = parse_llm_forslag(json.dumps({
            "utfall": [],
            "milstolpar": [{"lag": "Alfa", "uppgift": "alfa_3", "delta_hp": 10}],
        }), data)
        self.assertEqual(parsed["utfall"], [])
        self.assertEqual(parsed["milstolpar"][0]["delta_hp"], 10)

    def test_over_investment_is_capped_in_prompt_and_suggestion(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name="Sökfunktion", hp=10, backlog_selected="alfa_3")])
        ensure_round_rolls(data, randint=lambda: 8)
        add_backlog_spend(data, "Alfa", "alfa_3", 15)
        text = build_llm_export_text(data, data["team_orders"]["orders_round_1"], randint=lambda: 8)
        self.assertIn("min(satsad_hp, återstående_hp)", text)
        parsed = parse_llm_forslag(json.dumps({
            "utfall": [],
            "milstolpar": [{"lag": "Alfa", "uppgift": "alfa_3", "delta_hp": 5}],
        }), data)
        self.assertEqual(parsed["milstolpar"][0]["delta_hp"], 5)
        import_llm_forslag(data, json.dumps({
            "milstolpar": [{"lag": "Alfa", "uppgift": "alfa_3", "delta_hp": 5}],
        }))
        apply_llm_milestones(data)
        task = next(item for item in data["backlog"]["Alfa"] if item["id"] == "alfa_3")
        self.assertEqual(task["spenderade_hp"], 20)

    def test_milestone_suggestion_is_clamped_to_remaining_hp(self):
        data = create_game_state()
        add_backlog_spend(data, "Alfa", "alfa_1", 12)
        parsed = parse_llm_forslag(json.dumps({
            "utfall": [],
            "milstolpar": [{
                "lag": "Alfa",
                "uppgift": "alfa_1",
                "delta_hp": 10,
            }],
        }), data)
        self.assertEqual(parsed["milstolpar"][0]["delta_hp"], 3)
        self.assertTrue(parsed["warnings"])

    def test_backlog_plus_contested_outcome_keeps_progress_and_optional_delmal(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(
            name="Sökfunktion",
            hp=12,
            backlog_selected="alfa_3",
            syfte="Få sök i produktion före Bravo.",
        )])
        self._submit(data, "STT", [activity(
            name="Vägra släppa Alfas sök utan motprestation",
            hp=6,
            paverkar=["Alfa"],
        )])
        seq = iter([100, 40])
        ensure_round_rolls(data, randint=lambda: next(seq))
        parsed = parse_llm_forslag(json.dumps({
            "utfall": [{
                "lag": "Alfa",
                "order_ref": "Alfa-1",
                "order": "Sökfunktion",
                "delmal": "Få sökfunktionen produktionssatt",
                "satsad_hp": 12,
                "motstand_hp": 6,
                "sannolikhet": 40,
                "slump": 100,
                "resultat": "misslyckande",
                "motivering": "Utvecklingsarbetet går vidare, men STT blockerar produktionssättningen.",
            }],
            "milstolpar": [{
                "lag": "Alfa",
                "uppgift": "alfa_3",
                "delta_hp": 12,
                "orsak": "12 HP utvecklingsarbete. Produktionssättningen avgörs separat.",
            }],
        }), data)
        self.assertEqual(parsed["milstolpar"][0]["delta_hp"], 12)
        self.assertEqual(parsed["utfall"][0]["delmal"], "Få sökfunktionen produktionssatt")
        self.assertEqual(parsed["utfall"][0]["resultat"], "misslyckande")

    def test_sabotage_may_have_utfall_while_progress_depends_on_outcome(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name="Sökfunktion", hp=10, backlog_selected="alfa_3")])
        self._submit(data, "STT", [activity(
            name="Sabotera Search",
            hp=5,
            typ="forstora",
            paverkar=["Alfa"],
        )])
        seq = iter([88, 20])
        ensure_round_rolls(data, randint=lambda: next(seq))
        parsed = parse_llm_forslag(json.dumps({
            "utfall": [{
                "lag": "STT",
                "order_ref": "STT-1",
                "order": "Sabotera Search",
                "satsad_hp": 5,
                "motstand_hp": 10,
                "sannolikhet": 30,
                "slump": 20,
                "resultat": "delvis framgång",
                "motivering": "Sabotaget stör delen av arbetet. Alfa får minskad progress.",
            }],
            "milstolpar": [{
                "lag": "Alfa",
                "uppgift": "alfa_3",
                "delta_hp": 6,
                "orsak": "10 HP arbete minskat till +6 efter delvis lyckat sabotage.",
            }],
        }), data)
        refs = {item["order_ref"] for item in parsed["utfall"]}
        self.assertEqual(refs, {"STT-1"})
        self.assertEqual(parsed["milstolpar"][0]["delta_hp"], 6)
        self.assertEqual(get_round_rolls(data)["Alfa-1"], 88)

    def test_subset_of_orders_may_have_utfall(self):
        data = create_game_state()
        self._submit(data, "Alfa", [activity(name=f"A{i}", hp=1) for i in range(5)])
        self._submit(data, "Bravo", [activity(name=f"B{i}", hp=1) for i in range(4)])
        self._submit(data, "STT", [activity(name=f"S{i}", hp=1) for i in range(4)])
        seq = iter(range(1, 14))
        ensure_round_rolls(data, randint=lambda: next(seq))
        self.assertEqual(len(get_round_rolls(data)), 13)
        payload = {
            "utfall": [
                {
                    "lag": "Alfa",
                    "order_ref": "Alfa-2",
                    "order": "A1",
                    "satsad_hp": 1,
                    "motstand_hp": 0,
                    "sannolikhet": 10,
                    "slump": 2,
                    "resultat": "framgång",
                    "motivering": "Osäker handling.",
                },
                {
                    "lag": "Bravo",
                    "order_ref": "Bravo-1",
                    "order": "B0",
                    "satsad_hp": 1,
                    "motstand_hp": 0,
                    "sannolikhet": 10,
                    "slump": 6,
                    "resultat": "misslyckande",
                    "motivering": "Osäker handling.",
                },
                {
                    "lag": "STT",
                    "order_ref": "STT-3",
                    "order": "S2",
                    "satsad_hp": 1,
                    "motstand_hp": 0,
                    "sannolikhet": 10,
                    "slump": 12,
                    "resultat": "framgång",
                    "motivering": "Osäker handling.",
                },
                {
                    "lag": "Alfa",
                    "order_ref": "Alfa-5",
                    "order": "A4",
                    "satsad_hp": 1,
                    "motstand_hp": 0,
                    "sannolikhet": 10,
                    "slump": 5,
                    "resultat": "delvis framgång",
                    "motivering": "Osäker handling.",
                },
            ],
            "nyheter": [],
            "hp": [],
            "milstolpar": [],
        }
        import_llm_forslag(data, json.dumps(payload))
        self.assertEqual(len(get_round_utfall(data)), 4)
        self.assertEqual(len(get_round_rolls(data)), 13)
        self.assertEqual(get_round_rolls(data)["Alfa-1"], 1)


class TestLlmJsonImportErrors(unittest.TestCase):
    def _payload(self, **extra):
        body = {
            "runda": 1,
            "utfall": [],
            "nyheter": [],
            "hp": [],
            "milstolpar": [],
        }
        body.update(extra)
        return body

    def test_valid_json_imports(self):
        data = create_game_state()
        parsed = parse_llm_forslag(json.dumps(self._payload()), data)
        self.assertEqual(parsed["nyheter"], [])
        self.assertFalse(parsed["hp_applied"])

    def test_swedish_characters_work(self):
        data = create_game_state()
        raw = json.dumps(self._payload(nyheter=[{
            "rubrik": "Åäö-nyhet",
            "upplasning": "Text med åäö.",
            "lag": [],
        }]), ensure_ascii=False)
        parsed = parse_llm_forslag(raw, data)
        self.assertEqual(parsed["nyheter"][0]["rubrik"], "Åäö-nyhet")

    def test_escaped_quotes_import(self):
        data = create_game_state()
        raw = (
            '{"runda":1,"utfall":[],"nyheter":[{"rubrik":'
            '"Mata Media med \\"läckt\\" valfusk","upplasning":"Text","lag":[]}],'
            '"hp":[],"milstolpar":[]}'
        )
        parsed = parse_llm_forslag(raw, data)
        self.assertEqual(parsed["nyheter"][0]["rubrik"], 'Mata Media med "läckt" valfusk')

    def test_unescaped_quotes_are_rejected_with_location_and_hint(self):
        data = create_game_state()
        raw = '{"order":"Mata Media med "läckt" valfusk"}'
        with self.assertRaises(LlmJsonSyntaxError) as ctx:
            parse_llm_forslag(raw, data)
        formatted = ctx.exception.formatted
        self.assertIsInstance(ctx.exception.__cause__, json.JSONDecodeError)
        self.assertIn("rad 1", formatted["message"])
        self.assertIn("kolumn", formatted["message"])
        self.assertEqual(formatted["lineno"], 1)
        self.assertGreater(formatted["colno"], 1)
        self.assertIn("Expecting ',' delimiter", formatted["detail"])
        self.assertIn("läckt", formatted["snippet"])
        self.assertIn("↑", formatted["pointer"])
        self.assertIn('\\"', formatted["hint"])
        self.assertIsNone(get_llm_forslag(data))

    def test_markdown_json_fence_is_accepted(self):
        data = create_game_state()
        inner = json.dumps(self._payload(runda=2))
        raw = f"```json\n{inner}\n```"
        parsed = parse_llm_forslag(raw, data)
        self.assertEqual(parsed["utfall"], [])

    def test_markdown_fence_without_language_is_accepted(self):
        data = create_game_state()
        inner = json.dumps(self._payload(runda=2))
        parsed = parse_llm_forslag(f"```\n{inner}\n```", data)
        self.assertEqual(parsed["runda"], 1)

    def test_extra_prose_is_rejected_with_outside_json_hint(self):
        data = create_game_state()
        raw = "Här är svaret:\n" + json.dumps(self._payload(runda=2))
        with self.assertRaises(LlmJsonSyntaxError) as ctx:
            parse_llm_forslag(raw, data)
        self.assertIn("utanför JSON-objektet", ctx.exception.formatted["hint"])

    def test_trailing_prose_is_rejected_with_outside_json_hint(self):
        data = create_game_state()
        raw = json.dumps(self._payload(runda=2)) + "\nHoppas det hjälper."
        with self.assertRaises(LlmJsonSyntaxError) as ctx:
            parse_llm_forslag(raw, data)
        self.assertIn("utanför JSON-objektet", ctx.exception.formatted["hint"])

    def test_multiline_syntax_error_reports_line_and_column(self):
        data = create_game_state()
        raw = (
            "{\n"
            '  "runda": 1,\n'
            '  "utfall": [],\n'
            '  "nyheter": [],\n'
            '  "hp": [],\n'
            '  "milstolpar":\n'
            "}"
        )
        with self.assertRaises(LlmJsonSyntaxError) as ctx:
            parse_llm_forslag(raw, data)
        formatted = ctx.exception.formatted
        self.assertEqual(formatted["lineno"], 7)
        self.assertEqual(formatted["colno"], 1)
        self.assertIn("rad 7", formatted["message"])
        self.assertIn("kolumn 1", formatted["message"])
        self.assertIn("↑", formatted["pointer"])

    def test_format_json_error_does_not_mutate_input(self):
        raw = '{"order":"Mata Media med "läckt" valfusk"}'
        original = raw
        try:
            json.loads(raw)
        except json.JSONDecodeError as exc:
            formatted = format_json_error(raw, exc)
        self.assertEqual(raw, original)
        self.assertIn("läckt", formatted["snippet"])
        self.assertIn("copy_text", formatted)

    def test_domain_error_is_not_a_syntax_error(self):
        data = create_game_state()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": {
                    "final": True,
                    "submitted_at": 1,
                    "orders": {"activities": [{"aktivitet": "X", "hp": 5}]},
                }
            }
        }
        ensure_round_rolls(data, randint=lambda: 44)
        with self.assertRaises(ValueError) as ctx:
            parse_llm_forslag(json.dumps({
                "utfall": [{
                    "lag": "Alfa",
                    "order_ref": "Alfa-1",
                    "order": "X",
                    "satsad_hp": 5,
                    "motstand_hp": 0,
                    "sannolikhet": 50,
                    "slump": 21,
                    "resultat": "framgång",
                    "motivering": "x",
                }]
            }), data)
        self.assertNotIsInstance(ctx.exception, LlmJsonSyntaxError)
        self.assertIn("Alfa-1", str(ctx.exception))
        self.assertIn("44", str(ctx.exception))


class TestSessionAndPassword(unittest.TestCase):
    def test_password_round_trip(self):
        stored = encrypt_password("hemligt")
        self.assertTrue(verify_password(stored, "hemligt"))
        self.assertFalse(verify_password(stored, "fel"))

    def test_session_is_valid_until_timeout_then_expires(self):
        session = create_game_session("g1")
        self.assertTrue(is_game_session_valid("g1", session))
        self.assertFalse(is_game_session_valid("other", session))
        session["timestamp"] = time.time() - SESSION_TIMEOUT_SECONDS - 1
        self.assertFalse(is_game_session_valid("g1", session))

    def test_refreshing_session_extends_validity(self):
        session = create_game_session("g1")
        session["timestamp"] = time.time() - SESSION_TIMEOUT_SECONDS + 10
        refresh_game_session(session)
        self.assertTrue(is_game_session_valid("g1", session))


class TestGameCreation(unittest.TestCase):
    def test_two_games_created_in_same_second_do_not_overwrite_each_other(self):
        fixed_now = real_datetime(2025, 1, 2, 3, 4, 5)
        with tempfile.TemporaryDirectory() as data_dir, \
                patch("models.DATA_DIR", data_dir), \
                patch("models.datetime") as mocked_datetime, \
                patch("models.secrets.token_hex", side_effect=["aaaa", "bbbb"]):
            mocked_datetime.now.return_value = fixed_now
            first = skapa_nytt_spel("2025-01-02", "A", 20, 10, 10)
            second = skapa_nytt_spel("2025-01-02", "B", 20, 10, 10)

            self.assertNotEqual(first, second)
            self.assertTrue(os.path.exists(os.path.join(data_dir, f"game_{first}.json")))
            self.assertTrue(os.path.exists(os.path.join(data_dir, f"game_{second}.json")))


if __name__ == "__main__":
    unittest.main()
