"""
HTML for the Game Master live console.

News still happen outside the app (LLM copy → paper headlines → studio).
This UI keeps that copy step first-class and puts orders, HP, time, and
phase control on one screen.
"""

from markupsafe import escape
import json
from gm_console import STATUS_LABELS, build_live_state, build_public_state
from models import MAX_RUNDA


def _fmt_time(seconds):
    seconds = max(0, int(seconds or 0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


CHIP_LABELS = {
    "empty": "Saknas",
    "draft": "Utkast",
    "submitted": "Inne",
    "changed": "Ändrad",
}

GM_CLOCK_WARN_S = 300
GM_CLOCK_DANGER_S = 60


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
    ("lag", "Lag"),
    ("arbete", "Arbete"),
    ("historik", "Historik"),
)


def _tab_shell_html(default_tab, panels):
    """Always-available views. Clock stays outside. No new URLs."""
    if default_tab not in panels:
        default_tab = "inkorg"
    buttons = []
    bodies = []
    for key, label in CONSOLE_TABS:
        selected = key == default_tab
        buttons.append(
            f'<button type="button" class="gm-tab" role="tab" id="gm-tab-{key}" '
            f'data-tab="{key}" aria-controls="gm-panel-{key}" '
            f'aria-selected="{"true" if selected else "false"}">{escape(label)}</button>'
        )
        hidden = "" if selected else " hidden"
        bodies.append(
            f'<div class="gm-tabpanel" role="tabpanel" id="gm-panel-{key}" '
            f'aria-labelledby="gm-tab-{key}"{hidden}>{panels[key]}</div>'
        )
    return (
        f'<div class="gm-tabs" data-default="{escape(default_tab)}">'
        f'<div class="gm-tablist" role="tablist" aria-label="Konsolvyer">'
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
        "inbox": _inbox_html(spel_id, state.get("inbox") or [], state.get("fas"), state.get("test_mode")),
        "backlog": _backlog_html(state.get("backlog") or [], state.get("avslutat")),
        "log": _log_section_html(state.get("history") or [], state.get("log") or []),
    }


def create_gm_console_html(spel_id, data):
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
        next_confirm = "onsubmit=\"return confirm('Starta nästa runda? Det går att ångra.');\""
    elif next_action == "end_game":
        next_confirm = "onsubmit=\"return confirm('Avsluta spelet?');\""
    else:
        next_confirm = "onsubmit=\"return confirm('Gå till nästa fas? Det går att ångra.');\""

    back_disabled = "disabled" if not can_back or avslutat else ""
    undo_disabled = "disabled" if not undo_ok or avslutat else ""
    next_disabled = "disabled" if avslutat else ""
    timer_disabled = "disabled" if avslutat else ""

    attention = attention_items(state)

    attention_html = _attention_lis(attention)
    attention_hidden = "" if attention else " hidden"
    teams_html = _team_strip_html(spel_id, state["teams"], fas)
    inbox_html = _inbox_html(spel_id, state["inbox"], fas, test_mode)
    readiness_html = _readiness_html(state)
    start_hidden = "hidden" if timer_status == "running" else ""
    pause_hidden = "hidden" if timer_status != "running" else ""
    clock_class = _clock_warn_class(remaining)
    backlog_html = _backlog_html(state["backlog"], avslutat)
    log_html = _log_section_html(state.get("history") or [], state["log"])
    llm_note = ""
    if fas in ("Diplomatifas", "Resultatfas"):
        llm_note = f'''
        <div class="gm-llm">
            <div>Kopiera ordrar till LLM. Rubriker skrivs på papper, inte här.</div>
            <a href="/admin/{escape(spel_id)}/order_summary" target="_blank" class="primary">Kopiera ordrar till LLM</a>
        </div>
        '''

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
            <li>Läs nyheterna från studion. Rubrikerna finns på papper, inte i det här verktyget.</li>
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
        inbox_help = "Gå igenom order och konflikter. Ändra rättar text/HP. Lägg HP flyttar till backlog."
    else:
        inbox_help = "Order från rundan. Lägg HP flyttar till backlog vid behov."
    inbox_inner = (
        f'<p class="gm-section-help">{inbox_help}</p>'
        f'<div id="gm-inbox-root">{inbox_html}</div>'
    )
    backlog_body = (
        f'<p class="gm-section-help">Sätt HP per klick i kolumnen, sedan − / + på en roadmap-uppgift. '
        f'Egna aktiviteter (t.ex. CI/CD) ligger i orderinkorgen, inte här.</p>'
        f'<div id="gm-backlog-root">{backlog_html}</div>'
    )
    log_body = (
        f'<p class="gm-section-help">Avklarade faser och GM-åtgärder i verktyget. Nyhetsrubriker hör hemma på väggen, inte här.</p>'
        f'<div id="gm-log-root">{log_html}</div>'
    )
    tabs = _tab_shell_html(
        "lag" if fas == "Resultatfas" else "inkorg",
        {
            "inkorg": f'<h3 class="gm-section-title">Orderinkorg</h3>{inbox_inner}',
            "lag": f'<h3 class="gm-section-title">Lag och handlingspoäng</h3>{hp_body}',
            "arbete": f'<h3 class="gm-section-title">Teamens arbete</h3>{backlog_body}',
            "historik": f'<h3 class="gm-section-title">Händelselogg</h3>{log_body}',
        },
    )
    if fas == "Orderfas":
        job_block = tabs
    elif fas == "Diplomatifas":
        job_block = f"{llm_note}{tabs}"
    else:
        job_block = f"{result_note}{llm_note}{tabs}"

    test_checked = "checked" if test_mode else ""
    test_class = "is-on" if test_mode else ""

    state_json = json.dumps({
        "spel_id": spel_id,
        "remaining": remaining,
        "timer_status": timer_status,
        "fas": fas,
        "runda": runda,
        "avslutat": avslutat,
        "test_mode": bool(test_mode),
    }, ensure_ascii=False)

    return f'''
    <div class="gm-console" id="gm-console">
      <script type="application/json" id="gm-state">{state_json}</script>
      <div class="gm-bar">
        <div class="gm-bar-now">
          <div class="gm-round">Runda {runda}/{MAX_RUNDA}</div>
          <div class="gm-phase" data-fas="{escape(fas)}">{escape(fas)}</div>
          <div class="gm-clock{clock_class}" id="gm-clock">{_fmt_time(remaining)}</div>
          <span class="gm-timer-badge" id="gm-timer-badge">{escape(timer_status)}</span>
        </div>
        <form method="post" action="/admin/{escape(spel_id)}/timer" class="gm-bar-time">
          <button name="action" value="start" class="success" {timer_disabled} {start_hidden}>Starta</button>
          <button name="action" value="pause" class="warning" {timer_disabled} {pause_hidden}>Pausa</button>
          <button name="action" value="add_min" class="secondary" {timer_disabled}>+1 min</button>
          <button name="action" value="sub_min" class="secondary" {timer_disabled}>−1 min</button>
          <button type="button" class="secondary" onclick="openTimerWindow('{escape(spel_id)}')">Spelarskärm</button>
          <span class="gm-keys">Space starta/pausa · N nästa</span>
        </form>
        <div class="gm-bar-phase">
          <form method="post" action="/admin/{escape(spel_id)}/timer" class="d-inline" id="gm-next-form" data-next-action="{next_action}" {next_confirm}>
            <button name="action" value="{next_action}" class="primary" {next_disabled}>{escape(next_label)}</button>
          </form>
          <form method="post" action="/admin/{escape(spel_id)}/undo" class="d-inline">
            <button type="submit" class="secondary" data-gm-undo {undo_disabled}>Ångra</button>
          </form>
          <details class="gm-menu">
            <summary aria-haspopup="menu">Meny</summary>
            <div class="gm-mer-menu" role="menu">
              <form method="post" action="/admin/{escape(spel_id)}/timer">
                <button name="action" value="reset" class="secondary" {timer_disabled}
                  onclick="return confirm('Nollställ timern till fasens fulla längd?');">Nollställ timer</button>
              </form>
              <form method="post" action="/admin/{escape(spel_id)}/timer">
                <button name="action" value="prev_fas" class="secondary" {back_disabled}
                  onclick="return confirm('Gå tillbaka till föregående fas?');">Föregående fas</button>
              </form>
              <form method="post" action="/admin/{escape(spel_id)}/test_mode" id="gm-test-form" class="gm-test-form">
                <input type="hidden" name="enabled" id="gm-test-enabled" value="{"1" if test_mode else "0"}">
                <label class="gm-test {test_class}">
                  <input type="checkbox" id="gm-test-mode" {test_checked}
                    onchange="this.form.querySelector('[name=enabled]').value=this.checked?'1':'0'; this.form.submit();">
                  Testläge
                </label>
              </form>
              <a href="/admin/{escape(spel_id)}/poang">HP-tabell</a>
              <a href="/admin/{escape(spel_id)}/backlog">Backlog</a>
              <a href="/admin/{escape(spel_id)}/aktivitetskort" target="_blank">Aktivitetskort</a>
              <a href="/admin/{escape(spel_id)}/order_summary" target="_blank">LLM-export</a>
              <a href="/admin">Alla spel</a>
              <form method="post" action="/admin/{escape(spel_id)}/reset"
                onsubmit="return confirm('Återställ HELA spelet till runda 1? Detta går att ångra en gång, men raderar rundor och ordrar.');">
                <button type="submit" class="danger">Återställ spel</button>
              </form>
            </div>
          </details>
        </div>
      </div>

      <p class="gm-clock-hint" id="gm-clock-hint" hidden></p>
      {start_hint}

      <div class="gm-attention" id="gm-attention"{attention_hidden}>
        <h3>Kräver uppmärksamhet</h3>
        <ul id="gm-attention-list">{attention_html}</ul>
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
            <span class="gm-hp-now">{t["effective"]}</span>
            <span class="gm-hp-sub gm-hp-aktuell">aktuell {t["aktuell"]}{bonus}</span>
            <span class="gm-hp-sub gm-hp-budget">lagt {t["spent"]} · kvar {t["remaining"]}</span>
            <span class="gm-hp-sub gm-hp-transferable">{escape(transferable)}</span>
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


def _inbox_html(spel_id, inbox, fas, test_mode):
    hidden_fill = "" if test_mode else "hidden"
    autofill = (
        f'<form method="post" action="/admin/{escape(spel_id)}/auto_fill_orders" '
        f'class="gm-autofill" {hidden_fill} '
        f'''onsubmit="return confirm('Ersätt alla ordrar med testdata?');">'''
        f'<button type="submit" class="warning">Auto-fyll testdata</button>'
        f'</form>'
    )
    if not inbox:
        return (
            f'<div class="gm-inbox-wrap">'
            f'<p class="gm-empty">Inga ordrar ännu. Utkast dyker upp här när ett lag börjar skriva.</p>'
            f'{autofill}</div>'
        )
    can_edit = fas in ("Orderfas", "Diplomatifas")
    seen_withdraw = set()
    seen_edit = set()
    rows = []
    for row in inbox:
        conflict = "gm-conflict" if row["conflict"] else ""
        typ = "Förstöra" if row["typ"] == "forstora" else "Bygga"
        targets = ", ".join(row["paverkar"]) if row["paverkar"] else "—"
        edit = ""
        if can_edit:
            edit = (
                f'<button type="button" class="secondary gm-mini" data-order-edit '
                f'data-team="{escape(row["team"])}" data-index="{row["index"]}" '
                f'data-aktivitet="{escape(row["aktivitet"])}" data-syfte="{escape(row["syfte"])}" '
                f'data-hp="{row["hp"]}">Ändra</button>'
            )
            if row["team"] not in seen_edit:
                seen_edit.add(row["team"])
                edit += (
                    f'<a class="secondary gm-mini" '
                    f'href="/admin/{escape(spel_id)}/edit_order/{escape(row["team"])}">Redigera order</a>'
                )
            if (
                row.get("status") in ("submitted", "changed")
                and fas == "Orderfas"
                and row["team"] not in seen_withdraw
            ):
                seen_withdraw.add(row["team"])
                edit += (
                    f'<button type="button" class="secondary gm-mini" data-order-withdraw '
                    f'data-team="{escape(row["team"])}">Öppna för laget</button>'
                )
        backlog_cell = "—"
        if row.get("can_apply_backlog"):
            backlog_cell = (
                f'<button type="button" class="secondary gm-mini" data-backlog-apply '
                f'data-team="{escape(row["team"])}" data-index="{row["index"]}">'
                f'Lägg +{row["hp"]} HP</button>'
            )
        elif row.get("backlog_applied"):
            backlog_cell = '<span class="gm-applied">Tillagd</span>'
        rows.append(f'''
        <tr class="{conflict}">
          <td>{escape(row["team"])}</td>
          <td><span class="gm-status {_status_class(row["status"])}">{escape(STATUS_LABELS.get(row["status"], row["status"]))}</span></td>
          <td>
            <div class="gm-inbox-activity">{escape(row["aktivitet"])}</div>
            <div class="gm-inbox-purpose">{escape(row["syfte"]) or "—"}</div>
            <div class="gm-inbox-meta">{escape(typ)} · {escape(targets)}</div>
            {f'<span class="gm-conflict-tag">Konflikt</span>' if row["conflict"] else ""}
          </td>
          <td class="gm-inbox-hp">{row["hp"]} HP</td>
          <td>
            <div class="gm-inbox-actions">{backlog_cell}{edit}</div>
          </td>
        </tr>
        ''')
    return f'''
    <div class="gm-inbox-wrap">
      <table class="gm-inbox">
        <thead>
          <tr>
            <th>Lag</th><th>Status</th><th>Aktivitet</th><th>HP</th><th></th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
      {autofill}
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
                    f'<strong>{escape(item["name"])}</strong></span>'
                    f'<span class="gm-backlog-count">{item["spent"]}/{item["estimated"]}</span></div>'
                )
                for phase in item.get("phases") or []:
                    phase_done = " is-done" if phase.get("done") else ""
                    rows.append(
                        f'<div class="gm-backlog-row gm-backlog-phase{phase_done}">'
                        f'<span class="gm-backlog-name">{escape(phase["name"])}</span>'
                        f'<span class="gm-backlog-count">{phase["spent"]}/{phase["estimated"]}</span>'
                        f'<span class="gm-backlog-btns">{_spend_buttons(team["team"], item["id"], phase["name"], disabled)}</span>'
                        f'</div>'
                    )
                rows.append("</div>")
            else:
                rows.append(
                    f'<div class="gm-backlog-row{done_class}">'
                    f'<span class="gm-backlog-name">{escape(item["name"])}{recurring}</span>'
                    f'<span class="gm-backlog-count">{item["spent"]}/{item["estimated"]}</span>'
                    f'<span class="gm-backlog-btns">{_spend_buttons(team["team"], item["id"], "", disabled)}</span>'
                    f'</div>'
                )
        cards.append(
            f'<section class="gm-backlog-team" data-team="{escape(team["team"])}">'
            f'<h4>{escape(team["team"])} '
            f'<span class="gm-hp-sub">{team["spent"]}/{team["estimated"]} HP</span></h4>'
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


def _projector_hp_html(teams):
    cards = []
    for t in teams or []:
        extra = " has-support" if t.get("regeringsstod") else ""
        note = '<div class="projector-team-note">stöd +10</div>' if t.get("regeringsstod") else ""
        cards.append(
            f'<div class="projector-team{extra}">'
            f'<div class="projector-team-name">{escape(t["team"])}</div>'
            f'<div class="projector-team-hp">{t["hp"]}</div>'
            f"{note}</div>"
        )
    return "".join(cards)


def _projector_bar(percent, extra_class=""):
    width = max(0, min(100, int(percent or 0)))
    done = " is-done" if width >= 100 else ""
    return (
        f'<div class="projector-bar{done} {extra_class}">'
        f'<span style="width:{width}%"></span></div>'
    )


def _projector_progress_html(progress):
    if not progress:
        return ""
    cards = []
    for team in progress:
        rows = []
        for item in team.get("items") or []:
            phases = ""
            if item.get("phases"):
                ticks = "".join(
                    f'<span class="{"is-done" if phase.get("done") else ""}">'
                    f'{escape(phase.get("name") or "")}</span>'
                    for phase in item["phases"]
                )
                phases = f'<div class="projector-phases">{ticks}</div>'
            done_class = " is-done" if item.get("done") else ""
            rows.append(
                f'<div class="projector-task{done_class}">'
                f'<span class="projector-task-name">{escape(item.get("name") or "")}</span>'
                f'<span class="projector-task-hp">{item.get("spent", 0)}/{item.get("estimated", 0)}</span>'
                f'{_projector_bar(item.get("percent"))}'
                f"{phases}</div>"
            )
        cards.append(
            f'<section class="projector-progress-card">'
            f'<div class="projector-progress-head">'
            f'<div class="projector-progress-team">{escape(team["team"])}</div>'
            f'<div class="projector-progress-total">{team.get("percent", 0)}% · '
            f'{team.get("spent", 0)}/{team.get("estimated", 0)} HP</div>'
            f"</div>"
            f'{_projector_bar(team.get("percent"), "is-team")}'
            f'{"".join(rows)}</section>'
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
    team_cards = _projector_hp_html(state["teams"])
    progress_html = _projector_progress_html(state.get("progress") or [])
    ended = " Spelet är slut." if state["avslutat"] else ""
    clock_class = _projector_clock_class(state["remaining"])
    state_json = json.dumps({"spel_id": spel_id, **state}, ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Spelarskärm – runda {state["runda"]}</title>
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <link rel="stylesheet" href="/static/app.css?v=13">
</head>
<body class="projector-page">
  <script type="application/json" id="projector-state">{state_json}</script>
  <div class="projector">
    <div class="projector-now">
      <div class="projector-round">Runda {state["runda"]}/{state["max_runda"]}</div>
      <div class="projector-phase">{escape(state["fas"])}</div>
      <div class="projector-clock{clock_class}" id="projector-clock">{_fmt_time(state["remaining"])}</div>
      <div class="projector-status" id="projector-status">{escape(state["timer_status"])}{ended}</div>
    </div>
    <div class="projector-hp" id="projector-hp">{team_cards}</div>
    <div class="projector-progress" id="projector-progress">{progress_html}</div>
  </div>
  <button type="button" class="projector-audio-hint" id="projector-audio-hint" hidden>
    Klicka för ljudvarningar
  </button>
  <script src="/static/projector.js?v=3"></script>
</body>
</html>
'''
