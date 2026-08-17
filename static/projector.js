/**
 * Player projector: round, phase, remaining time, public HP.
 * Polls a room-safe endpoint — no orders, log, or GM controls.
 * Audio: one chime at 5 min, one at 1 min, repeating alarm at 30s.
 */
(function () {
  var POLL_MS = 2000;
  var WARN_S = 300;
  var DANGER_S = 60;
  var CRITICAL_S = 30;
  var state = null;
  var audioCtx = null;
  var stressfulTimer = null;
  var alertsReady = false;
  var fired = { five: false, one: false };

  function readState() {
    var el = document.getElementById("projector-state");
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

  function remainingNow() {
    return state ? Math.max(0, state.remaining || 0) : 0;
  }

  function isRunning() {
    return !!(state && state.timer_status === "running" && !state.avslutat);
  }

  function paintClock() {
    var clock = document.getElementById("projector-clock");
    if (!clock || !state) return;
    var remaining = remainingNow();
    clock.textContent = formatTime(remaining);
    clock.classList.remove("is-warning", "is-danger", "is-critical");
    if (remaining <= CRITICAL_S) {
      clock.classList.add("is-danger", "is-critical");
    } else if (remaining <= DANGER_S) {
      clock.classList.add("is-danger");
    } else if (remaining <= WARN_S) {
      clock.classList.add("is-warning");
    }
  }

  function ensureAudio() {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    if (!audioCtx) audioCtx = new AC();
    if (audioCtx.state === "suspended") {
      audioCtx.resume().catch(function () {});
    }
    updateAudioHint();
    return audioCtx;
  }

  function updateAudioHint() {
    var hint = document.getElementById("projector-audio-hint");
    if (!hint) return;
    var locked = !audioCtx || audioCtx.state === "suspended";
    hint.hidden = !locked;
  }

  function beepAt(when, freq, duration, volume) {
    if (!audioCtx || audioCtx.state !== "running") return;
    var osc = audioCtx.createOscillator();
    var gain = audioCtx.createGain();
    osc.type = "triangle";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.0001, when);
    gain.gain.exponentialRampToValueAtTime(volume, when + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start(when);
    osc.stop(when + duration + 0.03);
  }

  function playFiveMin() {
    ensureAudio();
    if (!audioCtx || audioCtx.state !== "running") return;
    var t = audioCtx.currentTime;
    beepAt(t, 660, 0.32, 0.22);
    beepAt(t + 0.42, 660, 0.32, 0.22);
  }

  function playOneMin() {
    ensureAudio();
    if (!audioCtx || audioCtx.state !== "running") return;
    var t = audioCtx.currentTime;
    beepAt(t, 880, 0.16, 0.28);
    beepAt(t + 0.22, 880, 0.16, 0.28);
    beepAt(t + 0.44, 988, 0.28, 0.3);
  }

  function playThirtyTick() {
    ensureAudio();
    if (!audioCtx || audioCtx.state !== "running") return;
    var t = audioCtx.currentTime;
    beepAt(t, 1046, 0.1, 0.34);
    beepAt(t + 0.12, 1397, 0.16, 0.38);
  }

  function setStressful(on) {
    if (on) {
      if (stressfulTimer) return;
      playThirtyTick();
      stressfulTimer = setInterval(playThirtyTick, 900);
      return;
    }
    if (stressfulTimer) {
      clearInterval(stressfulTimer);
      stressfulTimer = null;
    }
  }

  function initAlertMemory() {
    var remaining = remainingNow();
    fired.five = remaining <= WARN_S;
    fired.one = remaining <= DANGER_S;
    alertsReady = true;
  }

  function syncAlerts() {
    if (!alertsReady || !state) return;
    var remaining = remainingNow();
    var running = isRunning();

    if (remaining > WARN_S) fired.five = false;
    if (remaining > DANGER_S) fired.one = false;

    if (running && remaining <= WARN_S && remaining > DANGER_S && !fired.five) {
      fired.five = true;
      playFiveMin();
    }
    if (running && remaining <= DANGER_S && remaining > CRITICAL_S && !fired.one) {
      fired.one = true;
      playOneMin();
    }
    setStressful(running && remaining <= CRITICAL_S && remaining > 0);
    if (running && remaining === 0) setStressful(false);
  }

  function barHtml(percent, extraClass) {
    var width = Math.max(0, Math.min(100, Math.round(percent || 0)));
    var done = width >= 100 ? " is-done" : "";
    extraClass = extraClass ? " " + extraClass : "";
    return (
      '<div class="projector-bar' + done + extraClass + '">' +
      '<span style="width:' + width + '%"></span></div>'
    );
  }

  function paintProgress(progress) {
    var root = document.getElementById("projector-progress");
    if (!root) return;
    if (!progress || !progress.length) {
      root.innerHTML = "";
      return;
    }
    var cards = progress
      .map(function (team) {
        var rows = (team.items || [])
          .map(function (item) {
            var phases = "";
            if (item.phases && item.phases.length) {
              phases =
                '<div class="projector-phases">' +
                item.phases
                  .map(function (phase) {
                    return (
                      '<span class="' +
                      (phase.done ? "is-done" : "") +
                      '">' +
                      escapeHtml(phase.name || "") +
                      "</span>"
                    );
                  })
                  .join("") +
                "</div>";
            }
            return (
              '<div class="projector-task' +
              (item.done ? " is-done" : "") +
              '">' +
              '<span class="projector-task-name">' +
              escapeHtml(item.name || "") +
              "</span>" +
              '<span class="projector-task-hp">' +
              (item.spent || 0) +
              "/" +
              (item.estimated || 0) +
              "</span>" +
              barHtml(item.percent) +
              phases +
              "</div>"
            );
          })
          .join("");
        return (
          '<section class="projector-progress-card">' +
          '<div class="projector-progress-head">' +
          '<div class="projector-progress-team">' +
          escapeHtml(team.team) +
          "</div>" +
          '<div class="projector-progress-total">' +
          (team.percent || 0) +
          "% · " +
          (team.spent || 0) +
          "/" +
          (team.estimated || 0) +
          " HP</div></div>" +
          barHtml(team.percent, "is-team") +
          rows +
          "</section>"
        );
      })
      .join("");
    root.innerHTML =
      '<h2 class="projector-progress-title">Teamens arbete</h2>' +
      '<div class="projector-progress-grid">' +
      cards +
      "</div>";
  }

  function paintHp(teams) {
    var root = document.getElementById("projector-hp");
    if (!root) return;
    root.innerHTML = (teams || [])
      .map(function (t) {
        var extra = t.regeringsstod ? " has-support" : "";
        var note = t.regeringsstod ? '<div class="projector-team-note">stöd +10</div>' : "";
        return (
          '<div class="projector-team' + extra + '">' +
          '<div class="projector-team-name">' + escapeHtml(t.team) + "</div>" +
          '<div class="projector-team-hp">' + t.hp + "</div>" +
          note +
          "</div>"
        );
      })
      .join("");
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function paint(next) {
    if (!next) return;
    var phaseEl = document.querySelector(".projector-phase");
    var roundEl = document.querySelector(".projector-round");
    var statusEl = document.getElementById("projector-status");
    if (roundEl) roundEl.textContent = "Runda " + next.runda + "/" + next.max_runda;
    if (phaseEl) phaseEl.textContent = next.fas;
    if (statusEl) {
      statusEl.textContent = next.avslutat ? "Spelet är slut" : next.timer_status || "";
    }
    state.remaining = next.remaining;
    state.timer_status = next.timer_status;
    state.fas = next.fas;
    state.runda = next.runda;
    state.avslutat = next.avslutat;
    paintClock();
    syncAlerts();
    paintHp(next.teams);
    paintProgress(next.progress);
  }

  function poll() {
    if (!state || !state.spel_id || document.hidden) return;
    fetch("/spelarskarm/" + state.spel_id + "/live", { headers: { Accept: "application/json" } })
      .then(function (res) {
        if (!res.ok) throw new Error("live " + res.status);
        return res.json();
      })
      .then(function (payload) {
        if (payload && payload.success) paint(payload.state);
      })
      .catch(function () {});
  }

  function unlockAudio() {
    ensureAudio();
  }

  state = readState();
  if (!state) return;
  initAlertMemory();
  paintClock();
  ensureAudio();
  setInterval(function () {
    if (state.timer_status === "running" && state.remaining > 0) {
      state.remaining -= 1;
      paintClock();
      syncAlerts();
    } else {
      setStressful(false);
    }
  }, 1000);
  setInterval(poll, POLL_MS);
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) setStressful(false);
    else poll();
  });
  document.addEventListener("click", unlockAudio);
  document.addEventListener("keydown", unlockAudio);
  document.addEventListener("touchstart", unlockAudio, { passive: true });
})();
