(() => {
  const $ = (sel) => document.querySelector(sel);
  const feedEl = $("#feed");
  const messageInput = $("#message-input");
  const messageForm = $("#message-form");
  const connectBtn = $("#connect-btn");
  const disconnectBtn = $("#disconnect-btn");
  const statusLight = $("#status-light");

  const state = {
    socket: null,
    liveEntry: null,
    buffer: "",
  };

  const setStatus = (text, connected) => {
    statusLight.textContent = text;
    statusLight.className = `status ${connected ? "status--connected" : "status--disconnected"}`;
  };

  const appendEntry = (role, text, live = false) => {
    const tpl = document.getElementById("entry-template");
    const entry = tpl.content.cloneNode(true);
    const meta = entry.querySelector(".entry-meta");
    const body = entry.querySelector(".entry-body");
    meta.textContent = role === "ai" ? "AI · Zephyr" : "You";
    meta.classList.add(role === "ai" ? "entry-meta--ai" : "entry-meta--user");
    const container = entry.querySelector(".entry");
    if (live) {
      container.classList.add("entry-live");
    }
    body.textContent = text;
    feedEl.prepend(entry);
    return feedEl.firstElementChild;
  };

  const ensureLiveEntry = () => {
    if (!state.liveEntry) {
      state.liveEntry = appendEntry("ai", "⏳ Waiting for response...", true);
    }
    return state.liveEntry.querySelector(".entry-body");
  };

  const finalizeLiveEntry = () => {
    if (state.liveEntry) {
      state.liveEntry.classList.remove("entry-live");
      state.liveEntry = null;
      state.buffer = "";
    }
  };

  const generateSessionId = () =>
    crypto.randomUUID ? crypto.randomUUID() : `session-${Date.now().toString(16)}`;

  $("#generate-session").addEventListener("click", () => {
    $("#session-input").value = generateSessionId();
  });

  const connect = () => {
    if (state.socket) return;
    const host = $("#host-input").value.trim();
    const sessionId = $("#session-input").value.trim() || generateSessionId();
    const userId = $("#user-input").value.trim() || "anonymous";

    $("#session-input").value = sessionId;
    const wsUrl = `${host.replace(/\/$/, "")}/ws/session/${sessionId}?user_id=${encodeURIComponent(
      userId
    )}`;

    const socket = new WebSocket(wsUrl);
    state.socket = socket;

    socket.addEventListener("open", () => {
      setStatus(`Connected to ${wsUrl}`, true);
      toggleControls(true);
    });

    socket.addEventListener("message", (event) => {
      if (event.data === "[END_OF_RESPONSE]") {
        finalizeLiveEntry();
        return;
      }

      // Ignore session-start JSON; only stream token text.
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.type === "session_started") {
          return;
        }
      } catch (_) {
        // not JSON
      }

      const liveBody = ensureLiveEntry();
      state.buffer += event.data;
      liveBody.textContent = state.buffer;
    });

    socket.addEventListener("close", () => {
      setStatus("Disconnected", false);
      toggleControls(false);
      state.socket = null;
      finalizeLiveEntry();
    });

    socket.addEventListener("error", (err) => {
      console.error("WebSocket error", err);
      setStatus("Connection error, see console.", false);
      socket.close();
    });
  };

  const disconnect = () => {
    if (state.socket) {
      state.socket.close(1000, "Client disconnect");
    }
  };

  const toggleControls = (connected) => {
    connectBtn.disabled = connected;
    disconnectBtn.disabled = !connected;
    messageInput.disabled = !connected;
    messageForm.querySelector("button").disabled = !connected;
  };

  messageForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) return;

    const content = messageInput.value.trim();
    if (!content) return;

    appendEntry("user", content);
    state.socket.send(JSON.stringify({ message: content }));
    messageInput.value = "";
    messageInput.focus();
  });

  connectBtn.addEventListener("click", connect);
  disconnectBtn.addEventListener("click", disconnect);
})();

