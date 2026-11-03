const elements = {
  connection: document.querySelector(".connection"),
  connectionLabel: document.querySelector("#connection-label"),
  modeLabel: document.querySelector("#mode-label"),
  idleMark: document.querySelector("#idle-mark"),
  lessonDisplay: document.querySelector("#lesson-display"),
  screenKind: document.querySelector("#screen-kind"),
  nkoDisplay: document.querySelector("#nko-display"),
  latinDisplay: document.querySelector("#latin-display"),
  englishDisplay: document.querySelector("#english-display"),
  recordingBanner: document.querySelector("#recording-banner"),
  talkButton: document.querySelector("#talk-button"),
  cardDeck: document.querySelector("#deck-card"),
  deckGlyph: document.querySelector(".deck-glyph"),
  deckTitle: document.querySelector(".deck-title"),
  cameraShutter: document.querySelector("#camera-shutter"),
  shutterCopy: document.querySelector(".shutter-copy"),
  micSwitch: document.querySelector("#mic-switch"),
  micLabel: document.querySelector("#mic-label"),
  lessonGrid: document.querySelector("#lesson-grid"),
  coachTitle: document.querySelector("#coach-title"),
  coachPrompt: document.querySelector("#coach-prompt"),
  responseLine: document.querySelector("#response-line"),
  expectedResponse: document.querySelector("#expected-response"),
  replayButton: document.querySelector("#replay-button"),
  audioStatus: document.querySelector("#audio-status"),
  resetButton: document.querySelector("#reset-button"),
  eventLabel: document.querySelector("#event-label"),
  revisionLabel: document.querySelector("#revision-label"),
};

let lessons = [];
let state = null;
let mediaStream = null;
let mediaRecorder = null;
let audioChunks = [];
let audioUrl = null;
let pointerHeld = false;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

async function load() {
  try {
    const [lessonPayload, statePayload] = await Promise.all([
      api("/api/lessons"),
      api("/api/state"),
    ]);
    lessons = lessonPayload.lessons;
    renderLessonOptions();
    renderState(statePayload);
    elements.connection.classList.add("online");
    elements.connectionLabel.textContent = "Local prototype connected";
  } catch (error) {
    elements.connectionLabel.textContent = "Local prototype unavailable";
    setAudioStatus(error.message, true);
  }
}

function renderLessonOptions() {
  elements.lessonGrid.replaceChildren();
  for (const lesson of lessons) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "lesson-option";
    button.dataset.cardId = lesson.card_id;
    button.setAttribute("aria-label", `Place lesson card: ${lesson.title}`);

    const kind = document.createElement("span");
    kind.className = "card-kind";
    kind.textContent = lesson.kind.toUpperCase();

    const nko = document.createElement("span");
    nko.className = "card-nko";
    nko.lang = "nqo";
    nko.dir = "rtl";
    nko.textContent = lesson.nko;

    const english = document.createElement("span");
    english.className = "card-english";
    english.textContent = lesson.english;

    button.append(kind, nko, english);
    button.addEventListener("click", () => selectCard(lesson.card_id));
    elements.lessonGrid.append(button);
  }
}

function renderState(nextState) {
  state = nextState;
  const lesson = state.lesson;
  elements.modeLabel.textContent = state.mode.replaceAll("_", " ").toUpperCase();
  elements.eventLabel.textContent = state.last_event;
  elements.revisionLabel.textContent = `REV ${state.revision}`;
  elements.recordingBanner.classList.toggle("hidden", !state.recording_indicator);
  elements.talkButton.classList.toggle("active", state.talk_active);
  elements.talkButton.disabled = !lesson || !state.mic_enabled;

  elements.cameraShutter.setAttribute("aria-pressed", String(state.camera_open));
  elements.cameraShutter.setAttribute(
    "aria-label",
    state.camera_open ? "Close camera shutter" : "Open camera shutter",
  );
  elements.shutterCopy.textContent = state.camera_open ? "CAMERA OPEN · NO CAPTURE" : "CAMERA CLOSED";

  const micLocked = !state.mic_enabled;
  elements.micSwitch.setAttribute("aria-pressed", String(micLocked));
  elements.micSwitch.setAttribute("aria-label", micLocked ? "Unlock microphone" : "Lock microphone");
  elements.micLabel.textContent = micLocked ? "LOCKED" : "READY";

  document.querySelectorAll(".lesson-option").forEach((button) => {
    button.classList.toggle("selected", button.dataset.cardId === state.selected_card_id);
    button.setAttribute("aria-pressed", String(button.dataset.cardId === state.selected_card_id));
  });

  if (!lesson) {
    elements.idleMark.classList.remove("hidden");
    elements.lessonDisplay.classList.add("hidden");
    elements.cardDeck.classList.remove("loaded");
    elements.deckGlyph.textContent = "ߒߞߏ";
    elements.deckTitle.textContent = "Choose a card";
    elements.coachTitle.textContent = "Start with a card";
    elements.coachPrompt.textContent =
      "Pick a greeting or letter. Jeli will show it on the face and unlock the talk button.";
    elements.responseLine.classList.add("hidden");
    return;
  }

  elements.idleMark.classList.add("hidden");
  elements.lessonDisplay.classList.remove("hidden");
  elements.screenKind.textContent = lesson.kind.toUpperCase();
  elements.nkoDisplay.textContent = lesson.nko;
  elements.latinDisplay.textContent = lesson.latin;
  elements.englishDisplay.textContent = lesson.english;
  elements.cardDeck.classList.add("loaded");
  elements.deckGlyph.textContent = lesson.nko;
  elements.deckTitle.textContent = lesson.title;
  elements.coachTitle.textContent = lesson.title;
  elements.coachPrompt.textContent = lesson.prompt;
  elements.expectedResponse.textContent = lesson.expected_response || "";
  elements.responseLine.classList.toggle("hidden", !lesson.expected_response);
}

