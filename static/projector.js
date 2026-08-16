/**
 * Player projector: round, phase, remaining time, public HP.
 * Polls a room-safe endpoint — no orders, log, or GM controls.
 */
(function () {
  var POLL_MS = 2000;
  var state = null;

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

  function paintClock() {
    var clock = document.getElementById("projector-clock");
    if (!clock || !state) return;
    clock.textContent = formatTime(state.remaining || 0);
    clock.classList.remove("is-warning", "is-danger");
    if ((state.remaining || 0) <= 30) clock.classList.add("is-danger");
    else if ((state.remaining || 0) <= 60) clock.classList.add("is-warning");
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
    paintHp(next.teams);
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

  state = readState();
  if (!state) return;
  paintClock();
  setInterval(function () {
    if (state.timer_status === "running" && state.remaining > 0) {
      state.remaining -= 1;
      paintClock();
    }
  }, 1000);
  setInterval(poll, POLL_MS);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) poll();
  });
})();
