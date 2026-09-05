"""
HTML for the Game Master live console.

News is produced outside the app: copy orders to an LLM, paste JSON
suggestions back, print headlines for the studio. This UI keeps that
workflow first-class and puts orders, HP, time, and phase on one screen.
"""

from markupsafe import escape
import json
import re
from gm_console import STATUS_LABELS, build_live_state, build_public_state
from models import MAX_RUNDA


def _fmt_time(seconds):
    seconds = max(0, int(seconds or 0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _json_for_script(value):
    """Serialize JSON without allowing data to terminate a script element."""
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


CHIP_LABELS = {
    "empty": "Saknas",
    "draft": "Utkast",
    "submitted": "Inne",
    "changed": "Ändrad",
}

GM_CLOCK_WARN_S = 300
GM_CLOCK_DANGER_S = 60
_HP_SUFFIX = re.compile(r"\s*\(\d+\s*HP\)\s*$", re.I)
_TEAM_TONES = {
    "alfa": "alfa",
    "bravo": "bravo",
    "stt": "stt",
    "fm": "fm",
    "bs": "bs",
    "media": "media",
    "säpo": "sapo",
    "sapo": "sapo",
    "regeringen": "regeringen",
    "usa": "usa",
}


def _status_class(status):
    return {
        "empty": "gm-status-empty",
        "draft": "gm-status-draft",
        "submitted": "gm-status-submitted",
        "changed": "gm-status-changed",
    }.get(status, "")


def _clock_warn_class(remaining):
    remaining = int(remaining or 0)
    if remaining <= GM_CLOCK_DANGER_S:
        return " is-danger"
    if remaining <= GM_CLOCK_WARN_S:
        return " is-warning"
    return ""


def _timer_status_label(status):
    return {
        "running": "Pågår",
        "paused": "Pausad",
        "stopped": "Inte startad",
    }.get(status, status or "")


def attention_items(state):
    items = []
    fas = state.get("fas")
    missing = state.get("missing_teams") or []
    # Orderfas shows missing teams on the readiness chips; do not repeat them here.
    if missing and fas == "Diplomatifas":
        items.append(f"{len(missing)} lag utan inskickad order: {', '.join(missing)}")
    if state.get("conflict_count"):
        items.append(f"{state['conflict_count']} mål med ordrar från flera lag")
    over = [t for t in state.get("teams") or [] if t.get("remaining", 0) < 0]
    if over:
        items.append("HP över budget: " + ", ".join(t["team"] for t in over))
    return items


_HEROICONS = {
    "bars-3": (
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"/>'
    ),
    "beaker": (
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.169.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23-.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.131 3.601-1.14.181-2.345.271-3.571.271-3.044 0-5.952-.725-8.429-2.004"/>'
    ),
    "table-cells": (
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.25m11.25 0h-4m4 0a1.125 1.125 0 0 0 1.125-1.125M20.625 19.5V5.625m0 0A1.125 1.125 0 0 0 19.5 4.5h-15a1.125 1.125 0 0 0-1.125 1.125m16.25 0v5.625m-16.25-5.625v13.75m0-13.75A1.125 1.125 0 0 1 4.5 4.5h6.375v16m6.25-16H19.5a1.125 1.125 0 0 1 1.125 1.125v5.625m-7.5 8.125h7.5"/>'
    ),
    "queue-list": (
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 0 1 0 3.75H5.625a1.875 1.875 0 0 1 0-3.75Z"/>'
    ),
    "identification": (
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Zm6-10.125a1.875 1.875 0 1 1-3.75 0 1.875 1.875 0 0 1 3.75 0Zm1.294 6.336a6.721 6.721 0 0 1-3.17.665 6.721 6.721 0 0 1-3.168-.665 3.375 3.375 0 0 1 6.338 0Z"/>'
    ),
    "arrow-up-tray": (
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"/>'
    ),
    "squares-2x2": (
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 8.25 20.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z"/>'
    ),
    "arrow-path": (
        '<path stroke-linecap="round" stroke-linejoin="round" '
        'd="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"/>'
    ),
}


def _heroicon(name):
    return (
        f'<svg class="gm-menu-icon" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.5" aria-hidden="true">'
        f"{_HEROICONS[name]}</svg>"
    )


def _gm_menu_item(href, icon, label, extra=""):
    return (
        f'<a class="gm-menu-item" role="menuitem" href="{href}"{extra}>'
        f"{_heroicon(icon)}{escape(label)}</a>"
    )


def gm_app_menu_html(spel_id, test_mode=False, runda=1, has_orders=False):
    """Classic top-left overflow: tools and risky actions, not live phase controls."""
    sid = escape(spel_id)
    test_checked = "checked" if test_mode else ""
    test_class = "is-on" if test_mode else ""
    autofill_hidden = "" if test_mode else " hidden"
    autofill_label = "Ersätt med testdata…" if has_orders else "Fyll med testdata"
    autofill_confirm = (
        f"Ersätt alla ordrar för runda {int(runda)} med testdata?"
        if has_orders
        else f"Fyll alla lag med testdata för runda {int(runda)}?"
    )
    return (
        f'<details class="gm-menu gm-app-menu">'
        f'<summary aria-haspopup="menu" aria-label="Meny">'
        f'{_heroicon("bars-3")}<span>Meny</span></summary>'
        f'<div class="gm-mer-menu" role="menu">'
        f'<form method="post" action="/admin/{sid}/test_mode" id="gm-test-form" class="gm-test-form">'
        f'<input type="hidden" name="enabled" id="gm-test-enabled" value="{"1" if test_mode else "0"}">'
        f'<label class="gm-test gm-menu-item {test_class}">'
        f'{_heroicon("beaker")}'
        f'<input type="checkbox" id="gm-test-mode" {test_checked} '
        f"onchange=\"this.form.querySelector('[name=enabled]').value=this.checked?'1':'0'; this.form.submit();\">"
        f"Testläge</label></form>"
        f'<form method="post" action="/admin/{sid}/auto_fill_orders" '
        f'class="gm-autofill gm-menu-autofill"{autofill_hidden} '
        f'onsubmit="return confirm(\'{escape(autofill_confirm)}\');">'
        f'<button type="submit" class="gm-menu-item" role="menuitem">'
        f'{_heroicon("beaker")}{escape(autofill_label)}</button></form>'
        f'{_gm_menu_item(f"/admin/{sid}/poang", "table-cells", "HP-tabell")}'
        f'{_gm_menu_item(f"/admin/{sid}/backlog", "queue-list", "Backlog")}'
        f'{_gm_menu_item(f"/admin/{sid}/aktivitetskort", "identification", "Aktivitetskort", " target=_blank")}'
        f'{_gm_menu_item(f"/admin/{sid}/order_summary", "arrow-up-tray", "LLM-export")}'
        f'{_gm_menu_item("/admin", "squares-2x2", "Alla spel")}'
        f'<form method="post" action="/admin/{sid}/reset" class="gm-menu-danger" '
        f"onsubmit=\"return confirm('Återställ HELA spelet till runda 1? Detta går att ångra en gång, men raderar rundor och ordrar.');\">"
        f'<button type="submit" class="danger gm-menu-item" role="menuitem">'
        f'{_heroicon("arrow-path")}Återställ spel</button></form>'
        f"</div></details>"
    )


def _gm_game_meta_html(spel_id, data):
    bits = []
    if data.get("datum"):
        bits.append(escape(str(data["datum"])))
    if data.get("plats"):
        bits.append(escape(str(data["plats"])))
    if data.get("antal_spelare"):
        bits.append(f'{escape(str(data["antal_spelare"]))} spelare')
    lag_html = ", ".join(
        f'<a href="/team/{escape(spel_id)}/{escape(lag)}" target="_blank" '
        f'class="gm-meta-link">{escape(lag)}</a>'
        for lag in data.get("lag") or []
    )
    if lag_html:
        bits.append(lag_html)
    return f'<p class="gm-meta">{" · ".join(bits)}</p>' if bits else ""


def _signed_delta(n):
    n = int(n or 0)
    return f"+{n}" if n > 0 else str(n)


def _news_copy_text(nyheter):
    blocks = []
    for item in nyheter or []:
        rubrik = (item.get("rubrik") or "").strip()
        uppl = (item.get("upplasning") or "").strip()
        parts = [p for p in (rubrik, uppl) if p]
        if parts:
            blocks.append("\n\n".join(parts))
    return "\n\n---\n\n".join(blocks)


def _split_order_ref(ref):
    team, sep, number = str(ref or "").rpartition("-")
    if not sep:
        return ref, ""
    return team, number


def _utfall_section_html(llm, show_heading=True):
    utfall = (llm or {}).get("utfall") or []
    rolls = (llm or {}).get("rolls") or {}
    if utfall:
        cards = "".join(_utfall_card_html(item) for item in utfall)
        heading = '<h3 class="gm-section-title">Utfall och sannolikhet</h3>' if show_heading else ""
        return (
            f'<div class="gm-utfall">'
            f'{heading}'
            f"{cards}"
            f"</div>"
        )
    if rolls:
        items = " · ".join(
            f"{escape(str(ref))}: {int(value)}" for ref, value in rolls.items()
        )
        return (
            f'<p class="gm-utfall-rolls">Slag (innan LLM-svar): {items}. '
            f"Sannolikhet och resultat kommer efter import.</p>"
        )
    return ""


def _utfall_card_html(item):
    resultat = item.get("resultat") or ""
    mark = {"framgång": "✓", "delvis framgång": "~", "misslyckande": "✕"}.get(resultat, "")
    label = resultat.upper() if resultat else ""
    tone = {
        "framgång": "is-success",
        "delvis framgång": "is-partial",
        "misslyckande": "is-fail",
    }.get(resultat, "")
    team, number = _split_order_ref(item.get("order_ref") or "")
    order_no = f"Order {escape(number)}" if number else escape(item.get("order_ref") or "")
    satsad = int(item.get("satsad_hp") or 0)
    motstand = int(item.get("motstand_hp") or 0)
    sannolikhet = int(item.get("sannolikhet") or 0)
    slump = int(item.get("slump") or 0)
    delmal = str(item.get("delmal") or "").strip()
    delmal_html = (
        f'<p class="gm-utfall-delmal">{escape(delmal)}</p>' if delmal else ""
    )
    return (
        f'<article class="gm-utfall-card {tone}">'
        f'<p class="gm-utfall-meta">{escape(item.get("lag") or team)} · {order_no}</p>'
        f'<p class="gm-utfall-order">{escape(item.get("order") or "")}</p>'
        f"{delmal_html}"
        f'<p class="gm-utfall-hp">{satsad} HP mot {motstand} HP</p>'
        f'<div class="gm-utfall-headline" aria-label="Chans {sannolikhet} procent, Slag {slump}, Utfall {escape(label.lower())}">'
        f'<span class="gm-utfall-metric"><small>Chans</small><strong>{sannolikhet} %</strong></span>'
        f'<span class="gm-utfall-arrow" aria-hidden="true">→</span>'
        f'<span class="gm-utfall-metric"><small>Slag</small><strong>{slump}</strong></span>'
        f'<span class="gm-utfall-arrow" aria-hidden="true">→</span>'
        f'<span class="gm-utfall-metric gm-utfall-result {tone}"><small>Utfall</small><strong>{escape(mark)} {escape(label)}</strong></span>'
        f"</div>"
        f'<p class="gm-utfall-why">{escape(item.get("motivering") or "")}</p>'
        f"</article>"
    )


def _tab_alert_html(text):
    if not text:
        return ""
    return (
        f'<span class="gm-tab-alert" title="{escape(text)}">'
        f"Att göra</span>"
    )


def _has_llm_import(llm):
    return bool(
        llm
        and (
            llm.get("importerad")
            or llm.get("nyheter")
            or llm.get("hp")
            or llm.get("milstolpar")
            or llm.get("utfall")
        )
    )


def _llm_statusbar_html(spel_id, state):
    if state.get("fas") not in ("Diplomatifas", "Resultatfas"):
        return ""
    has_import = _has_llm_import(state.get("llm") or {})
    status_class = " is-imported" if has_import else ""
    status = "✓ LLM-svar importerat" if has_import else "LLM-svar saknas"
    help_text = (
        "Resultatet finns under fliken LLM-resultat."
        if has_import else "Kopiera underlaget och importera svaret på nästa sida."
    )
    action_class = "secondary" if has_import else "primary"
    action_label = "Öppna LLM-underlag" if has_import else "Kopiera till LLM"
    return f'''
      <div class="gm-llm-statusbar{status_class}">
        <div class="gm-llm-state">
          <strong>{status}</strong>
          <span>{help_text}</span>
        </div>
        <a href="/admin/{escape(spel_id)}/order_summary" class="{action_class}">{action_label}</a>
      </div>
    '''


def _llm_block_html(spel_id, state, default_result_tab=None):
    fas = state.get("fas")
    if fas not in ("Diplomatifas", "Resultatfas"):
        return ""
    sid = escape(spel_id)
    llm = state.get("llm") or {}
    has_import = _has_llm_import(llm)
    if not has_import:
        return (
            '<div class="gm-llm-empty" id="gm-llm-results">'
            '<h3>Inget LLM-svar importerat</h3>'
            '<p>Kopiera först rundans underlag och importera sedan JSON-svaret.</p>'
            f'<a href="/admin/{sid}/order_summary" class="primary">Kopiera till LLM</a>'
            '</div>'
        )

    utfall_html = _utfall_section_html(llm, show_heading=False)

    warnings = "".join(
        f"<li>{escape(item)}</li>" for item in (llm.get("warnings") or [])
    )
    warning_html = (
        f'<ul class="gm-llm-warnings">{warnings}</ul>' if warnings else ""
    )

    news_items = []
    for item in llm.get("nyheter") or []:
        lag = ", ".join(item.get("lag") or [])
        lag_html = f'<p class="gm-muted">{escape(lag)}</p>' if lag else ""
        news_items.append(
            f'<article class="gm-news-item">'
            f'<h4>{escape(item.get("rubrik") or "(utan rubrik)")}</h4>'
            f'{lag_html}'
            f'<p>{escape(item.get("upplasning") or "")}</p>'
            f"</article>"
        )
    news_html = "".join(news_items) or "<p class=\"gm-muted\">Inga nyhetsförslag.</p>"
    news_copy = escape(_news_copy_text(llm.get("nyheter") or []))
    news_copy_btn = ""
    if llm.get("nyheter"):
        news_copy_btn = (
            f'<textarea id="gm-news-copy" class="gm-news-copy" readonly hidden>{news_copy}</textarea>'
            f'<button type="button" class="secondary sm" '
            f"onclick=\"navigator.clipboard.writeText(document.getElementById('gm-news-copy').value)\">"
            f"Kopiera nyheter till papper</button>"
        )

    hp_items = []
    for item in llm.get("hp") or []:
        orsak = item.get("orsak") or ""
        extra = f" — {escape(orsak)}" if orsak else ""
        hp_items.append(
            f'<li><strong>{escape(item.get("lag") or "")}</strong> '
            f'{escape(_signed_delta(item.get("delta")))} HP{extra}</li>'
        )
    hp_html = "".join(hp_items) or "<li>Inga HP-förslag.</li>"
    hp_primary_action = ""
    if llm.get("hp_applied"):
        hp_status = (
            '<div class="gm-llm-applied" role="status">'
            '<strong>✓ HP är schemalagda till nästa runda</strong>'
            '<span>Den här rundans kassa är oförändrad. Ångra i listen om utfallet ska göras om.</span>'
            '</div>'
        )
    elif llm.get("hp"):
        hp_status = ""
        hp_primary_action = (
            f'<form method="post" action="/admin/{sid}/llm_apply" class="d-inline gm-single-submit" '
            f"onsubmit=\"return confirm('Tillämpa HP till nästa runda? Går att ångra.');\">"
            f'<input type="hidden" name="op" value="hp">'
            f'<button type="submit" class="success sm">Tillämpa HP</button>'
            f"</form>"
        )
    else:
        hp_status = ""

    mile_items = []
    for item in llm.get("milstolpar") or []:
        orsak = item.get("orsak") or ""
        extra = f" — {escape(orsak)}" if orsak else ""
        mile_items.append(
            f'<li><strong>{escape(item.get("lag") or "")}</strong> / '
            f'{escape(item.get("etikett") or item.get("uppgift") or "")} '
            f'+{int(item.get("delta_hp") or 0)} HP{extra}</li>'
        )
    mile_html = "".join(mile_items) or "<li>Inga milstolpeförslag.</li>"
    milestones_handled = bool(llm.get("milestones_handled") or llm.get("milestones_applied"))
    manual_status = llm.get("milestones_manual_status") or "none"
    mile_primary_action = ""
    if milestones_handled:
        handled_in_inbox = llm.get("milestones_applied_via") == "inbox" or (
            not llm.get("milestones_applied") and manual_status == "all"
        )
        heading = "✓ Milstolpar är hanterade i Inkorg" if handled_in_inbox else "✓ Milstolpar är tillämpade"
        mile_status = (
            '<div class="gm-llm-applied" role="status">'
            f'<strong>{heading}</strong>'
            '<span>Kan inte tillämpas igen. Ångra i listen om utfallet ska göras om.</span>'
            '</div>'
        )
    elif manual_status == "partial":
        mile_status = (
            '<div class="gm-llm-partial" role="status">'
            '<strong>Milstolpar är delvis hanterade i Inkorg</strong>'
            '<span>Slutför återstående aktiviteter där. Samlad tillämpning är avstängd för att undvika dubbelräkning.</span>'
            '<button type="button" class="secondary sm" data-show-tab="inkorg">Öppna Inkorg</button>'
            '</div>'
        )
    elif llm.get("milstolpar"):
        mile_status = ""
        mile_primary_action = (
            f'<form method="post" action="/admin/{sid}/llm_apply" class="d-inline gm-single-submit" '
            f"onsubmit=\"return confirm('Tillämpa milstolpeförslagen? Går att ångra.');\">"
            f'<input type="hidden" name="op" value="milstolpar">'
            f'<button type="submit" class="success sm">Tillämpa milstolpar</button>'
            f"</form>"
        )
    else:
        mile_status = ""

    primary_actions = "".join((hp_primary_action, mile_primary_action))
    action_bar = (
        '<div class="gm-llm-actions" aria-label="Åtgärder för LLM-resultat">'
        '<strong>Nästa steg</strong>'
        f'<div>{primary_actions}</div>'
        '</div>'
        if primary_actions else ""
    )

    counts = (
        ("Utfall", len(llm.get("utfall") or []), ""),
        ("Nyheter", len(llm.get("nyheter") or []), ""),
        ("HP", len(llm.get("hp") or []), "is-action" if llm.get("hp") and not llm.get("hp_applied") else ""),
        ("Milstolpar", len(llm.get("milstolpar") or []), "is-action" if llm.get("milstolpar") and not milestones_handled else ""),
    )
    summary = "".join(
        f'<span class="gm-llm-summary-item {tone}"><strong>{count}</strong>{escape(label)}</span>'
        for label, count, tone in counts
    )
    hp_open = " open" if llm.get("hp") and not llm.get("hp_applied") else ""
    mile_open = " open" if llm.get("milstolpar") and not milestones_handled else ""
    return f'''
      <div class="gm-llm-results" id="gm-llm-results">
        {warning_html}
        <div class="gm-llm-summary" aria-label="Sammanfattning av LLM-resultat">{summary}</div>
        {action_bar}
        <section class="gm-llm-result-section is-primary">
          <div class="gm-llm-result-heading"><h4>Utfall och sannolikhet</h4><span>{len(llm.get("utfall") or [])}</span></div>
          {utfall_html or '<p class="gm-muted">Inga sannolikhetsutfall.</p>'}
        </section>
        <details class="gm-llm-result-section">
          <summary><span>Nyheter till studion</span><span class="gm-llm-section-count">{len(llm.get("nyheter") or [])}</span></summary>
          <div class="gm-llm-result-body">{news_html}{news_copy_btn}</div>
        </details>
        <details class="gm-llm-result-section"{hp_open}>
          <summary><span>HP-konsekvenser</span><span class="gm-llm-section-count">{len(llm.get("hp") or [])}</span>{_tab_alert_html("Tillämpa förslaget") if hp_open else ""}</summary>
          <div class="gm-llm-result-body">
            <p class="gm-section-help">Ändrar kassan från nästa runda, inte den här rundans kvarvarande HP.</p>
            <ul class="gm-llm-list">{hp_html}</ul>{hp_status}
          </div>
        </details>
        <details class="gm-llm-result-section"{mile_open}>
          <summary><span>Backlog och milstolpar</span><span class="gm-llm-section-count">{len(llm.get("milstolpar") or [])}</span>{_tab_alert_html("Tillämpa förslaget") if mile_primary_action else ""}</summary>
          <div class="gm-llm-result-body"><ul class="gm-llm-list">{mile_html}</ul>{mile_status}</div>
        </details>
      </div>
    '''


def _chip_issue(team, inbox):
    status = team.get("status")
    rows = [row for row in inbox if row.get("team") == team.get("team")]
    if status == "draft":
        return "inte låst"
    if status not in ("submitted", "changed"):
        return ""
    if not rows:
        return "inskickad utan aktiviteter"
    notes = []
    if any(not str(row.get("aktivitet") or "").strip() for row in rows):
        notes.append("saknar aktivitet")
    if any(int(row.get("hp") or 0) <= 0 for row in rows):
        notes.append("saknar HP")
    return ", ".join(notes)


def _readiness_html(state):
    if state.get("fas") != "Orderfas":
        return ""
    teams = state.get("teams") or []
    inbox = state.get("inbox") or []
    chips = []
    missing = []
    drafts = []
    issues = []
    for team in teams:
        status = team.get("status") or "empty"
        name = team.get("team") or ""
        issue = _chip_issue(team, inbox)
        if status in ("empty", "draft"):
            missing.append(name)
        if status == "draft":
            drafts.append(name)
        if issue and status in ("submitted", "changed"):
            issues.append(f"{name}: {issue}")
        note = f'<span class="gm-chip-note">{escape(issue)}</span>' if issue else ""
        chips.append(
            f'<div class="gm-chip {_status_class(status)}" data-team="{escape(name)}">'
            f'<span class="gm-chip-name">{escape(name)}</span>'
            f'<span class="gm-chip-status">{escape(CHIP_LABELS.get(status, status))}</span>'
            f'<span class="gm-chip-hp">{int(team.get("effective") or 0)} HP</span>'
            f"{note}</div>"
        )
    if not missing and not issues:
        summary = "Alla order inne."
    else:
        parts = []
        if missing:
            parts.append(f"{len(missing)} lag utan inskickad order")
        if drafts:
            parts.append(f"{', '.join(drafts)} har utkast (inte låst)")
        parts.extend(issues)
        summary = " · ".join(parts)
    return (
        f'<div class="gm-readiness">'
        f'<div class="gm-chips">{"".join(chips)}</div>'
        f'<p class="gm-readiness-summary">{escape(summary)}</p>'
        f"</div>"
    )


def _fold_html(title, body):
    return (
        f'<details class="gm-fold">'
        f"<summary>{escape(title)}</summary>"
        f"{body}"
        f"</details>"
    )


CONSOLE_TABS = (
    ("inkorg", "Inkorg"),
    ("llm", "LLM-resultat"),
    ("lag", "Lag"),
    ("arbete", "Arbete"),
    ("historik", "Historik"),
)


def _tab_shell_html(default_tab, panels, alerts=None, counts=None):
    """Always-available views. Clock stays outside. No new URLs."""
    if default_tab not in panels:
        default_tab = "inkorg"
    alerts = alerts or {}
    counts = counts or {}
    buttons = []
    bodies = []
    for key, label in CONSOLE_TABS:
        if key not in panels:
            continue
        selected = key == default_tab
        needs = bool(alerts.get(key))
        alert = _tab_alert_html(alerts.get(key))
        count = (
            f'<span class="gm-tab-count">{int(counts[key])}</span>'
            if key in counts else ""
        )
        extra = " needs-action" if needs else ""
        buttons.append(
            f'<button type="button" class="app-tab gm-tab{extra}" role="tab" id="gm-tab-{key}" '
            f'data-tab="{key}" aria-controls="gm-panel-{key}" '
            f'aria-selected="{"true" if selected else "false"}" tabindex="{0 if selected else -1}">'
            f'{escape(label)}{count}{alert}</button>'
        )
        hidden = "" if selected else " hidden"
        bodies.append(
            f'<div class="app-tabpanel gm-tabpanel" role="tabpanel" id="gm-panel-{key}" '
            f'aria-labelledby="gm-tab-{key}"{hidden}>{panels[key]}</div>'
        )
    return (
        f'<div class="app-tabs gm-tabs" data-gm-tabs data-default="{escape(default_tab)}">'
        f'<div class="app-tablist gm-tablist" role="tablist" aria-label="Konsolvyer">'
        f"{''.join(buttons)}</div>"
        f"{''.join(bodies)}</div>"
    )


QUARTER_NAMES = ("Okt–Dec", "Jan–Mar", "Apr–Jun", "Jul–Sep")


def _quarter_strip_html(runda):
    try:
        runda = int(runda or 1)
    except (TypeError, ValueError):
        runda = 1
    pills = []
    for i, name in enumerate(QUARTER_NAMES, start=1):
        if i < runda:
            cls = "is-done"
        elif i == runda:
            cls = "is-current"
        else:
            cls = "is-future"
        pills.append(
            f'<div class="gm-quarter {cls}">'
            f'<span class="gm-quarter-round">Runda {i}</span>'
            f'<span class="gm-quarter-name">{escape(name)}</span>'
            f"</div>"
        )
    return f'<div class="gm-quarters" aria-label="Kvartalsförlopp">{"".join(pills)}</div>'


def _attention_lis(items):
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def live_html_fragments(spel_id, state):
    """HTML snippets the console can swap in without a full reload."""
    return {
        "attention": _attention_lis(attention_items(state)),
        "readiness": _readiness_html(state),
        "inbox": _inbox_html(
            spel_id,
            state.get("inbox") or [],
            state.get("fas"),
            state.get("test_mode"),
            state.get("runda") or 1,
        ),
        "backlog": _backlog_html(state.get("backlog") or [], state.get("avslutat")),
        "llm": _llm_block_html(spel_id, state),
        "log": _log_section_html(state.get("history") or [], state.get("log") or []),
    }


def create_gm_console_html(spel_id, data, llm_view=None, banner=""):
    state = build_live_state(data)
    runda = state["runda"]
    fas = state["fas"]
    remaining = state["remaining"]
    timer_status = state["timer_status"]
    avslutat = state["avslutat"]
    missing = state["missing_teams"]
    can_back = state["can_go_back"]
    undo_ok = state["undo_available"]
    test_mode = state["test_mode"]
    game_meta_html = _gm_game_meta_html(spel_id, data)
    round_orders = (data.get("team_orders") or {}).get(f"orders_round_{runda}") or {}
    app_menu_html = gm_app_menu_html(
        spel_id,
        test_mode,
        runda,
        bool(round_orders),
    )

    next_label = "Nästa fas"
    next_action = "next_fas"
    if fas == "Orderfas":
        next_label = "Nästa: Diplomatifas"
    elif fas == "Diplomatifas":
        next_label = "Nästa: Resultatfas"
    elif fas == "Resultatfas":
        if runda >= MAX_RUNDA:
            next_label = "Avsluta spelet"
            next_action = "end_game"
        else:
            next_label = "Starta nästa runda"
            next_action = "ny_runda"

    next_confirm = ""
    if next_action == "next_fas" and missing:
        next_confirm = (
            f"onsubmit=\"return confirm('Lag utan inskickad order: {escape(', '.join(missing))}. "
            f"De får inga ordrar. Fortsätt?');\""
        )
    elif next_action == "ny_runda":
        next_confirm = "onsubmit=\"return confirm('Starta nästa runda?');\""
    elif next_action == "end_game":
        next_confirm = "onsubmit=\"return confirm('Avsluta spelet?');\""

    back_disabled = "disabled" if not can_back or avslutat else ""
    undo_disabled = "disabled" if not undo_ok or avslutat else ""
    next_disabled = "disabled" if avslutat else ""
    timer_disabled = "disabled" if avslutat else ""

    attention = attention_items(state)

    attention_html = _attention_lis(attention)
    attention_hidden = "" if attention else " hidden"
    teams_html = _team_strip_html(spel_id, state["teams"], fas)
    inbox_html = _inbox_html(spel_id, state["inbox"], fas, test_mode, runda)
    readiness_html = _readiness_html(state)
    start_hidden = "hidden" if timer_status == "running" else ""
    pause_hidden = "hidden" if timer_status != "running" else ""
    clock_class = _clock_warn_class(remaining)
    backlog_html = _backlog_html(state["backlog"], avslutat)
    log_html = _log_section_html(state.get("history") or [], state["log"])
    llm_note = _llm_block_html(spel_id, state, default_result_tab=llm_view)
    llm_status = _llm_statusbar_html(spel_id, state)

    result_note = ""
    if fas == "Resultatfas" and avslutat:
        result_note = '<div class="gm-runofshow"><h3>Spelet är slut</h3></div>'
    elif fas == "Resultatfas":
        next_round_hint = (
            "Avsluta spelet (N eller knappen i listen)."
            if runda >= MAX_RUNDA
            else "Starta nästa runda (N eller knappen i listen). Går att ångra."
        )
        result_note = f'''
        <div class="gm-runofshow">
          <h3>Resultatfas — körschema</h3>
          {_quarter_strip_html(runda)}
          <ol>
            <li>
              <button type="button" class="primary" onclick="openTimerWindow('{escape(spel_id)}')">Öppna spelarskärm</button>
              så rummet ser tid och HP. Inga ordrar syns där.
            </li>
            <li>Läs nyheterna från studion. Rubriker och uppläsning finns i LLM-förslaget — kopiera till papper.</li>
            <li>Peka på HP på spelarskärmen.</li>
            <li>Peka på kvartalen här så rummet ser vilken runda ni är i.</li>
            <li>{escape(next_round_hint)}</li>
          </ol>
        </div>
        '''

    start_hint = ""
    if timer_status == "stopped" and not avslutat:
        start_hint = (
            f'<p class="gm-start-hint" id="gm-start-hint">'
            f'Tryck Starta (Space) för att sätta igång {escape(fas)}. '
            f'Spelarskärm visar tid och publik HP för rummet.</p>'
        )

    hp_body = (
        f'<p class="gm-section-help">Skriv hur många HP, sedan − eller +. '
        f'Överför flyttar mellan lag. Regeringsstöd är +10 ovanpå aktuell och kan inte flyttas.</p>'
        f'{teams_html}'
        f'{_transfer_form_html(spel_id, state["teams"])}'
    )

    if fas == "Orderfas":
        inbox_help = "Utkast syns här. Öppna för laget om de behöver skicka om."
    elif fas == "Diplomatifas":
        inbox_help = "Gå igenom order och konflikter. Lägg HP flyttar till backlog. Pennan rättar text/HP."
    else:
        inbox_help = "Order från rundan. Lägg HP flyttar till backlog vid behov."
    inbox_inner = (
        f'<p class="gm-section-help">{inbox_help}</p>'
        f'<div id="gm-inbox-root">{inbox_html}</div>'
    )
    backlog_body = (
        f'<p class="gm-section-help">Sätt HP per klick i kolumnen, sedan − / + på en roadmap-uppgift. '
        f'Egna aktiviteter (t.ex. CI/CD) ligger i orderinkorgen, inte här.</p>'
        f'<p class="gm-backlog-legend" aria-hidden="true">'
        f'<span class="gm-backlog-swatch is-prev"></span> förra rundan '
        f'<span class="gm-backlog-swatch is-add"></span> tillagt den här rundan '
        f'<span class="gm-backlog-swatch is-lost"></span> draget den här rundan'
        f'</p>'
        f'<div id="gm-backlog-root">{backlog_html}</div>'
    )
    log_body = (
        f'<p class="gm-section-help">Avklarade faser och GM-åtgärder i verktyget. Nyheter till studion ligger under LLM-förslag, inte här.</p>'
        f'<div id="gm-log-root">{log_html}</div>'
    )
    llm = state.get("llm") or {}
    tab_alerts = {}
    if fas == "Diplomatifas" and missing:
        tab_alerts["inkorg"] = "Lag utan inskickad order"
    elif state.get("inbox_action_count"):
        tab_alerts["inkorg"] = f"{state['inbox_action_count']} aktiviteter har HP att lägga"
    elif state.get("conflicts_require_review"):
        tab_alerts["inkorg"] = "Konflikter behöver bedömas"
    llm_actions = []
    if llm.get("hp") and not llm.get("hp_applied"):
        llm_actions.append("HP")
    if llm.get("milstolpar") and not llm.get("milestones_handled"):
        llm_actions.append("milstolpar")
    if llm_actions:
        tab_alerts["llm"] = " och ".join(llm_actions) + " att tillämpa"
    tab_panels = {
        "inkorg": f'<h3 class="gm-section-title">Orderinkorg</h3>{inbox_inner}',
        "lag": f'<h3 class="gm-section-title">Lag och handlingspoäng</h3>{hp_body}',
        "arbete": f'<h3 class="gm-section-title">Teamens arbete</h3>{backlog_body}',
        "historik": f'<h3 class="gm-section-title">Händelselogg</h3>{log_body}',
    }
    tab_counts = {}
    if fas in ("Diplomatifas", "Resultatfas"):
        tab_panels["llm"] = llm_note
        if _has_llm_import(llm):
            tab_counts["llm"] = sum(
                len(llm.get(key) or []) for key in ("utfall", "nyheter", "hp", "milstolpar")
            )
    default_tab = "lag" if fas == "Resultatfas" else "inkorg"
    if llm_view and "llm" in tab_panels:
        default_tab = "llm"
    tabs = _tab_shell_html(
        default_tab,
        tab_panels,
        tab_alerts,
        tab_counts,
    )
    if fas == "Orderfas":
        job_block = tabs
    elif fas == "Diplomatifas":
        job_block = f"{llm_status}{tabs}"
    else:
        job_block = f"{result_note}{llm_status}{tabs}"

    state_json = _json_for_script({
        "spel_id": spel_id,
        "remaining": remaining,
        "timer_status": timer_status,
        "fas": fas,
        "runda": runda,
        "avslutat": avslutat,
        "test_mode": bool(test_mode),
    })

    return f'''
    <div class="gm-console" id="gm-console">
      <script type="application/json" id="gm-state">{state_json}</script>
      <div class="gm-bar">
        <div class="gm-bar-main">
          <div class="gm-bar-now">
            <div class="gm-header-stat gm-header-round">
              <span class="gm-header-label">Runda</span>
              <strong class="gm-round">{runda}/{MAX_RUNDA}</strong>
            </div>
            <div class="gm-header-stat gm-header-phase">
              <span class="gm-header-label">Fas</span>
              <strong class="gm-phase" data-fas="{escape(fas)}">{escape(fas)}</strong>
            </div>
            <div class="gm-header-stat gm-header-timer">
              <span class="gm-header-label">Timer</span>
              <span class="gm-header-timer-line">
                <strong class="gm-clock{clock_class}" id="gm-clock">{_fmt_time(remaining)}</strong>
                <span class="gm-timer-badge is-{escape(timer_status)}" id="gm-timer-badge">{escape(_timer_status_label(timer_status))}</span>
              </span>
            </div>
          </div>
          <div class="gm-bar-context">{game_meta_html}</div>
          <button type="button" class="secondary gm-player-screen" onclick="openTimerWindow('{escape(spel_id)}')">Spelarskärm</button>
        </div>
        <div class="gm-bar-actions">
          <div class="gm-bar-phase">
            <form method="post" action="/admin/{escape(spel_id)}/timer" class="d-inline" id="gm-next-form" data-next-action="{next_action}" {next_confirm}>
              <button name="action" value="{next_action}" class="primary" {next_disabled}>{escape(next_label)}</button>
            </form>
            <form method="post" action="/admin/{escape(spel_id)}/timer" class="d-inline">
              <button name="action" value="prev_fas" class="secondary" {back_disabled}>Föregående</button>
            </form>
            <form method="post" action="/admin/{escape(spel_id)}/undo" class="d-inline">
              <button type="submit" class="secondary" data-gm-undo {undo_disabled}>Ångra</button>
            </form>
          </div>
          <div class="gm-bar-tools">
            <form method="post" action="/admin/{escape(spel_id)}/timer" class="gm-bar-time">
              <button name="action" value="start" class="success" {timer_disabled} {start_hidden}>Starta</button>
              <button name="action" value="pause" class="warning" {timer_disabled} {pause_hidden}>Pausa</button>
              <button name="action" value="add_min" class="secondary" {timer_disabled}>+1 min</button>
              <button name="action" value="sub_min" class="secondary" {timer_disabled}>−1 min</button>
              <button name="action" value="reset" class="secondary" {timer_disabled}
                onclick="return confirm('Nollställ timern till fasens fulla längd?');">Nollställ timer</button>
              <span class="gm-keys">Space starta/pausa · N nästa</span>
            </form>
            {app_menu_html}
          </div>
        </div>
      </div>

      {banner}

      <p class="gm-clock-hint" id="gm-clock-hint" hidden></p>
      {start_hint}

      <div class="gm-attention" id="gm-attention"{attention_hidden}>
        <div class="gm-attention-copy">
          <strong>Kräver uppmärksamhet</strong>
          <ul id="gm-attention-list">{attention_html}</ul>
        </div>
        <button type="button" class="secondary sm" data-show-tab="inkorg">Visa i Inkorg</button>
      </div>

      <div id="gm-readiness-root">{readiness_html}</div>
      <p class="gm-live-error" id="gm-live-error" hidden></p>

      {job_block}
    </div>
    '''


def _team_strip_html(spel_id, teams, fas):
    if not teams:
        return '<p class="text-muted">Inga lag.</p>'
    cards = []
    can_edit = fas in ("Orderfas", "Diplomatifas")
    for t in teams:
        support = "checked" if t["regeringsstod"] else ""
        remaining_class = "gm-hp-over" if t["remaining"] < 0 else ""
        bonus = " +10" if t["regeringsstod"] else ""
        if t["regeringsstod"]:
            transferable = f"överförbart {t['aktuell']} · stöd +10 kan inte flyttas"
        else:
            transferable = f"överförbart {t['aktuell']}"
        withdraw = ""
        if t.get("can_withdraw"):
            withdraw = (
                f'<button type="button" class="secondary gm-mini" data-order-withdraw '
                f'data-team="{escape(t["team"])}">Öppna för laget</button>'
            )
        edit_link = ""
        if can_edit:
            edit_link = (
                f'<a class="gm-edit-order secondary gm-mini" '
                f'href="/admin/{escape(spel_id)}/edit_order/{escape(t["team"])}">Redigera order</a>'
            )
        cards.append(f'''
        <div class="gm-team" data-team="{escape(t["team"])}">
          <div class="gm-team-head">
            <strong>{escape(t["team"])}</strong>
            <span class="gm-status {_status_class(t["status"])}">{escape(t["status_label"])}</span>
          </div>
          <div class="gm-hp {remaining_class}">
            <span class="gm-hp-label">Kvar att använda</span>
            <span class="gm-hp-now">{t["remaining"]}</span>
            <span class="gm-hp-sub gm-hp-budget">{t["effective"]} tillgängligt · {t["spent"]} lagt</span>
            <span class="gm-hp-sub gm-hp-aktuell">grundvärde {t["aktuell"]}{bonus}</span>
            <span class="gm-hp-sub gm-hp-transferable">{escape(transferable)}</span>
            <span class="gm-hp-next"{"" if t.get("pending_next") else " hidden"}>Nästa runda {escape(_signed_delta(t.get("pending_next")))}</span>
          </div>
          <form method="post" action="/admin/{escape(spel_id)}/hp" class="gm-hp-actions">
            <input type="hidden" name="team" value="{escape(t["team"])}">
            <input type="hidden" name="op" value="adjust">
            <div class="gm-stepper">
              <button type="submit" name="direction" value="minus" class="secondary gm-mini" data-hp-delta="-1">−</button>
              <input type="number" name="amount" min="1" value="1" class="gm-amount" inputmode="numeric" aria-label="HP-belopp">
              <button type="submit" name="direction" value="plus" class="secondary gm-mini" data-hp-delta="1">+</button>
            </div>
            <input type="text" name="reason" placeholder="Orsak" class="gm-reason">
          </form>
          <form method="post" action="/admin/{escape(spel_id)}/hp" class="gm-hp-support">
            <input type="hidden" name="team" value="{escape(t["team"])}">
            <input type="hidden" name="op" value="support">
            <label class="gm-support">
              <input type="checkbox" name="regeringsstod" value="on" {support} onchange="this.form.submit()">
              Stöd +10
            </label>
          </form>
          {withdraw}
          {edit_link}
        </div>
        ''')
    return '<div class="gm-teams">' + "".join(cards) + "</div>"


def _transfer_form_html(spel_id, teams):
    options = "".join(
        f'<option value="{escape(t["team"])}">{escape(t["team"])} '
        f'({t.get("transferable", t.get("aktuell", 0))} överförbart)</option>'
        for t in teams
    )
    return f'''
    <form method="post" action="/admin/{escape(spel_id)}/hp" class="gm-transfer">
      <input type="hidden" name="op" value="transfer">
      <label>Överför <input type="number" name="amount" min="1" value="5" class="gm-amount"></label>
      <label>från <select name="from_team">{options}</select></label>
      <label>till <select name="to_team">{options}</select></label>
      <input type="text" name="reason" placeholder="Orsak (spion, regering, förhandling…)" class="gm-reason-wide">
      <button type="submit" class="primary">Överför HP</button>
      <p class="gm-transfer-help">Bara aktuell HP kan flyttas. Regeringsstöd +10 följer inte med.</p>
    </form>
    '''


def _team_tone(name):
    return _TEAM_TONES.get((name or "").strip().lower(), "other")


def _group_inbox(inbox):
    groups = []
    index = {}
    for row in inbox:
        team = row.get("team") or ""
        if team not in index:
            index[team] = len(groups)
            groups.append({
                "team": team,
                "status": row.get("status") or "empty",
                "rows": [],
            })
        groups[index[team]]["rows"].append(row)
    return groups


def _activity_title(row):
    name = row.get("aktivitet") or ""
    if row.get("backlog_estimated"):
        name = _HP_SUFFIX.sub("", name).strip()
    return name or "—"


def _inbox_hp_html(row):
    hp = int(row.get("hp") or 0)
    est = row.get("backlog_estimated")
    try:
        est = int(est) if est is not None else None
    except (TypeError, ValueError):
        est = None
    if est and est != hp:
        return f'{hp} <span class="gm-inbox-hp-est">/ {est}</span> HP'
    return f"{hp} HP"


def _inbox_html(spel_id, inbox, fas, test_mode, runda=1):
    if not inbox:
        return (
            f'<div class="gm-inbox-wrap">'
            f'<p class="gm-empty">Inga ordrar ännu. Utkast dyker upp här när ett lag börjar skriva.</p></div>'
        )
    can_edit = fas in ("Orderfas", "Diplomatifas")
    show_apply = fas in ("Diplomatifas", "Resultatfas")
    rows = []
    for group in _group_inbox(inbox):
        team = group["team"]
        status = group["status"]
        team_actions = ""
        if can_edit:
            if status in ("submitted", "changed") and fas == "Orderfas":
                team_actions += (
                    f'<button type="button" class="warning gm-mini" data-order-withdraw '
                    f'data-team="{escape(team)}">Öppna för laget</button>'
                )
            team_actions += (
                f'<a class="gm-inbox-link" '
                f'href="/admin/{escape(spel_id)}/edit_order/{escape(team)}">Redigera</a>'
            )
        rows.append(f'''
        <tr class="gm-inbox-team">
          <td colspan="2">
            <div class="gm-inbox-team-line">
              <span class="gm-inbox-team-mark is-{escape(_team_tone(team))}">{escape(team)}</span>
              <span class="gm-status {_status_class(status)}">{escape(STATUS_LABELS.get(status, status))}</span>
            </div>
          </td>
          <td>
            <div class="gm-inbox-actions">{team_actions}</div>
          </td>
        </tr>
        ''')
        for row in group["rows"]:
            conflict = " gm-conflict" if row["conflict"] else ""
            typ = "Förstöra" if row["typ"] == "forstora" else "Bygga"
            typ_class = "is-break" if row["typ"] == "forstora" else "is-build"
            targets = ", ".join(row["paverkar"]) if row["paverkar"] else "—"
            actions = ""
            if show_apply and row.get("can_apply_backlog") and row.get("backlog_action") == "llm":
                actions += (
                    '<button type="button" class="secondary gm-mini" data-show-tab="llm">'
                    'Hantera i LLM-resultat</button>'
                )
            elif show_apply and row.get("can_apply_backlog"):
                actions += (
                    f'<button type="button" class="success gm-mini" data-backlog-apply '
                    f'data-team="{escape(row["team"])}" data-index="{row["index"]}">'
                    f'Lägg +{row["hp"]} HP</button>'
                )
            elif show_apply and row.get("backlog_applied"):
                actions += '<span class="gm-applied">Tillagd</span>'
            if can_edit:
                actions += (
                    f'<button type="button" class="gm-icon-btn" data-order-edit '
                    f'data-team="{escape(row["team"])}" data-index="{row["index"]}" '
                    f'data-aktivitet="{escape(row["aktivitet"])}" data-syfte="{escape(row["syfte"])}" '
                    f'data-hp="{row["hp"]}" aria-label="Ändra" title="Ändra">✎</button>'
                )
            rows.append(f'''
        <tr class="gm-inbox-activity-row{conflict}">
          <td>
            <div class="gm-inbox-activity">{escape(_activity_title(row))}</div>
            <div class="gm-inbox-purpose">{escape(row["syfte"]) or "—"}</div>
            <div class="gm-inbox-meta">
              <span class="gm-type-tag {typ_class}">{escape(typ)}</span>
              <span>{escape(targets)}</span>
            </div>
            {f'<span class="gm-conflict-tag">Konflikt</span>' if row["conflict"] else ""}
          </td>
          <td class="gm-inbox-hp">{_inbox_hp_html(row)}</td>
          <td>
            <div class="gm-inbox-actions">{actions}</div>
          </td>
        </tr>
            ''')
    return f'''
    <div class="gm-inbox-wrap">
      <table class="gm-inbox">
        <thead>
          <tr>
            <th>Aktivitet</th><th>HP</th><th></th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </div>
    '''


def _spend_buttons(team, task_id, phase="", disabled=""):
    phase_attr = f' data-phase="{escape(phase)}"' if phase else ""
    return (
        f'<button type="button" class="secondary gm-mini" data-backlog-delta="-1" '
        f'data-team="{escape(team)}" data-task="{escape(task_id)}"{phase_attr} {disabled}>−</button>'
        f'<button type="button" class="secondary gm-mini" data-backlog-delta="1" '
        f'data-team="{escape(team)}" data-task="{escape(task_id)}"{phase_attr} {disabled}>+</button>'
    )


def _backlog_progress_html(spent, estimated, label, previous=None):
    try:
        spent = max(0, int(spent or 0))
        estimated = max(0, int(estimated or 0))
        previous = max(0, int(previous or 0))
    except (TypeError, ValueError):
        spent = estimated = previous = 0
    kept = min(previous, spent)
    added = max(0, spent - previous)
    lost = max(0, previous - spent)
    def pct(value):
        return min(100, round(100 * value / estimated)) if estimated else 0
    kept_w = pct(kept)
    room = max(0, 100 - kept_w)
    add_w = min(pct(added), room)
    lost_w = min(pct(lost), room)
    prev_html = (
        f'<span class="gm-backlog-prev" style="width:{kept_w}%"></span>'
        if kept_w else ""
    )
    add_html = (
        f'<span class="gm-backlog-add" style="left:{kept_w}%;width:{add_w}%"></span>'
        if add_w else ""
    )
    lost_html = (
        f'<span class="gm-backlog-lost" style="left:{kept_w}%;width:{lost_w}%"></span>'
        if lost_w else ""
    )
    return (
        f'<span class="gm-backlog-progress" role="progressbar" '
        f'aria-label="{escape(label)}: {spent} av {estimated} HP, förra rundan {previous}" '
        f'aria-valuemin="0" aria-valuemax="{estimated}" aria-valuenow="{min(spent, estimated)}">'
        f"{prev_html}{add_html}{lost_html}</span>"
    )


def _backlog_count_html(spent, estimated, previous=None):
    remaining = max(0, int(estimated or 0) - int(spent or 0))
    suffix = "klar" if estimated and remaining == 0 else f"{remaining} kvar"
    try:
        previous = int(previous) if previous is not None else None
    except (TypeError, ValueError):
        previous = None
    extra = ""
    if previous is not None:
        delta = int(spent or 0) - previous
        if previous == 0 and delta > 0:
            extra = f'<small class="gm-backlog-delta">+{delta} den här rundan</small>'
        elif delta > 0:
            extra = f'<small class="gm-backlog-delta">förra {previous} · +{delta} den här rundan</small>'
        elif delta < 0:
            extra = f'<small class="gm-backlog-delta">förra {previous} · {delta} den här rundan</small>'
        elif previous:
            extra = f'<small class="gm-backlog-delta">förra {previous} · oförändrat</small>'
    return f'{int(spent or 0)} / {int(estimated or 0)} HP <small>{suffix}</small>{extra}'


def _backlog_html(board, avslutat=False):
    if not board:
        return '<p class="gm-empty">Inga utvecklingsteam med backlog i det här spelet.</p>'
    disabled = "disabled" if avslutat else ""
    cards = []
    for team in board:
        rows = []
        for item in team.get("items") or []:
            done_class = " is-done" if item.get("done") else ""
            recurring = ' <span class="gm-recurring">återkommande</span>' if item.get("recurring") else ""
            if item.get("kind") == "phased":
                rows.append(
                    f'<div class="gm-backlog-item{done_class}">'
                    f'<div class="gm-backlog-parent"><span class="gm-backlog-name">'
                    f'<strong>{escape(item["name"])}</strong>'
                    f'{_backlog_progress_html(item["spent"], item["estimated"], item["name"], item.get("previous"))}</span>'
                    f'<span class="gm-backlog-count">{_backlog_count_html(item["spent"], item["estimated"], item.get("previous"))}</span></div>'
                )
                for phase in item.get("phases") or []:
                    phase_done = " is-done" if phase.get("done") else ""
                    rows.append(
                        f'<div class="gm-backlog-row gm-backlog-phase{phase_done}">'
                        f'<span class="gm-backlog-name">{escape(phase["name"])}'
                        f'{_backlog_progress_html(phase["spent"], phase["estimated"], phase["name"], phase.get("previous"))}</span>'
                        f'<span class="gm-backlog-count">{_backlog_count_html(phase["spent"], phase["estimated"], phase.get("previous"))}</span>'
                        f'<span class="gm-backlog-btns">{_spend_buttons(team["team"], item["id"], phase["name"], disabled)}</span>'
                        f'</div>'
                    )
                rows.append("</div>")
            else:
                progress = "" if item.get("recurring") else _backlog_progress_html(
                    item["spent"], item["estimated"], item["name"], item.get("previous")
                )
                rows.append(
                    f'<div class="gm-backlog-row{done_class}">'
                    f'<span class="gm-backlog-name">{escape(item["name"])}{recurring}{progress}</span>'
                    f'<span class="gm-backlog-count">{_backlog_count_html(item["spent"], item["estimated"], item.get("previous"))}</span>'
                    f'<span class="gm-backlog-btns">{_spend_buttons(team["team"], item["id"], "", disabled)}</span>'
                    f'</div>'
                )
        cards.append(
            f'<section class="gm-backlog-team" data-team="{escape(team["team"])}">'
            f'<h4>{escape(team["team"])} '
            f'<span class="gm-hp-sub">{_backlog_count_html(team["spent"], team["estimated"], team.get("previous"))}</span></h4>'
            f'<label class="gm-backlog-stepper">HP per klick '
            f'<input type="number" min="1" value="1" class="gm-amount gm-backlog-amount" '
            f'data-team="{escape(team["team"])}" {disabled} aria-label="HP per klick {escape(team["team"])}">'
            f'</label>'
            f'{"".join(rows)}</section>'
        )
    return f'<div class="gm-backlog">{"".join(cards)}</div>'


def _history_html(history):
    if not history:
        return ""
    rounds = {}
    order = []
    for entry in history:
        runda = entry.get("runda")
        if runda not in rounds:
            rounds[runda] = []
            order.append(runda)
        status = entry.get("status") or ""
        if status == "pågående":
            cls = "is-now"
            label = "pågår"
        else:
            cls = "is-done"
            label = "klar"
        fas = entry.get("fas") or ""
        rounds[runda].append(
            f'<span class="gm-history-fas {cls}">{escape(fas)} '
            f'<span class="gm-history-state">{label}</span></span>'
        )
    blocks = []
    for runda in order:
        blocks.append(
            f'<div class="gm-history-round">'
            f'<strong>Runda {escape(str(runda))}</strong>'
            f'{"".join(rounds[runda])}'
            f"</div>"
        )
    return f'<div class="gm-history">{"".join(blocks)}</div>'


def _log_section_html(history, log):
    return _history_html(history) + _log_html(log)


def _log_html(log):
    if not log:
        return '<p class="text-muted">Inga GM-åtgärder ännu.</p>'
    items = []
    for entry in log:
        items.append(f'<li><span class="gm-log-kind">{escape(entry.get("kind") or "")}</span> {escape(entry.get("message") or "")}</li>')
    return f'<ul class="gm-log">{"".join(items)}</ul>'


def _projector_hp_change(delta):
    delta = int(delta or 0)
    if delta > 0:
        return " is-gain", f"+{delta} HP"
    if delta < 0:
        return " is-loss", f"−{abs(delta)} HP"
    return " is-same", "Oförändrat"


def _projector_hp_html(teams, show_next=False):
    cards = []
    for t in teams or []:
        extra = " has-support" if t.get("regeringsstod") else ""
        note = '<div class="projector-team-note">stöd +10</div>' if t.get("regeringsstod") else ""
        hp_html = f'<div class="projector-team-hp">{t["hp"]}</div>'
        aria = f'{escape(t["team"])}: {t["hp"]} HP'
        if show_next:
            change_class, change_label = _projector_hp_change(t.get("next_delta"))
            extra += change_class
            aria = (
                f'{escape(t["team"])}: denna runda {t["hp"]} HP, '
                f'nästa runda {t.get("next_hp", t["hp"])} HP, {escape(change_label)}'
            )
            hp_html = (
                '<div class="projector-team-comparison">'
                '<div class="projector-team-period">'
                '<span>Denna runda</span>'
                f'<strong>{t["hp"]}</strong></div>'
                '<span class="projector-team-arrow" aria-hidden="true">→</span>'
                '<div class="projector-team-period is-next">'
                '<span>Nästa runda</span>'
                f'<strong>{t.get("next_hp", t["hp"])}</strong></div>'
                '</div>'
                f'<div class="projector-team-change">{escape(change_label)}</div>'
            )
        cards.append(
            f'<div class="projector-team{extra}" aria-label="{aria}">'
            f'<div class="projector-team-name">{escape(t["team"])}</div>'
            f'{hp_html}'
            f"{note}</div>"
        )
    return "".join(cards)


def _projector_progress_tone(percent):
    percent = max(0, min(100, int(percent or 0)))
    if percent >= 67:
        return "is-high"
    if percent >= 34:
        return "is-medium"
    return "is-low"


def _projector_bar(percent, extra_class=""):
    width = max(0, min(100, int(percent or 0)))
    done = " is-done" if width >= 100 else ""
    tone = _projector_progress_tone(width)
    extra = f" {extra_class}" if extra_class else ""
    return (
        f'<div class="projector-bar {tone}{done}{extra}" role="progressbar" '
        f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{width}">'
        f'<span style="width:{width}%"></span></div>'
    )


def _projector_progress_html(progress):
    if not progress:
        return ""
    cards = []
    for team in progress:
        cards.append(
            f'<section class="projector-progress-card">'
            f'<div class="projector-progress-head">'
            f'<div class="projector-progress-team">{escape(team["team"])}</div>'
            f'<div class="projector-progress-total">{team.get("percent", 0)}% · '
            f'{team.get("spent", 0)}/{team.get("estimated", 0)} HP</div>'
            f"</div>"
            f'{_projector_bar(team.get("percent"), "is-team")}'
            f"</section>"
        )
    return (
        '<h2 class="projector-progress-title">Teamens arbete</h2>'
        f'<div class="projector-progress-grid">{"".join(cards)}</div>'
    )


def _projector_clock_class(remaining):
    remaining = int(remaining or 0)
    if remaining <= 30:
        return " is-danger is-critical"
    if remaining <= 60:
        return " is-danger"
    if remaining <= 300:
        return " is-warning"
    return ""


def create_projector_html(spel_id, data):
    """Player-facing display: round, phase, time, public HP. No GM controls."""
    state = build_public_state(data)
    show_next_hp = (
        state["fas"] == "Resultatfas"
        and state["runda"] < state["max_runda"]
        and not state["avslutat"]
    )
    team_cards = _projector_hp_html(state["teams"], show_next=show_next_hp)
    progress_html = _projector_progress_html(state.get("progress") or [])
    ended = " Spelet är slut." if state["avslutat"] else ""
    clock_class = _projector_clock_class(state["remaining"])
    state_json = _json_for_script({"spel_id": spel_id, **state})
    return f'''<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Spelarskärm – runda {state["runda"]}</title>
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <link rel="stylesheet" href="/static/app.css?v=45">
</head>
<body class="projector-page">
  <script type="application/json" id="projector-state">{state_json}</script>
  <div class="projector">
    <div class="projector-now">
      <div class="projector-round">Runda {state["runda"]}/{state["max_runda"]}</div>
      <div class="projector-phase">{escape(state["fas"])}</div>
      <div class="projector-clock{clock_class}" id="projector-clock">{_fmt_time(state["remaining"])}</div>
      <div class="projector-status" id="projector-status">{escape(_timer_status_label(state["timer_status"]))}{ended}</div>
    </div>
    <div class="projector-hp" id="projector-hp">{team_cards}</div>
    <div class="projector-progress" id="projector-progress">{progress_html}</div>
  </div>
  <button type="button" class="projector-audio-hint" id="projector-audio-hint" hidden>
    Klicka för ljudvarningar
  </button>
  <script src="/static/projector.js?v=5"></script>
</body>
</html>
'''
