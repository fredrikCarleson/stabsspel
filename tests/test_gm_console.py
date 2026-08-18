"""Tests for Game Master live-console helpers."""
import json
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
from gm_console_ui import create_projector_html


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

    def test_gm_javascript_defines_its_poll_interval(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "static",
            "gm-console.js",
        )
        with open(path, encoding="utf-8") as handle:
            script = handle.read()
        self.assertRegex(script, r"var\s+POLL_MS\s*=\s*[1-9][0-9]*\s*;")

    def test_projector_json_cannot_close_its_script_element(self):
        data = sample_game()
        data["fas"] = "</script><script>alert('x')</script>"
        html = create_projector_html("g1", data)
        self.assertNotIn("</script><script>alert('x')</script>", html)
        self.assertIn("\\u003c/script", html)

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
        self.assertIn("backlog_estimated", inbox_row)

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
        self.assertIn("överförbart", html)
        self.assertIn("Space starta/pausa", html)
        self.assertIn('data-hp-delta', html)
        self.assertIn("gm-backlog-amount", html)
        self.assertIn("HP per klick", html)
        self.assertNotIn("−5</button>", html)
        self.assertNotIn("+5</button>", html)

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
        self.assertIn("gm-inbox-team", fragments["inbox"])
        self.assertIn("Öppna för laget", fragments["inbox"])
        self.assertIn("Redigera", fragments["inbox"])
        self.assertIn('aria-label="Ändra"', fragments["inbox"])
        self.assertNotIn("Lägg +5 HP", fragments["inbox"])
        self.assertIn("gm-inbox-activity", fragments["inbox"])
        self.assertIn("5/15", fragments["backlog"])

        data["fas"] = "Diplomatifas"
        fragments = live_html_fragments("g1", build_live_state(data))
        self.assertIn("Lägg +5 HP", fragments["inbox"])
        self.assertIn('class="success gm-mini"', fragments["inbox"])
        self.assertNotIn("Öppna för laget", fragments["inbox"])
        self.assertIn('gm-inbox-hp-est">/ 15', fragments["inbox"])

    def test_inbox_groups_team_actions_once(self):
        from gm_console_ui import live_html_fragments
        from gm_console import build_live_state

        data = sample_game()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": {
                    "final": True,
                    "submitted_at": 1,
                    "orders": {
                        "activities": [
                            {
                                "aktivitet": "Inloggning val",
                                "syfte": "klar",
                                "hp": 10,
                                "typ": "bygga",
                                "paverkar": ["Alfa"],
                                "backlog_selected": "alfa_1",
                            },
                            {
                                "aktivitet": "API",
                                "syfte": "snabbare",
                                "hp": 8,
                                "typ": "bygga",
                                "paverkar": ["STT"],
                            },
                        ]
                    },
                }
            }
        }
        inbox = live_html_fragments("g1", build_live_state(data))["inbox"]
        self.assertEqual(inbox.count('class="gm-inbox-team"'), 1)
        self.assertEqual(inbox.count("Öppna för laget"), 1)
        self.assertEqual(inbox.count(">Redigera</a>"), 1)
        self.assertEqual(inbox.count("gm-inbox-activity-row"), 2)
        self.assertNotIn("Lägg +", inbox)

        data["fas"] = "Diplomatifas"
        dip = live_html_fragments("g1", build_live_state(data))["inbox"]
        self.assertEqual(dip.count("Lägg +10 HP"), 1)
        self.assertNotIn("Öppna för laget", dip)
        self.assertIn("gm-type-tag is-build", dip)

    def test_admin_order_form_has_back_to_console(self):
        from team_order_routes import TEAM_ORDER_TEMPLATE

        self.assertIn("Tillbaka till spelledarpanel", TEAM_ORDER_TEMPLATE)
        self.assertIn("{% if show_gm_back %}", TEAM_ORDER_TEMPLATE)
        self.assertIn("{% if is_admin_edit %}", TEAM_ORDER_TEMPLATE)
        self.assertIn("Skicka slutgiltig order", TEAM_ORDER_TEMPLATE)
        self.assertIn("Spara utkast", TEAM_ORDER_TEMPLATE)
        self.assertNotIn("Uppdatera Order", TEAM_ORDER_TEMPLATE)

    def test_backlog_choice_meta_matches_dropdown(self):
        from team_order_routes import TEAM_ORDER_TEMPLATE, backlog_choice_meta, generate_backlog_options

        meta = backlog_choice_meta()
        self.assertEqual(meta["alfa_1"]["team"], "Alfa")
        self.assertEqual(meta["alfa_1"]["hp"], 15)
        self.assertEqual(meta["alfa_1"]["namn"], "Inloggning val")
        self.assertEqual(meta["alfa_1"]["syfte"], "Driva Inloggning val vidare i backlog")
        self.assertEqual(meta["bravo_1_Krav"]["team"], "Bravo")
        self.assertEqual(meta["bravo_1_Krav"]["hp"], 10)
        html = generate_backlog_options()
        self.assertIn('value="alfa_1"', html)
        self.assertIn('value="bravo_1_Krav"', html)
        self.assertIn("BACKLOG_META", TEAM_ORDER_TEMPLATE)
        self.assertIn("order-sticky", TEAM_ORDER_TEMPLATE)
        self.assertIn("Ni har ${remainingHP} HP kvar", TEAM_ORDER_TEMPLATE)
        self.assertIn("handleBacklogSelection", TEAM_ORDER_TEMPLATE)

    def test_projector_shows_public_hp_without_gm_controls(self):
        from gm_console_ui import create_projector_html

        data = sample_game()
        data["fas"] = "Resultatfas"
        html = create_projector_html("g1", data)
        self.assertIn("projector-clock", html)
        self.assertIn("Alfa", html)
        self.assertIn("Teamens arbete", html)
        self.assertIn("Inloggning val", html)
        self.assertIn("projector-progress", html)
        self.assertIn("projector-audio-hint", html)
        self.assertIn("Klicka för ljudvarningar", html)
        self.assertIn("projector.js?v=3", html)
        self.assertNotIn("Starta", html)
        self.assertNotIn("Pausa", html)
        self.assertNotIn("Testläge", html)
        self.assertNotIn("Orderinkorg", html)
        self.assertNotIn("HP per klick", html)

    def test_result_phase_shows_run_of_show(self):
        from gm_console_ui import create_gm_console_html

        data = sample_game()
        data["fas"] = "Resultatfas"
        html = create_gm_console_html("g1", data)
        self.assertIn("Resultatfas — körschema", html)
        self.assertIn("Öppna spelarskärm", html)
        self.assertIn("gm-quarters", html)
        self.assertIn("Okt–Dec", html)
        self.assertIn("gm-quarter is-current", html)
        self.assertIn("Peka på kvartalen här", html)
        self.assertNotIn("under den här panelen", html)
        self.assertIn("gm-tabs", html)
        self.assertIn('aria-selected="true">Lag</button>', html)
        self.assertIn('id="gm-panel-inkorg" aria-labelledby="gm-tab-inkorg" hidden', html)
        self.assertIn("Starta nästa runda", html)
        self.assertLess(html.find("Resultatfas — körschema"), html.find("gm-tabs"))
        self.assertLess(html.find("Orderinkorg"), html.find("Lag och handlingspoäng"))

        data["runda"] = 4
        html = create_gm_console_html("g1", data)
        self.assertIn("Avsluta spelet", html)
        self.assertNotIn("Starta nästa runda", html)

        data["avslutat"] = True
        html = create_gm_console_html("g1", data)
        self.assertIn("Spelet är slut", html)
        self.assertNotIn("Resultatfas — körschema", html)

    def test_console_shows_phase_history_not_leftover_chrome(self):
        from gm_console_ui import create_gm_console_html, live_html_fragments
        from gm_console import apply_next_phase, build_live_state

        data = sample_game()
        html = create_gm_console_html("g1", data)
        self.assertIn("gm-history", html)
        self.assertIn("pågår", html)
        self.assertNotIn("KVARTALSFÖRLOPP", html)
        self.assertNotIn("Team Översikt", html)
        self.assertNotIn("Spelhistorik", html)
        fragments = live_html_fragments("g1", build_live_state(data))
        self.assertIn("gm-history", fragments["log"])
        self.assertIn("Orderfas", fragments["log"])

        apply_next_phase(data)
        html = create_gm_console_html("g1", data)
        self.assertIn("Diplomatifas", html)
        self.assertIn("klar", html)
        self.assertIn("pågår", html)

    def test_orderfas_readiness_board(self):
        from gm_console_ui import attention_items, create_gm_console_html, live_html_fragments
        from gm_console import build_live_state

        data = sample_game()
        html = create_gm_console_html("g1", data)
        self.assertIn('id="gm-readiness-root"', html)
        self.assertIn("gm-chip", html)
        self.assertIn("Saknas", html)
        self.assertIn("gm-tabs", html)
        self.assertIn('data-tab="inkorg"', html)
        self.assertIn("Inkorg", html)
        self.assertIn("Arbete", html)
        self.assertIn("Historik", html)
        self.assertIn('id="gm-tab-inkorg"', html)
        self.assertIn('aria-selected="true">Inkorg</button>', html)
        self.assertIn("gm-mer-menu", html)
        self.assertIn("gm-menu", html)
        self.assertIn(">Meny</summary>", html)
        self.assertIn("Nollställ timer", html)
        self.assertIn("Föregående", html)
        self.assertIn('value="prev_fas"', html)
        self.assertLess(html.find('value="prev_fas"'), html.find("gm-mer-menu"))
        self.assertNotIn("Gå till nästa fas? Det går att ångra.", html)
        self.assertIn("Testläge", html)
        self.assertIn("Redigera order", html)
        self.assertNotIn("Ange order", html)
        self.assertIn('id="gm-test-form"', html)
        self.assertIn('class="gm-autofill" hidden', html)
        self.assertIn('id="gm-attention" hidden', html)
        self.assertIn('value="next_fas" class="primary"', html)
        self.assertIn('value="start" class="success"', html)
        self.assertNotIn('value="next_fas" class="success"', html)
        self.assertIn('value="pause" class="warning"', html)
        self.assertIn("lag utan inskickad order", html)
        self.assertEqual(attention_items(build_live_state(data)), [])
        fragments = live_html_fragments("g1", build_live_state(data))
        self.assertIn("gm-chip", fragments["readiness"])
        self.assertEqual(fragments["attention"], "")

        data["fas"] = "Diplomatifas"
        dip = create_gm_console_html("g1", data)
        self.assertNotIn("gm-chip", dip)
        self.assertIn("gm-tabs", dip)
        items = attention_items(build_live_state(data))
        self.assertTrue(any("utan inskickad order" in item for item in items))

    def test_orderfas_chip_flags_missing_hp(self):
        from gm_console_ui import create_gm_console_html

        data = sample_game()
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": {
                    "final": True,
                    "submitted_at": 1,
                    "orders": {
                        "activities": [{
                            "aktivitet": "DDOS",
                            "syfte": "ner",
                            "hp": 0,
                            "typ": "forstora",
                            "paverkar": ["STT"],
                        }]
                    },
                }
            }
        }
        html = create_gm_console_html("g1", data)
        self.assertIn("Inne", html)
        self.assertIn("saknar HP", html)
        self.assertIn("Saknas", html)


    def test_diplomatifas_job_is_inbox(self):
        from gm_console_ui import attention_items, create_gm_console_html
        from gm_console import build_live_state

        data = sample_game()
        data["fas"] = "Diplomatifas"
        html = create_gm_console_html("g1", data)
        self.assertIn("Kopiera ordrar till LLM", html)
        self.assertIn("Importera LLM-svar", html)
        self.assertIn("Nästa: Resultatfas", html)
        self.assertIn('value="prev_fas" class="secondary"', html)
        self.assertNotIn('value="prev_fas" class="secondary" disabled', html)
        self.assertIn("Orderinkorg", html)
        self.assertIn("gm-tabs", html)
        self.assertIn('id="gm-tab-inkorg"', html)
        self.assertIn('aria-selected="true">Inkorg</button>', html)
        self.assertLess(html.find("Kopiera ordrar till LLM"), html.find("gm-tabs"))
        self.assertLess(html.find("Kopiera ordrar till LLM"), html.find("Orderinkorg"))
        self.assertLess(html.find("Orderinkorg"), html.find("Lag och handlingspoäng"))
        self.assertLess(html.find("Lag och handlingspoäng"), html.find("Teamens arbete"))
        items = attention_items(build_live_state(data))
        self.assertTrue(any("utan inskickad order" in item for item in items))

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
                    "final": True,
                    "submitted_at": 1,
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
        html = create_gm_console_html("g1", data)
        self.assertIn("Konflikt", html)
        self.assertIn("DDOS", html)

    def test_gm_can_edit_orders_without_test_mode(self):
        from gm_console_ui import create_gm_console_html, live_html_fragments
        from gm_console import build_live_state

        data = sample_game()
        html = create_gm_console_html("g1", data)
        self.assertIn("Redigera order", html)
        self.assertNotIn("Ange order", html)
        self.assertIn('class="gm-autofill" hidden', html)
        self.assertNotIn("cheat-link", html)
        self.assertNotIn("Importera LLM-svar", html)

        data["test_mode"] = True
        html = create_gm_console_html("g1", data)
        self.assertIn("Redigera order", html)
        self.assertNotIn('class="gm-autofill" hidden', html)
        self.assertIn("Auto-fyll testdata", html)

        data["fas"] = "Diplomatifas"
        data["test_mode"] = False
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": {
                    "final": True,
                    "submitted_at": 1,
                    "orders": {
                        "activities": [{
                            "aktivitet": "API",
                            "syfte": "snabbare",
                            "hp": 8,
                            "typ": "bygga",
                            "paverkar": ["STT"],
                        }]
                    },
                }
            }
        }
        html = create_gm_console_html("g1", data)
        self.assertIn("Redigera order", html)
        self.assertIn("Ändra", html)
        fragments = live_html_fragments("g1", build_live_state(data))
        self.assertIn(">Redigera</a>", fragments["inbox"])
        self.assertIn('aria-label="Ändra"', fragments["inbox"])
        self.assertNotIn("Öppna för laget", fragments["inbox"])
        self.assertIn('class="gm-autofill" hidden', fragments["inbox"])

        data["fas"] = "Resultatfas"
        html = create_gm_console_html("g1", data)
        self.assertNotIn("Redigera order", html)

    def test_llm_suggestions_render_after_import(self):
        from gm_console import import_llm_forslag
        from gm_console_ui import create_gm_console_html

        example = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testdata",
            "llm-svar-exempel.json",
        )
        data = sample_game()
        data["fas"] = "Diplomatifas"
        with open(example, encoding="utf-8") as handle:
            import_llm_forslag(data, handle.read())
        html = create_gm_console_html("g1", data)
        self.assertIn("Valmyndigheten tar första steget", html)
        self.assertIn("Tillämpa HP", html)
        self.assertIn("Tillämpa milstolpar", html)
        self.assertIn("Kopiera nyheter till papper", html)

    def test_gm_shows_utfall_probability_roll_and_reason(self):
        from gm_console import ensure_round_rolls, import_llm_forslag
        from gm_console_ui import create_gm_console_html, create_projector_html

        data = sample_game()
        data["fas"] = "Diplomatifas"
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": {
                    "final": True,
                    "submitted_at": 1,
                    "orders": {
                        "activities": [{
                            "aktivitet": "Massiv DDOS-attack mot valservern",
                            "syfte": "ner",
                            "hp": 8,
                            "typ": "forstora",
                            "paverkar": ["STT"],
                        }]
                    },
                }
            }
        }
        ensure_round_rolls(data, randint=lambda: 27)
        import_llm_forslag(data, json.dumps({
            "utfall": [{
                "lag": "Alfa",
                "order_ref": "Alfa-1",
                "order": "Massiv DDOS-attack mot valservern",
                "satsad_hp": 8,
                "motstand_hp": 12,
                "sannolikhet": 35,
                "slump": 27,
                "resultat": "framgång",
                "motivering": "STT hade ett tydligt resursövertag i försvaret, men det låga slaget gjorde att attacken lyckades.",
            }],
            "nyheter": [{
                "rubrik": "Störningar drabbar tekniska system inför extravalet",
                "upplasning": "Tekniska miljöer utsattes för omfattande belastning.",
                "lag": ["Alfa", "STT"],
            }],
        }))
        html = create_gm_console_html("g1", data)
        self.assertIn("Utfall och sannolikhet", html)
        self.assertIn("35 %", html)
        self.assertIn("Slag 27", html)
        self.assertIn("FRAMGÅNG", html)
        self.assertIn("8 HP mot 12 HP", html)
        self.assertIn("STT hade ett tydligt resursövertag", html)
        self.assertIn("Störningar drabbar tekniska system", html)
        projector = create_projector_html("g1", data)
        self.assertNotIn("Utfall och sannolikhet", projector)
        self.assertNotIn("Slag 27", projector)
        self.assertNotIn("resursövertag", projector)
        self.assertNotIn("Alfa-1", projector)

    def test_deterministic_backlog_is_not_shown_as_dice_outcome(self):
        from gm_console import ensure_round_rolls, import_llm_forslag
        from gm_console_ui import create_gm_console_html, create_projector_html

        data = sample_game()
        data["fas"] = "Diplomatifas"
        data["team_orders"] = {
            "orders_round_1": {
                "Alfa": {
                    "final": True,
                    "submitted_at": 1,
                    "orders": {"activities": [{
                        "aktivitet": "Sökfunktion",
                        "syfte": "Utveckla sök och få den i produktion.",
                        "hp": 12,
                        "typ": "bygga",
                        "backlog_selected": "alfa_3",
                        "paverkar": ["STT"],
                    }]},
                },
                "Bravo": {
                    "final": True,
                    "submitted_at": 2,
                    "orders": {"activities": [{
                        "aktivitet": "Grafisk visning valet - Design",
                        "syfte": "Nästa vattenfallssteg.",
                        "hp": 10,
                        "typ": "bygga",
                        "backlog_selected": "bravo_1_Design",
                        "paverkar": ["Bravo"],
                    }]},
                },
                "STT": {
                    "final": True,
                    "submitted_at": 3,
                    "orders": {"activities": [{
                        "aktivitet": "Vägra släppa Alfas sök utan motprestation",
                        "syfte": "Blockera produktion.",
                        "hp": 6,
                        "typ": "bygga",
                        "paverkar": ["Alfa"],
                    }]},
                },
            }
        }
        seq = iter([100, 66, 39])
        ensure_round_rolls(data, randint=lambda: next(seq))
        import_llm_forslag(data, json.dumps({
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
            "milstolpar": [
                {"lag": "Alfa", "uppgift": "alfa_3", "delta_hp": 12, "orsak": "Utveckling."},
                {"lag": "Bravo", "uppgift": "bravo_1_Design", "delta_hp": 10, "orsak": "Designarbete."},
            ],
        }))
        html = create_gm_console_html("g1", data)
        self.assertIn("Utfall och sannolikhet", html)
        self.assertIn("Få sökfunktionen produktionssatt", html)
        self.assertIn("40 %", html)
        self.assertIn("Slag 100", html)
        self.assertIn("Sökfunktion", html)
        self.assertIn("+12 HP", html)
        self.assertIn("+10 HP", html)
        self.assertIn("Grafisk visning valet", html)
        self.assertNotIn("Bravo · Order 1", html)
        self.assertNotIn("90 %", html)
        self.assertNotIn("Slag 66", html)
        projector = create_projector_html("g1", data)
        self.assertNotIn("Utfall och sannolikhet", projector)
        self.assertNotIn("produktionssatt", projector)
        self.assertNotIn("Slag 100", projector)


    def test_invalid_json_error_keeps_pasted_text_and_shows_snippet(self):
        from gm_console import format_json_error
        from gm_console_ui import create_gm_console_html

        data = sample_game()
        data["fas"] = "Diplomatifas"
        raw = '{"order":"Mata Media med "läckt" valfusk"}'
        try:
            json.loads(raw)
            self.fail("expected JSONDecodeError")
        except json.JSONDecodeError as exc:
            formatted = format_json_error(raw, exc)
        html = create_gm_console_html("g1", data, llm_import={
            "text": raw,
            "json_error": formatted,
        })
        self.assertIn("Ogiltig JSON", html)
        self.assertIn("Expecting &#39;,&#39; delimiter", html)
        self.assertIn("läckt", html)
        self.assertIn("gm-json-error", html)
        self.assertIn("Kopiera fel", html)
        self.assertIn('id="gm-llm-json"', html)
        self.assertIn("Mata Media med", html)
        self.assertIn('aria-invalid="true"', html)

    def test_json_error_snippet_is_html_escaped(self):
        from gm_console_ui import create_gm_console_html

        data = sample_game()
        data["fas"] = "Diplomatifas"
        html = create_gm_console_html("g1", data, llm_import={
            "text": '{"x":"<script>alert(1)</script>"}',
            "json_error": {
                "message": "Ogiltig JSON nära rad 1, kolumn 1.",
                "detail": "Expecting value",
                "snippet": "<script>alert(1)</script>",
                "pointer": "↑",
                "hint": "Kontrollera JSON-strukturen nära markeringen.",
                "copy_text": "Ogiltig JSON\n<script>alert(1)</script>",
            },
        })
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_domain_import_error_does_not_use_syntax_heading(self):
        from gm_console_ui import create_gm_console_html

        data = sample_game()
        data["fas"] = "Diplomatifas"
        payload = '{"utfall":[]}'
        html = create_gm_console_html("g1", data, llm_import={
            "text": payload,
            "domain_error": "Slumpvärdet för Alfa-1 är 21 i LLM-svaret, men spelet har 20.",
        })
        self.assertIn("Kunde inte importera", html)
        self.assertIn("Alfa-1", html)
        self.assertNotIn("Ogiltig JSON nära", html)
        self.assertIn("utfall", html)


if __name__ == "__main__":
    unittest.main()
