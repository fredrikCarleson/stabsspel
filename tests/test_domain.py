"""
High-value domain tests for Stabsspel.

These protect game-state rules that would silently corrupt a live event:
phases, HP, order budgets, undo, timers, and roster size.
They do not render the GUI.
"""
import time
import unittest
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
    apply_new_round,
    apply_next_phase,
    apply_previous_phase,
    apply_undo,
    build_inbox,
    build_live_state,
    build_public_state,
    build_team_strip,
    can_submit_orders,
    effective_hp,
    end_game,
    hp_delta_from_fields,
    missing_order_teams,
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
        self.assertNotIn("test_mode", public)
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


if __name__ == "__main__":
    unittest.main()
