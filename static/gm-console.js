/**
 * Live Game Master console: timer, keyboard, test mode, inbox poll, backlog.
 * News remain outside the app (LLM copy → paper → studio).
 */

(function () {
  document.documentElement.classList.add("gm-js");
  var POLL_MS = 3000;
  var GM_WARN_S = 300;
  var GM_DANGER_S = 60;
  var CHIP_LABELS = {
    empty: "Saknas",
    draft: "Utkast",
    submitted: "Inne",
    changed: "Ändrad",
  };
  var STATUS_CLASS = {
    empty: "gm-status-empty",
    draft: "gm-status-draft",
    submitted: "gm-status-submitted",
    changed: "gm-status-changed",
  };
  var TIMER_LABELS = {
    running: "Pågår",
    paused: "Pausad",
    stopped: "Inte startad",
  };
  var live = null;
  var inflight = false;
  var lastPaint = "";
  var writeGen = 0;
  var editing = false;
  var testModePending = false;

  function readState() {
    var el = document.getElementById("gm-state");
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      return null;
    }
  }

  function formatTime(seconds) {
    seconds = Math.max(0, Math.floor(seconds));
    var min = Math.floor(seconds / 60);
    var sec = seconds % 60;
    return (min < 10 ? "0" : "") + min + ":" + (sec < 10 ? "0" : "") + sec;
  }

  function paintClock() {
    var clock = document.getElementById("gm-clock");
    if (!clock || !live) return;
    var remaining = live.remaining || 0;
    clock.textContent = formatTime(remaining);
    clock.classList.remove("is-warning", "is-danger");
    if (remaining <= GM_DANGER_S) clock.classList.add("is-danger");
    else if (remaining <= GM_WARN_S) clock.classList.add("is-warning");
    var badge = document.getElementById("gm-timer-badge");
    if (badge && live.timer_status) {
      badge.textContent = TIMER_LABELS[live.timer_status] || live.timer_status;
      badge.className = "gm-timer-badge is-" + live.timer_status;
    }
    var hint = document.getElementById("gm-clock-hint");
    if (hint) {
      hint.classList.remove("is-warning", "is-danger");
      if (live.timer_status === "running" && remaining <= GM_DANGER_S) {
        hint.hidden = false;
        hint.textContent = "1 minut kvar.";
        hint.classList.add("is-danger");
      } else if (live.timer_status === "running" && remaining <= GM_WARN_S) {
        hint.hidden = false;
        hint.textContent = "5 minuter kvar.";
        hint.classList.add("is-warning");
      } else {
        hint.hidden = true;
        hint.textContent = "";
      }
    }
    var startBtn = document.querySelector('.gm-bar-time [value="start"]');
    var pauseBtn = document.querySelector('.gm-bar-time [value="pause"]');
    if (startBtn && pauseBtn) {
      var running = live.timer_status === "running";
      startBtn.hidden = running;
      pauseBtn.hidden = !running;
      startBtn.className = running ? "success" : "primary";
      var nextBtn = document.querySelector('#gm-next-form [name="action"]');
      if (nextBtn) nextBtn.className = running ? "primary" : "secondary";
    }
  }

  function tickClock() {
    paintClock();
    setInterval(function () {
      if (live && live.timer_status === "running" && live.remaining > 0) {
        live.remaining -= 1;
        paintClock();
      }
    }, 1000);
  }

  function showError(message) {
    var el = document.getElementById("gm-live-error");
    if (!el) return;
    if (!message) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = message;
  }

  function applyTestModeUi(on) {
    var box = document.getElementById("gm-test-mode");
    if (box) box.checked = !!on;
    var hidden = document.getElementById("gm-test-enabled");
    if (hidden) hidden.value = on ? "1" : "0";
    var label = document.querySelector(".gm-test");
    if (label) label.classList.toggle("is-on", !!on);
    document.querySelectorAll(".gm-autofill").forEach(function (el) {
      if (on) el.removeAttribute("hidden");
      else el.setAttribute("hidden", "hidden");
    });
  }

  function bindTestMode() {
    var form = document.getElementById("gm-test-form");
    var box = document.getElementById("gm-test-mode");
    if (!form || !box) return;
    box.removeAttribute("onchange");
    box.addEventListener("change", function () {
      var on = box.checked;
      var spelId = (live || readState() || {}).spel_id;
      var hidden = document.getElementById("gm-test-enabled");
      if (hidden) hidden.value = on ? "1" : "0";
      if (!spelId) {
        form.submit();
        return;
      }
      testModePending = true;
      applyTestModeUi(on);
      fetch("/admin/" + spelId + "/test_mode", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ enabled: !!on }),
      })
        .then(function (res) {
          if (!res.ok) throw new Error("test_mode " + res.status);
          return res.json();
        })
        .then(function (payload) {
          testModePending = false;
          if (!payload || !payload.success) throw new Error("test_mode");
          applyTestModeUi(!!payload.test_mode);
          if (live) live.test_mode = !!payload.test_mode;
        })
        .catch(function () {
          testModePending = false;
          form.submit();
        });
    });
  }

  function closeOpenMenus(event) {
    document.querySelectorAll("details.gm-menu[open]").forEach(function (menu) {
      if (!menu.contains(event.target)) menu.removeAttribute("open");
    });
  }

  function showConsoleTab(root, name) {
    if (!root || !name) return;
    var activePanelId = "";
    root.querySelectorAll("[role=tab]").forEach(function (tab) {
      var on = tab.getAttribute("data-tab") === name;
      tab.setAttribute("aria-selected", on ? "true" : "false");
      tab.tabIndex = on ? 0 : -1;
      if (on) activePanelId = tab.getAttribute("aria-controls") || "";
    });
    root.querySelectorAll("[role=tabpanel]").forEach(function (panel) {
      var on = panel.id === activePanelId;
      if (on) panel.removeAttribute("hidden");
      else panel.setAttribute("hidden", "hidden");
    });
  }

  function bindTabs() {
    document.querySelectorAll("[data-gm-tabs]").forEach(function (root) {
      root.addEventListener("click", function (event) {
        var tab = event.target.closest("[role=tab]");
        if (!tab || !root.contains(tab)) return;
        showConsoleTab(root, tab.getAttribute("data-tab"));
      });
      root.addEventListener("keydown", function (event) {
        var tabs = Array.prototype.slice.call(root.querySelectorAll("[role=tab]"));
        var index = tabs.indexOf(event.target.closest("[role=tab]"));
        if (index < 0 || !tabs.length) return;
        var next = null;
        if (event.key === "ArrowRight") next = tabs[(index + 1) % tabs.length];
        if (event.key === "ArrowLeft") next = tabs[(index - 1 + tabs.length) % tabs.length];
        if (event.key === "Home") next = tabs[0];
        if (event.key === "End") next = tabs[tabs.length - 1];
        if (!next) return;
        event.preventDefault();
        showConsoleTab(root, next.getAttribute("data-tab"));
        next.focus();
      });
    });

    document.addEventListener("click", function (event) {
      var trigger = event.target.closest("[data-show-tab]");
      if (!trigger) return;
      var root = document.querySelector("[data-gm-tabs]");
      if (!root) return;
      showConsoleTab(root, trigger.getAttribute("data-show-tab"));
      var active = root.querySelector('[role=tab][aria-selected="true"]');
      if (active) active.focus();
      root.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function bindHpDrafts() {
    document.addEventListener("submit", function (event) {
      var form = event.target.closest && event.target.closest("[data-hp-apply-form]");
      if (!form) return;
      event.preventDefault();
      var amountEl = form.querySelector("[data-hp-amount]");
      var total = parseDraft(amountEl);
      var delta = total - parseBaseline(amountEl);
      if (!delta) {
        syncApplyButton(form);
        return;
      }
      var lastingEl = form.querySelector("[name=lasting]");
      var lasting = !!(lastingEl && lastingEl.value === "1");
      var teamEl = form.querySelector("[name=team]");
      var reasonEl = form.querySelector("[name=reason]");
      postHp({
        op: "adjust",
        team: teamEl ? teamEl.value : "",
        amount: delta,
        reason: reasonEl ? reasonEl.value : "",
        duration: lasting ? "lasting" : "temp",
        lasting: lasting,
      }, form);
    });
    document.addEventListener("input", function (event) {
      var form = event.target.closest && event.target.closest("[data-hp-apply-form]");
      if (!form || !event.target.hasAttribute("data-hp-amount")) return;
      syncApplyButton(form);
    });
    document.addEventListener("focusout", function (event) {
      if (!event.target || !event.target.hasAttribute("data-hp-amount")) return;
      event.target.value = formatDraft(parseDraft(event.target));
      syncApplyButton(event.target.closest("[data-hp-apply-form]"));
    });
  }

  function bindSingleSubmitForms() {
    document.addEventListener("submit", function (event) {
      var form = event.target.closest && event.target.closest("form.gm-single-submit");
      if (!form || event.defaultPrevented) return;
      if (form.getAttribute("data-submitting") === "true") {
        event.preventDefault();
        return;
      }
      form.setAttribute("data-submitting", "true");
      var button = event.submitter || form.querySelector('button[type="submit"]');
      if (button) {
        button.disabled = true;
        button.textContent = "Tillämpar…";
      }
    });
  }

  function paintTeams(teams) {
    (teams || []).forEach(function (t) {
      var chip = document.querySelector('.gm-chip[data-team="' + t.team + '"]');
      if (chip) {
        chip.className = "gm-chip " + (STATUS_CLASS[t.status] || "");
        var chipStatus = chip.querySelector(".gm-chip-status");
        if (chipStatus) chipStatus.textContent = CHIP_LABELS[t.status] || t.status_label || t.status || "";
        var chipHp = chip.querySelector(".gm-chip-hp");
        if (chipHp) chipHp.textContent = t.effective + " HP";
      }
      var card = document.querySelector('.gm-team[data-team="' + t.team + '"]');
      if (!card) return;
      var pending = parseInt(t.pending_next, 10) || 0;
      card.classList.toggle("is-gain", pending > 0);
      card.classList.toggle("is-loss", pending < 0);
      var status = card.querySelector(".gm-status");
      if (status) {
        status.className = "gm-status " + (STATUS_CLASS[t.status] || "");
        status.textContent = t.status_label || t.status || "";
      }
      var nowHp = parseInt(t.aktuell, 10) || 0;
      var nextHp = t.next_hp == null ? nowHp : parseInt(t.next_hp, 10);
      if (isNaN(nextHp)) nextHp = nowHp;
      var now = card.querySelector(".gm-hp-now");
      if (now) now.textContent = nowHp;
      var hpBlock = card.querySelector(".gm-hp");
      if (hpBlock) {
        hpBlock.setAttribute(
          "aria-label",
          nextHp === nowHp ? "HP nu " + nowHp : "HP nu " + nowHp + ", nästa runda " + nextHp
        );
      }
      var to = card.querySelector(".gm-hp-to");
      if (to) {
        to.hidden = nextHp === nowHp;
        to.classList.toggle("is-gain", pending > 0);
        to.classList.toggle("is-loss", pending < 0);
      }
      var next = card.querySelector(".gm-hp-next");
      if (next) next.textContent = nextHp;
      var budget = card.querySelector(".gm-hp-budget");
      if (budget) budget.textContent = "lagt " + t.spent + " av " + t.effective;
      card.querySelectorAll("[data-hp-apply-form]").forEach(function (form) {
        var lastingEl = form.querySelector("[name=lasting]");
        var lasting = !!(lastingEl && lastingEl.value === "1");
        var amountEl = form.querySelector("[data-hp-amount]");
        if (!amountEl) return;
        if (parseDraft(amountEl) !== parseBaseline(amountEl)) return;
        setLayerTotal(form, layerTotal(t, lasting));
      });
    });
  }

  function setTabAlert(id, text) {
    var tab = document.getElementById(id);
    if (!tab) return;
    var badge = tab.querySelector(".gm-tab-alert");
    if (text) {
      tab.classList.add("needs-action");
      if (!badge) {
        badge = document.createElement("span");
        badge.className = "gm-tab-alert";
        badge.textContent = "Att göra";
        tab.appendChild(badge);
      }
      badge.title = text;
    } else {
      tab.classList.remove("needs-action");
      if (badge) badge.remove();
    }
  }

  function paintTabAlerts(state) {
    var fas = state.fas || "";
    var missing = state.missing_teams || [];
    var inkorg = "";
    if (fas === "Diplomatifas" && missing.length) {
      inkorg = "Lag utan inskickad order";
    } else if (state.inbox_action_count) {
      inkorg = state.inbox_action_count + " aktiviteter har HP att lägga";
    } else if (state.conflicts_require_review) {
      inkorg = "Konflikter behöver bedömas";
    }
    setTabAlert("gm-tab-inkorg", inkorg);

    var llm = state.llm || {};
    var actions = [];
    if (llm.hp && llm.hp.length && !llm.hp_applied) actions.push("HP");
    if (llm.milstolpar && llm.milstolpar.length && !llm.milestones_handled) {
      actions.push("milstolpar");
    }
    var missingUtfall = llm.missing_utfall || [];
    if (missingUtfall.length) {
      var missingLabel = missingUtfall.length === 1
        ? "1 order saknar utfall"
        : missingUtfall.length + " order saknar utfall";
      setTabAlert(
        "gm-tab-llm",
        actions.length ? missingLabel + " · " + actions.join(" och ") + " att tillämpa" : missingLabel
      );
    } else {
      setTabAlert("gm-tab-llm", actions.length ? actions.join(" och ") + " att tillämpa" : "");
    }
    setTabAlert("gm-tab-lag", "");
    setTabAlert("gm-tab-arbete", "");
  }

  function paintNextConfirm(state) {
    var form = document.getElementById("gm-next-form");
    if (!form) return;
    var action = form.getAttribute("data-next-action");
    var missing = state.missing_teams || [];
    if (action === "next_fas" && missing.length) {
      form.onsubmit = function () {
        return confirm(
          "Lag utan inskickad order: " + missing.join(", ") + ". De får inga ordrar. Fortsätt?"
        );
      };
    } else if (action === "next_fas") {
      form.onsubmit = null;
    }
  }

  function parseBaseline(el) {
    var n = parseInt(el && el.getAttribute("data-hp-baseline"), 10);
    return isNaN(n) ? 0 : n;
  }

  function layerTotal(t, lasting) {
    var editNow = live && live.fas === "Orderfas";
    var raw = lasting
      ? (editNow ? t.varaktigt : t.next_varaktigt)
      : (editNow ? t.tillfalligt : t.next_tillfalligt);
    var n = parseInt(raw, 10);
    return isNaN(n) ? 0 : n;
  }

  function setLayerTotal(form, total) {
    var amountEl = form.querySelector("[data-hp-amount]");
    var baselineEl = form.querySelector("[name=baseline]");
    if (amountEl) {
      amountEl.value = formatDraft(total);
      amountEl.setAttribute("data-hp-baseline", String(total));
    }
    if (baselineEl) baselineEl.value = String(total);
    syncApplyButton(form);
  }

  function parseDraft(el) {
    var n = parseInt(String((el && el.value) || "").replace("+", ""), 10);
    return isNaN(n) ? 0 : n;
  }

  function formatDraft(n) {
    n = parseInt(n, 10);
    if (isNaN(n) || n === 0) return "0";
    return n > 0 ? "+" + n : String(n);
  }

  function syncApplyButton(form) {
    if (!form) return;
    var btn = form.querySelector("[data-hp-apply]");
    var amountEl = form.querySelector("[data-hp-amount]");
    if (!btn || !amountEl) return;
    var dirty = parseDraft(amountEl) !== parseBaseline(amountEl);
    form.classList.toggle("is-dirty", dirty);
    btn.disabled = !dirty;
  }

  function resetHpDraft(form) {
    if (!form) return;
    var amountEl = form.querySelector("[data-hp-amount]");
    var reasonEl = form.querySelector("[name=reason]");
    if (reasonEl) reasonEl.value = "";
    if (amountEl) setLayerTotal(form, parseDraft(amountEl));
    else syncApplyButton(form);
  }

  function parseAmount(el) {
    var n = parseInt(el && el.value, 10);
    if (!n || n < 1) return 1;
    return n;
  }

  function readBacklogAmounts() {
    var amounts = {};
    document.querySelectorAll(".gm-backlog-amount").forEach(function (el) {
      var team = el.getAttribute("data-team");
      if (team) amounts[team] = el.value;
    });
    return amounts;
  }

  function restoreBacklogAmounts(amounts) {
    Object.keys(amounts || {}).forEach(function (team) {
      var el = document.querySelector('.gm-backlog-amount[data-team="' + team + '"]');
      if (el && amounts[team]) el.value = amounts[team];
    });
  }

  function backlogAmountFocused() {
    var active = document.activeElement;
    return !!(active && active.classList && active.classList.contains("gm-backlog-amount"));
  }

  function setHtml(id, html) {
    var el = document.getElementById(id);
    if (!el || html == null) return;
    if (el.innerHTML !== html) el.innerHTML = html;
  }

  function paintLive(payload) {
    var state = payload.state || payload;
    var html = payload.html || {};
    if (!state) return;

    if (
      live &&
      (live.fas !== state.fas || live.runda !== state.runda || !!live.avslutat !== !!state.avslutat)
    ) {
      window.location.reload();
      return;
    }

    live.remaining = state.remaining;
    live.timer_status = state.timer_status;
    live.fas = state.fas;
    live.runda = state.runda;
    live.avslutat = state.avslutat;
    paintClock();

    var sig = JSON.stringify({
      inbox: state.inbox,
      teams: state.teams,
      backlog: state.backlog,
      missing: state.missing_teams,
      log: state.log,
      undo: state.undo_available,
      conflicts: state.conflict_count,
      conflictsRequireReview: !!state.conflicts_require_review,
      inboxActions: state.inbox_action_count,
      test_mode: !!state.test_mode,
      llm: state.llm,
    });
    if (sig === lastPaint) return;
    lastPaint = sig;

    paintTeams(state.teams);
    paintTabAlerts(state);
    paintNextConfirm(state);

    setHtml("gm-attention-list", html.attention);
    var attentionBox = document.getElementById("gm-attention");
    var attentionList = document.getElementById("gm-attention-list");
    if (attentionBox) {
      attentionBox.hidden = !attentionList || !attentionList.children.length;
    }
    if (html.readiness != null) setHtml("gm-readiness-root", html.readiness);
    setHtml("gm-inbox-root", html.inbox);
    if (html.llm != null) setHtml("gm-panel-llm", html.llm);
    var backlogAmounts = readBacklogAmounts();
    if (!backlogAmountFocused()) {
      setHtml("gm-backlog-root", html.backlog);
      restoreBacklogAmounts(backlogAmounts);
    }
    setHtml("gm-log-root", html.log);

    var undo = document.querySelector("[data-gm-undo]");
    if (undo) undo.disabled = !state.undo_available || !!state.avslutat;

    if (!testModePending) {
      live.test_mode = !!state.test_mode;
      applyTestModeUi(!!state.test_mode);
    }
  }

  function poll() {
    if (!live || !live.spel_id || inflight || editing || document.hidden) return;
    inflight = true;
    var gen = writeGen;
    fetch("/admin/" + live.spel_id + "/live", { headers: { Accept: "application/json" } })
      .then(function (res) {
        if (!res.ok) throw new Error("live " + res.status);
        return res.json();
      })
      .then(function (payload) {
        if (gen !== writeGen) return;
        if (payload && payload.success) paintLive(payload);
      })
      .catch(function () {})
      .then(function () {
        inflight = false;
      });
  }

  function flashHpSaved(form) {
    if (!form) return;
    var btn = form.querySelector("[data-hp-apply]");
    if (!btn) return;
    var original = btn.getAttribute("data-label") || "Verkställ";
    btn.setAttribute("data-label", original);
    btn.textContent = "Sparat";
    form.classList.add("is-saved");
    window.clearTimeout(form._hpSavedTimer);
    form._hpSavedTimer = window.setTimeout(function () {
      if (!btn.isConnected) return;
      btn.textContent = original;
      form.classList.remove("is-saved");
    }, 2000);
  }

  function postHp(body, form) {
    if (!live || !live.spel_id || inflight) return;
    showError("");
    writeGen += 1;
    inflight = true;
    fetch("/admin/" + live.spel_id + "/hp", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (res) {
        return res.json().then(function (payload) {
          payload._http = res.status;
          return payload;
        });
      })
      .then(function (payload) {
        if (payload && payload.success) {
          resetHpDraft(form);
          paintLive(payload);
          flashHpSaved(form);
          return;
        }
        showError((payload && payload.error) || "Kunde inte uppdatera HP.");
      })
      .catch(function () {
        showError("Kunde inte uppdatera HP.");
      })
      .then(function () {
        inflight = false;
      });
  }

  function postBacklog(body) {
    if (!live || !live.spel_id || inflight) return;
    showError("");
    writeGen += 1;
    inflight = true;
    fetch("/admin/" + live.spel_id + "/backlog_live", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (res) {
        return res.json().then(function (payload) {
          payload._http = res.status;
          return payload;
        });
      })
      .then(function (payload) {
        if (payload && payload.success) {
          paintLive(payload);
          return;
        }
        showError((payload && payload.error) || "Kunde inte uppdatera backlog.");
      })
      .catch(function () {
        showError("Kunde inte uppdatera backlog.");
      })
      .then(function () {
        inflight = false;
      });
  }

  function postOrder(body) {
    if (!live || !live.spel_id || inflight) return;
    showError("");
    writeGen += 1;
    inflight = true;
    editing = false;
    fetch("/admin/" + live.spel_id + "/order_live", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (res) {
        return res.json().then(function (payload) {
          payload._http = res.status;
          return payload;
        });
      })
      .then(function (payload) {
        if (payload && payload.success) {
          paintLive(payload);
          return;
        }
        showError((payload && payload.error) || "Kunde inte uppdatera order.");
      })
      .catch(function () {
        showError("Kunde inte uppdatera order.");
      })
      .then(function () {
        inflight = false;
      });
  }

  function beginOrderEdit(btn) {
    var row = btn.closest("tr");
    var cell = row && row.querySelector(".gm-inbox-activity");
    if (!cell) return;
    cell = cell.closest("td") || cell.parentNode;
    editing = true;
    var team = btn.getAttribute("data-team");
    var index = btn.getAttribute("data-index");
    cell.innerHTML =
      '<form class="gm-inline-edit">' +
      '<input type="text" name="aktivitet" value="' +
      (btn.getAttribute("data-aktivitet") || "").replace(/"/g, "&quot;") +
      '" placeholder="Aktivitet">' +
      '<input type="number" name="hp" min="0" value="' +
      (btn.getAttribute("data-hp") || "0") +
      '" class="gm-amount">' +
      '<input type="text" name="syfte" value="' +
      (btn.getAttribute("data-syfte") || "").replace(/"/g, "&quot;") +
      '" placeholder="Syfte">' +
      '<button type="submit" class="primary gm-mini">Spara</button>' +
      '<button type="button" class="secondary gm-mini" data-order-cancel>Avbryt</button>' +
      "</form>";
    var form = cell.querySelector(".gm-inline-edit");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      postOrder({
        op: "edit",
        team: team,
        index: parseInt(index, 10),
        aktivitet: form.aktivitet.value,
        hp: form.hp.value,
        syfte: form.syfte.value,
      });
    });
  }

  window.toggleGmTestMode = function (on) {
    var box = document.getElementById("gm-test-mode");
    if (box) {
      box.checked = !!on;
      box.dispatchEvent(new Event("change"));
    }
  };

  document.addEventListener("keydown", function (event) {
    var tag = (event.target && event.target.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    var state = live || readState();
    if (!state) return;

    if (event.code === "Space") {
      event.preventDefault();
      var action = state.timer_status === "running" ? "pause" : "start";
      var form = document.createElement("form");
      form.method = "post";
      form.action = "/admin/" + state.spel_id + "/timer";
      var input = document.createElement("input");
      input.type = "hidden";
      input.name = "action";
      input.value = action;
      form.appendChild(input);
      document.body.appendChild(form);
      form.submit();
      return;
    }

    if ((event.key === "n" || event.key === "N") && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      var next = document.getElementById("gm-next-form");
      if (next) {
        if (typeof next.requestSubmit === "function") next.requestSubmit();
        else next.submit();
      }
    }
  });

  document.addEventListener("click", function (event) {
    var target = event.target;
    if (!target || !target.closest) return;
    var withdraw = target.closest("[data-order-withdraw]");
    if (withdraw) {
      event.preventDefault();
      if (!confirm("Öppna ordern så laget kan ändra och skicka igen under orderfasen?")) return;
      postOrder({ op: "withdraw", team: withdraw.getAttribute("data-team") });
      return;
    }
    var edit = target.closest("[data-order-edit]");
    if (edit) {
      event.preventDefault();
      beginOrderEdit(edit);
      return;
    }
    var cancel = target.closest("[data-order-cancel]");
    if (cancel) {
      event.preventDefault();
      editing = false;
      lastPaint = "";
      poll();
      return;
    }
      var hpNudge = target.closest("[data-hp-nudge]");
    if (hpNudge) {
      event.preventDefault();
      var form = hpNudge.closest("[data-hp-apply-form]");
      if (!form) return;
      var amountEl = form.querySelector("[data-hp-amount]");
      if (!amountEl) return;
      var step = parseInt(hpNudge.getAttribute("data-hp-nudge"), 10) || 0;
      amountEl.value = formatDraft(parseDraft(amountEl) + step);
      syncApplyButton(form);
      return;
    }
    var apply = target.closest("[data-backlog-apply]");
    if (apply) {
      event.preventDefault();
      postBacklog({
        op: "apply_order",
        team: apply.getAttribute("data-team"),
        index: parseInt(apply.getAttribute("data-index"), 10),
      });
      return;
    }
    var delta = target.closest("[data-backlog-delta]");
    if (delta) {
      event.preventDefault();
      var team = delta.getAttribute("data-team");
      var amountEl = document.querySelector('.gm-backlog-amount[data-team="' + team + '"]');
      var sign = parseInt(delta.getAttribute("data-backlog-delta"), 10) < 0 ? -1 : 1;
      postBacklog({
        op: "add",
        team: team,
        task_id: delta.getAttribute("data-task"),
        phase: delta.getAttribute("data-phase") || "",
        amount: sign * parseAmount(amountEl),
      });
    }
  });

  window.openTimerWindow = function (spelId) {
    var win = window.open(
      "/spelarskarm/" + spelId,
      "playerDisplay",
      "width=1100,height=720,scrollbars=yes,resizable=yes"
    );
    if (win) win.focus();
  };

  live = readState();
  if (!live) return;
  bindTestMode();
  bindTabs();
  bindSingleSubmitForms();
  bindHpDrafts();
  document.querySelectorAll("[data-hp-apply-form]").forEach(syncApplyButton);
  document.addEventListener("click", closeOpenMenus);
  tickClock();
  setInterval(poll, POLL_MS);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) poll();
  });
})();
