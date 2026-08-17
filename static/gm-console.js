/**
 * Live Game Master console: timer, keyboard, test mode, inbox poll, backlog.
 * News remain outside the app (LLM copy → paper → studio).
 */

(function () {
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
    if (badge && live.timer_status) badge.textContent = live.timer_status;
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
    root.querySelectorAll("[role=tab]").forEach(function (tab) {
      var on = tab.getAttribute("data-tab") === name;
      tab.setAttribute("aria-selected", on ? "true" : "false");
    });
    root.querySelectorAll("[role=tabpanel]").forEach(function (panel) {
      var on = panel.id === "gm-panel-" + name;
      if (on) panel.removeAttribute("hidden");
      else panel.setAttribute("hidden", "hidden");
    });
  }

  function bindTabs() {
    var root = document.querySelector(".gm-tabs");
    if (!root) return;
    root.addEventListener("click", function (event) {
      var tab = event.target.closest("[role=tab]");
      if (!tab || !root.contains(tab)) return;
      showConsoleTab(root, tab.getAttribute("data-tab"));
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
      var status = card.querySelector(".gm-status");
      if (status) {
        status.className = "gm-status " + (STATUS_CLASS[t.status] || "");
        status.textContent = t.status_label || t.status || "";
      }
      var hp = card.querySelector(".gm-hp");
      if (hp) hp.classList.toggle("gm-hp-over", t.remaining < 0);
      var now = card.querySelector(".gm-hp-now");
      if (now) now.textContent = t.effective;
      var aktuell = card.querySelector(".gm-hp-aktuell");
      if (aktuell) aktuell.textContent = "aktuell " + t.aktuell + (t.regeringsstod ? " +10" : "");
      var budget = card.querySelector(".gm-hp-budget");
      if (budget) budget.textContent = "lagt " + t.spent + " · kvar " + t.remaining;
      var xfer = card.querySelector(".gm-hp-transferable");
      if (xfer) {
        xfer.textContent = t.regeringsstod
          ? "överförbart " + t.aktuell + " · stöd +10 kan inte flyttas"
          : "överförbart " + t.aktuell;
      }
    });
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
    }
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
      test_mode: !!state.test_mode,
    });
    if (sig === lastPaint) return;
    lastPaint = sig;

    paintTeams(state.teams);
    paintNextConfirm(state);

    setHtml("gm-attention-list", html.attention);
    var attentionBox = document.getElementById("gm-attention");
    var attentionList = document.getElementById("gm-attention-list");
    if (attentionBox) {
      attentionBox.hidden = !attentionList || !attentionList.children.length;
    }
    if (html.readiness != null) setHtml("gm-readiness-root", html.readiness);
    setHtml("gm-inbox-root", html.inbox);
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

  function postHp(body) {
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
          paintLive(payload);
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
    cell = cell.parentNode;
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
    var hpDelta = target.closest("[data-hp-delta]");
    if (hpDelta) {
      event.preventDefault();
      var form = hpDelta.closest(".gm-hp-actions");
      if (!form) return;
      var amountEl = form.querySelector("[name=amount]");
      var reasonEl = form.querySelector("[name=reason]");
      var teamEl = form.querySelector("[name=team]");
      var sign = parseInt(hpDelta.getAttribute("data-hp-delta"), 10) < 0 ? -1 : 1;
      postHp({
        op: "adjust",
        team: teamEl ? teamEl.value : "",
        amount: sign * parseAmount(amountEl),
        reason: reasonEl ? reasonEl.value : "",
      });
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
  document.addEventListener("click", closeOpenMenus);
  tickClock();
  setInterval(poll, POLL_MS);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) poll();
  });
})();
