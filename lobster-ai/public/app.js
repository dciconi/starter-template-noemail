// LobsterAI — Web Chat Client

const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const formEl = document.getElementById('chat-form');
const statusEl = document.getElementById('status');
const micBtn = document.getElementById('mic-btn');

let ws = null;
let sessionId = null;
let thinkingEl = null;

// ── WebSocket ────────────────────────────────────────────────────────────

function connect() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws`);

  ws.onopen = () => {
    setStatus('connected', 'connected');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'session') {
      sessionId = data.sessionId;
      return;
    }

    if (data.type === 'status') {
      showStatus(data.text);
      return;
    }

    if (data.type === 'transcription') {
      // Show the transcribed text as a user message
      addMessage('user', data.text);
      showThinking();
      return;
    }

    if (data.type === 'message') {
      removeThinking();
      addMessage('assistant', data.text);

      // Auto-speak if voice mode is on
      if (autoSpeak && window.speechSynthesis) {
        const stripped = data.text.replace(/[#*`_~\[\]()]/g, '').replace(/```[\s\S]*?```/g, '');
        const u = new SpeechSynthesisUtterance(stripped);
        speechSynthesis.speak(u);
      }
    }
  };

  ws.onclose = () => {
    setStatus('connecting', 'reconnecting...');
    setTimeout(connect, 2000);
  };

  ws.onerror = () => {
    setStatus('error', 'connection error');
  };
}

function setStatus(cls, text) {
  statusEl.className = `status status--${cls}`;
  statusEl.textContent = text;
}

// ── Messages ─────────────────────────────────────────────────────────────

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = `msg msg--${role}`;

  if (role === 'assistant') {
    div.innerHTML = renderMarkdown(text);
  } else {
    div.textContent = text;
  }

  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showStatus(text) {
  const div = document.createElement('div');
  div.className = 'msg msg--status';
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showThinking() {
  if (thinkingEl) return;
  thinkingEl = document.createElement('div');
  thinkingEl.className = 'msg msg--assistant thinking';
  thinkingEl.innerHTML = '<span></span><span></span><span></span>';
  messagesEl.appendChild(thinkingEl);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeThinking() {
  if (thinkingEl) {
    thinkingEl.remove();
    thinkingEl = null;
  }
}

// ── Simple Markdown ──────────────────────────────────────────────────────

function renderMarkdown(text) {
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\n/g, '<br>');
}

// ── Form ─────────────────────────────────────────────────────────────────

formEl.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

  addMessage('user', text);
  ws.send(JSON.stringify({ type: 'message', text }));
  inputEl.value = '';
  inputEl.style.height = 'auto';
  showThinking();
});

inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
});

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    formEl.dispatchEvent(new Event('submit'));
  }
});

// ── Voice (Gemma 4 E4B STT + Browser TTS) ───────────────────────────────

let autoSpeak = false;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// Check for MediaRecorder support and show mic button
if (typeof MediaRecorder !== 'undefined' && navigator.mediaDevices) {
  micBtn.style.display = 'block';
}

micBtn.addEventListener('click', async () => {
  if (isRecording) {
    stopRecording();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

      // Convert to base64 and send over WebSocket
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'audio',
            audio: base64,
            mimeType: 'audio/webm',
          }));
          showThinking();
          autoSpeak = true; // Auto-speak responses after voice input
        }
      };
      reader.readAsDataURL(audioBlob);
    };

    mediaRecorder.start();
    isRecording = true;
    micBtn.classList.add('recording');
    micBtn.title = 'Stop recording';
  } catch (err) {
    console.error('Mic access denied:', err);
    showStatus('Microphone access denied');
  }
});

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  }
  isRecording = false;
  micBtn.classList.remove('recording');
  micBtn.title = 'Voice input';
}

// ── Init ─────────────────────────────────────────────────────────────────

connect();
