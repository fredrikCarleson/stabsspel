/**
 * Live Game Master console: timer, keyboard, test mode.
 * News remain outside the app (LLM copy → paper → studio).
 */

(function () {
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

  function tickClock(state) {
    var clock = document.getElementById("gm-clock");
    if (!clock || !state) return;
    var remaining = state.remaining || 0;
    var running = state.timer_status === "running";

    function paint() {
      clock.textContent = formatTime(remaining);
      clock.classList.remove("is-warning", "is-danger");
      if (remaining <= 30) clock.classList.add("is-danger");
      else if (remaining <= 60) clock.classList.add("is-warning");
    }

    paint();
    setInterval(function () {
      if (running && remaining > 0) {
        remaining -= 1;
        paint();
      }
    }, 1000);
  }

  window.toggleGmTestMode = function (on) {
    var spelId = (readState() || {}).spel_id;
    if (!spelId) return;
    fetch("/admin/" + spelId + "/test_mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !!on }),
    }).then(function () {
      document.querySelectorAll(".cheat-link, .gm-autofill").forEach(function (el) {
        if (on) el.removeAttribute("hidden");
        else el.setAttribute("hidden", "hidden");
      });
      var label = document.querySelector(".gm-test");
      if (label) label.classList.toggle("is-on", !!on);
    });
  };

  document.addEventListener("keydown", function (event) {
    var tag = (event.target && event.target.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    var state = readState();
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
    }
  });

  var originalOpen = window.openTimerWindow;
  window.openTimerWindow = function (spelId) {
    var clock = document.getElementById("gm-clock") || document.getElementById("timer");
    var badge = document.getElementById("gm-timer-badge");
    if (clock) {
      var parts = (clock.textContent || "10:00").split(":");
      var total = parseInt(parts[0], 10) * 60 + parseInt(parts[1] || "0", 10);
      var status = badge ? badge.textContent.trim().toLowerCase() : "paused";
      var win = window.open(
        "/timer_window/" + spelId + "?time=" + total + "&status=" + encodeURIComponent(status),
        "timerWindow",
        "width=800,height=600,scrollbars=no,resizable=yes"
      );
      if (win) win.focus();
      return;
    }
    if (typeof originalOpen === "function") originalOpen(spelId);
  };

  tickClock(readState());
})();