async function selectCard(cardId) {
  try {
    stopLocalRecording();
    renderState(
      await api("/api/card", {
        method: "POST",
        body: JSON.stringify({ card_id: cardId }),
      }),
    );
    setAudioStatus("Card recognized. Hold the amber button when ready.");
  } catch (error) {
    setAudioStatus(error.message, true);
  }
}

async function ensureRecorder() {
  if (mediaStream && mediaStream.active) return;
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    throw new Error("This browser does not support local microphone recording.");
  }
  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
}

async function startTalking(event) {
  if (pointerHeld || elements.talkButton.disabled) return;
  if (event?.pointerId !== undefined) {
    elements.talkButton.setPointerCapture(event.pointerId);
  }
  pointerHeld = true;
  try {
    await ensureRecorder();
    audioChunks = [];
    mediaRecorder = new MediaRecorder(mediaStream);
    mediaRecorder.addEventListener("dataavailable", (item) => {
      if (item.data.size) audioChunks.push(item.data);
    });
    mediaRecorder.addEventListener("stop", finalizeAudio, { once: true });
    mediaRecorder.start();
    renderState(
      await api("/api/talk", {
        method: "POST",
        body: JSON.stringify({ active: true }),
      }),
    );
    setAudioStatus("Listening locally. Release the button to stop.");
  } catch (error) {
    pointerHeld = false;
    stopLocalRecording();
    setAudioStatus(error.message, true);
  }
}

async function stopTalking() {
  if (!pointerHeld) return;
  pointerHeld = false;
  stopLocalRecording();
  try {
    renderState(
      await api("/api/talk", {
        method: "POST",
        body: JSON.stringify({ active: false }),
      }),
    );
    setAudioStatus("Captured in this browser only. Replay or try again.");
  } catch (error) {
    setAudioStatus(error.message, true);
  }
}

function stopLocalRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
}

function finalizeAudio() {
  if (!audioChunks.length) return;
  if (audioUrl) URL.revokeObjectURL(audioUrl);
  const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
  audioUrl = URL.createObjectURL(blob);
  elements.replayButton.disabled = false;
}

async function togglePrivacy(key) {
  try {
    const payload = key === "camera"
      ? { camera_open: !state.camera_open }
      : { mic_enabled: !state.mic_enabled };
    if (key === "mic" && state.mic_enabled) {
      pointerHeld = false;
      stopLocalRecording();
    }
    renderState(
      await api("/api/privacy", { method: "POST", body: JSON.stringify(payload) }),
    );
    setAudioStatus(
      key === "camera"
        ? "Mechanical shutter state changed. Camera capture remains disabled."
        : state.mic_enabled
          ? "Microphone unlocked. It activates only while the button is held."
          : "Microphone privacy lock active.",
    );
  } catch (error) {
    setAudioStatus(error.message, true);
  }
}

async function resetPrototype() {
  pointerHeld = false;
  stopLocalRecording();
  if (audioUrl) URL.revokeObjectURL(audioUrl);
  audioUrl = null;
  elements.replayButton.disabled = true;
  try {
    renderState(await api("/api/reset", { method: "POST", body: "{}" }));
    setAudioStatus("Prototype reset. No audio leaves this browser.");
  } catch (error) {
    setAudioStatus(error.message, true);
  }
}

function setAudioStatus(message, isError = false) {
  elements.audioStatus.textContent = message;
  elements.audioStatus.style.color = isError ? "#ff9e8d" : "";
}

elements.talkButton.addEventListener("pointerdown", startTalking);
elements.talkButton.addEventListener("pointerup", stopTalking);
elements.talkButton.addEventListener("pointercancel", stopTalking);
elements.talkButton.addEventListener("lostpointercapture", stopTalking);
elements.cameraShutter.addEventListener("click", () => togglePrivacy("camera"));
elements.micSwitch.addEventListener("click", () => togglePrivacy("mic"));
elements.resetButton.addEventListener("click", resetPrototype);
elements.replayButton.addEventListener("click", () => {
  if (audioUrl) new Audio(audioUrl).play();
});

window.addEventListener("keydown", (event) => {
  if (event.code === "Space" && event.target === document.body && !event.repeat) {
    event.preventDefault();
    startTalking();
  }
});

window.addEventListener("keyup", (event) => {
  if (event.code === "Space" && event.target === document.body) {
    event.preventDefault();
    stopTalking();
  }
});

window.addEventListener("beforeunload", () => {
  if (audioUrl) URL.revokeObjectURL(audioUrl);
  mediaStream?.getTracks().forEach((track) => track.stop());
});

load();

