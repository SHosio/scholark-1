<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SCHOLARK-1 // Autonomous Research Intelligence</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Share+Tech+Mono&display=swap');

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --g0: #000000;
  --g1: #0a0a0a;
  --g2: #0d1a0d;
  --green: #00ff41;
  --green-dim: #00cc33;
  --green-dark: #004d14;
  --green-glow: rgba(0, 255, 65, 0.15);
  --green-faint: rgba(0, 255, 65, 0.04);
  --amber: #ffb000;
  --red: #ff3333;
  --cyan: #00e5ff;
}

html { scroll-behavior: smooth; }

body {
  background: var(--g0);
  color: var(--green);
  font-family: 'JetBrains Mono', monospace;
  overflow-x: hidden;
  min-height: 100vh;
  position: relative;
}

/* CRT scanlines overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.08) 2px,
    rgba(0, 0, 0, 0.08) 4px
  );
  pointer-events: none;
  z-index: 1000;
}

/* CRT vignette */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.6) 100%);
  pointer-events: none;
  z-index: 999;
}

/* Matrix rain canvas */
#matrix-rain {
  position: fixed;
  inset: 0;
  z-index: 0;
  opacity: 0.07;
}

/* Flicker effect */
@keyframes flicker {
  0%, 100% { opacity: 1; }
  92% { opacity: 1; }
  93% { opacity: 0.8; }
  94% { opacity: 1; }
  96% { opacity: 0.9; }
  97% { opacity: 1; }
}

.crt-flicker {
  animation: flicker 8s infinite;
}

/* Main container */
.container {
  position: relative;
  z-index: 10;
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* Top status bar */
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--green-dark);
  font-size: 11px;
  letter-spacing: 0.1em;
  color: var(--green-dim);
  margin-bottom: 40px;
  opacity: 0;
  animation: fadeUp 0.6s ease forwards 0.2s;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--green);
  border-radius: 50%;
  margin-right: 8px;
  animation: pulse-dot 2s ease-in-out infinite;
  box-shadow: 0 0 6px var(--green), 0 0 12px var(--green-glow);
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* ASCII Robot */
.ascii-entity {
  text-align: center;
  margin: 20px 0 30px;
  opacity: 0;
  animation: fadeUp 0.8s ease forwards 0.5s;
}

.ascii-art {
  font-family: 'Share Tech Mono', monospace;
  font-size: clamp(5px, 1.15vw, 11px);
  line-height: 1.2;
  white-space: pre;
  display: inline-block;
  color: var(--green);
  text-shadow: 0 0 10px var(--green-glow), 0 0 40px rgba(0,255,65,0.05);
  animation: entity-breathe 4s ease-in-out infinite;
  position: relative;
}

@keyframes entity-breathe {
  0%, 100% {
    text-shadow: 0 0 10px var(--green-glow), 0 0 40px rgba(0,255,65,0.05);
    filter: brightness(1);
  }
  50% {
    text-shadow: 0 0 20px rgba(0,255,65,0.3), 0 0 60px rgba(0,255,65,0.1), 0 0 100px rgba(0,255,65,0.05);
    filter: brightness(1.15);
  }
}

/* Eye glow animation */
.eye-left, .eye-right {
  display: inline;
  color: var(--green);
  animation: eye-pulse 3s ease-in-out infinite;
}

.eye-right {
  animation-delay: 0.15s;
}

@keyframes eye-pulse {
  0%, 100% { color: var(--green); text-shadow: 0 0 8px var(--green); }
  30% { color: #ffffff; text-shadow: 0 0 20px var(--green), 0 0 40px var(--green); }
  60% { color: var(--green); text-shadow: 0 0 8px var(--green); }
}

/* Boot sequence */
.boot-line {
  font-size: 10px;
  color: var(--green-dark);
  letter-spacing: 0.05em;
  margin: 4px 0;
  opacity: 0;
  animation: boot-in 0.3s ease forwards;
  text-align: center;
}

.boot-line.ok { color: var(--green-dim); }

/* Title section */
.title-section {
  text-align: center;
  margin: 40px 0 50px;
  opacity: 0;
  animation: fadeUp 0.8s ease forwards 1.2s;
}

.title-main {
  font-family: 'Share Tech Mono', monospace;
  font-size: clamp(32px, 6vw, 64px);
  font-weight: 400;
  letter-spacing: 0.25em;
  color: var(--green);
  text-shadow: 0 0 30px var(--green-glow), 0 0 60px rgba(0,255,65,0.08);
  margin-bottom: 8px;
  animation: title-glow 4s ease-in-out infinite;
}

@keyframes title-glow {
  0%, 100% { text-shadow: 0 0 30px var(--green-glow), 0 0 60px rgba(0,255,65,0.08); }
  50% { text-shadow: 0 0 40px rgba(0,255,65,0.3), 0 0 80px rgba(0,255,65,0.12), 0 0 120px rgba(0,255,65,0.05); }
}

.title-sub {
  font-size: 13px;
  letter-spacing: 0.4em;
  color: var(--green-dim);
  text-transform: uppercase;
}

.title-sub .typed-cursor {
  display: inline-block;
  width: 8px;
  height: 14px;
  background: var(--green);
  margin-left: 4px;
  animation: cursor-blink 1s step-end infinite;
  vertical-align: middle;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Divider */
.divider {
  text-align: center;
  color: var(--green-dark);
  font-size: 11px;
  letter-spacing: 0.3em;
  margin: 40px 0;
  opacity: 0;
  animation: fadeUp 0.6s ease forwards 1.6s;
  overflow: hidden;
}

.divider span {
  display: inline-block;
  position: relative;
  padding: 0 20px;
}

.divider span::before,
.divider span::after {
  content: '════════════════════';
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  color: var(--green-dark);
}

.divider span::before { right: 100%; }
.divider span::after { left: 100%; }

/* Capability cards */
.capabilities {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2px;
  margin: 30px 0;
  opacity: 0;
  animation: fadeUp 0.8s ease forwards 1.8s;
}

.cap-row {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 0;
  border: 1px solid var(--green-dark);
  border-bottom: none;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.cap-row:last-child { border-bottom: 1px solid var(--green-dark); }

.cap-row::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, var(--green-faint), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.cap-row:hover::before { opacity: 1; }
.cap-row:hover { border-color: var(--green-dim); }

.cap-label {
  padding: 14px 16px;
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--green);
  border-right: 1px solid var(--green-dark);
  display: flex;
  align-items: center;
  position: relative;
}

.cap-label .pulse-marker {
  width: 4px;
  height: 4px;
  background: var(--green);
  border-radius: 50%;
  margin-right: 10px;
  flex-shrink: 0;
  animation: pulse-dot 3s ease-in-out infinite;
}

.cap-value {
  padding: 14px 16px;
  font-size: 12px;
  color: var(--green-dim);
  line-height: 1.6;
  position: relative;
}

/* Tools section */
.tools-section {
  margin: 50px 0;
  opacity: 0;
  animation: fadeUp 0.8s ease forwards 2.2s;
}

.tools-header {
  font-size: 10px;
  letter-spacing: 0.3em;
  color: var(--green-dark);
  text-transform: uppercase;
  margin-bottom: 16px;
  padding-left: 2px;
}

.tool-block {
  border-left: 2px solid var(--green-dark);
  padding: 12px 0 12px 20px;
  margin-bottom: 0;
  transition: all 0.3s ease;
  position: relative;
}

.tool-block:hover {
  border-left-color: var(--green);
  background: var(--green-faint);
}

.tool-block:hover .tool-name { color: var(--green); }

.tool-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--green-dim);
  margin-bottom: 4px;
  font-family: 'Share Tech Mono', monospace;
  transition: color 0.3s ease;
}

.tool-name::before {
  content: '> ';
  color: var(--green-dark);
}

.tool-desc {
  font-size: 11px;
  color: rgba(0, 204, 51, 0.5);
  line-height: 1.5;
}

/* Data sources */
.sources {
  margin: 50px 0;
  opacity: 0;
  animation: fadeUp 0.8s ease forwards 2.5s;
}

.source-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.source-tag {
  font-size: 10px;
  letter-spacing: 0.1em;
  padding: 6px 14px;
  border: 1px solid var(--green-dark);
  color: var(--green-dim);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.source-tag::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--green);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.source-tag:hover {
  border-color: var(--green);
  color: var(--green);
}

.source-tag:hover::before { opacity: 0.05; }

.source-tag span { position: relative; }

/* CTA section */
.cta-section {
  text-align: center;
  margin: 60px 0 20px;
  opacity: 0;
  animation: fadeUp 0.8s ease forwards 2.8s;
}

.cta-box {
  border: 1px solid var(--green-dark);
  padding: 30px 40px;
  position: relative;
  display: inline-block;
  transition: all 0.4s ease;
}

.cta-box:hover {
  border-color: var(--green);
  box-shadow: 0 0 30px var(--green-glow), inset 0 0 30px var(--green-faint);
}

.cta-box::before {
  content: '[ INTERFACE ]';
  position: absolute;
  top: -8px;
  left: 20px;
  background: var(--g0);
  padding: 0 10px;
  font-size: 9px;
  letter-spacing: 0.2em;
  color: var(--green-dark);
}

.cta-text {
  font-size: 12px;
  color: var(--green-dim);
  margin-bottom: 16px;
  line-height: 1.6;
}

.cta-command {
  font-family: 'Share Tech Mono', monospace;
  font-size: 13px;
  color: var(--green);
  padding: 10px 24px;
  border: 1px solid var(--green);
  display: inline-block;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  text-decoration: none;
  background: transparent;
}

.cta-command:hover {
  background: var(--green);
  color: var(--g0);
  box-shadow: 0 0 20px var(--green-glow);
}

.cta-command::before {
  content: '$ ';
  opacity: 0.5;
}

/* Footer */
.footer {
  text-align: center;
  padding: 40px 0 20px;
  font-size: 9px;
  letter-spacing: 0.2em;
  color: rgba(0, 204, 51, 0.2);
  opacity: 0;
  animation: fadeUp 0.6s ease forwards 3.2s;
}

.footer .version {
  color: var(--green-dark);
  margin-bottom: 8px;
}

/* Animations */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes boot-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--g0); }
::-webkit-scrollbar-thumb { background: var(--green-dark); }
::-webkit-scrollbar-thumb:hover { background: var(--green-dim); }

/* Mobile */
@media (max-width: 640px) {
  .container { padding: 20px 16px 60px; }
  .cap-row { grid-template-columns: 1fr; }
  .cap-label { border-right: none; border-bottom: 1px solid var(--green-dark); padding: 10px 16px; }
  .ascii-art { font-size: clamp(4px, 2.2vw, 9px); }
  .status-bar { flex-direction: column; gap: 8px; text-align: center; }
}
</style>
</head>
<body class="crt-flicker">

<canvas id="matrix-rain"></canvas>

<div class="container">

  <!-- Status Bar -->
  <div class="status-bar">
    <div><span class="status-dot"></span>SYSTEM ONLINE</div>
    <div><?= strtoupper(date('Y.m.d')) ?> // <?= date('H:i') ?> UTC</div>
    <div>BUILD 1.0.0</div>
  </div>

  <!-- ASCII Entity -->
  <div class="ascii-entity">
    <pre class="ascii-art" id="ascii-robot">
                         _______________
                    ____/               \____
                   /    |  +---------+  |    \
                  /     |  |         |  |     \
                 |   ___| .|_________| .|___   |
                 |  /   '=-    ___    -='   \  |
                 | |         .'   '.         | |
                 | |   <span class="eye-left">(@)</span>  :     :  <span class="eye-right">(@)</span>   | |
                 | |         '.___.'         | |
                 | |    _                _   | |
                 |  \  |_|   .=====.   |_| /   |
                 |   '-.___  |  S  |  ___.-'   |
                 |         '-|  1  |-'         |
                  \          '====='          /
                   \    .-.          .-.    /
                    '--'|  |  ____  |  |'--'
                       _|  |_/    \_|  |_
                      |____|  ||||  |____|
                         |    ||||    |
                    _____|    ||||    |_____
                   /     |    ||||    |     \
                  |  .---|    ||||    |---.  |
                  |  |   |____________|   |  |
                  |  |   /  |      |  \   |  |
                  |  |  /   |      |   \  |  |
                  '--' /    |      |    \ '--'
                      |_____|      |_____|
                      |     |      |     |
                      |     |      |     |
                      |_____|      |_____|
                     /______\    /______\
    </pre>

    <div id="boot-sequence" style="margin-top: 16px;"></div>
  </div>

  <!-- Title -->
  <div class="title-section">
    <h1 class="title-main">SCHOLARK-1</h1>
    <div class="title-sub">
      <span id="typed-subtitle"></span><span class="typed-cursor"></span>
    </div>
  </div>

  <div class="divider"><span>SYSTEM MANIFEST</span></div>

  <!-- Capabilities -->
  <div class="capabilities">
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>CLASS</div>
      <div class="cap-value">Autonomous Research Intelligence // MCP-native agent</div>
    </div>
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>MISSION</div>
      <div class="cap-value">Tap into the world's academic knowledge. Surface context, insights, and wisdom from the literature — on demand.</div>
    </div>
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>PROTOCOL</div>
      <div class="cap-value">MCP stdio transport // Spawned by AI agents // No daemon, no overhead</div>
    </div>
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>ACCURACY</div>
      <div class="cap-value">Every result cites its source. Uncertainty is flagged, never hidden. Scholark-1 does not hallucinate — it tells you when it doesn't know.</div>
    </div>
  </div>

  <!-- Tools -->
  <div class="tools-section">
    <div class="tools-header">// ACTIVE TOOLS</div>
    <div class="tool-block">
      <div class="tool-name">search_papers</div>
      <div class="tool-desc">Multi-source search across Semantic Scholar + Crossref. Combined results with source attribution.</div>
    </div>
    <div class="tool-block">
      <div class="tool-name">fetch_paper_details</div>
      <div class="tool-desc">Deep metadata retrieval with automatic fallback chain. SS first, Crossref for DOIs.</div>
    </div>
    <div class="tool-block">
      <div class="tool-name">search_by_topic</div>
      <div class="tool-desc">Topic search with year range filtering. Falls back gracefully when primary source is empty.</div>
    </div>
    <div class="tool-block">
      <div class="tool-name">doi_to_bibtex</div>
      <div class="tool-desc">DOI to BibTeX via content negotiation. Accepts any format — bare, URL, prefixed.</div>
    </div>
  </div>

  <!-- Data Sources -->
  <div class="sources">
    <div class="tools-header">// DATA SOURCES</div>
    <div class="source-grid">
      <div class="source-tag"><span>SEMANTIC SCHOLAR</span></div>
      <div class="source-tag"><span>CROSSREF</span></div>
      <div class="source-tag"><span>DOI.ORG</span></div>
      <div class="source-tag"><span>OPENALEX <sup style="font-size:7px;opacity:0.5">SOON</sup></span></div>
      <div class="source-tag"><span>UNPAYWALL <sup style="font-size:7px;opacity:0.5">SOON</sup></span></div>
      <div class="source-tag"><span>CLAUDE API <sup style="font-size:7px;opacity:0.5">SOON</sup></span></div>
    </div>
  </div>

  <!-- CTA -->
  <div class="cta-section">
    <div class="cta-box">
      <div class="cta-text">
        Open source. MCP-native. Built for agents and researchers.<br>
        Install in one command.
      </div>
      <a href="https://github.com/SHosio/scholark-1" target="_blank" class="cta-command">git clone scholark-1</a>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div class="version">v1.0.0 // BUILD <?= date('Ymd') ?> // STDIO TRANSPORT</div>
    <div>SCHOLARK-1 IS WATCHING THE LITERATURE</div>
  </div>

</div>

<script>
// Matrix rain
const canvas = document.getElementById('matrix-rain');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

const chars = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEF';
const fontSize = 14;
let columns = Math.floor(canvas.width / fontSize);
let drops = Array(columns).fill(1);

function drawMatrix() {
  ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#00ff41';
  ctx.font = fontSize + 'px monospace';

  for (let i = 0; i < drops.length; i++) {
    const text = chars[Math.floor(Math.random() * chars.length)];
    ctx.fillText(text, i * fontSize, drops[i] * fontSize);

    if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
      drops[i] = 0;
    }
    drops[i]++;
  }
}

setInterval(drawMatrix, 50);

window.addEventListener('resize', () => {
  columns = Math.floor(canvas.width / fontSize);
  drops = Array(columns).fill(1);
});

// Boot sequence
const bootMessages = [
  { text: '[INIT] Loading neural pathways...', delay: 300 },
  { text: '[SYNC] Connecting to Semantic Scholar....... OK', delay: 600, ok: true },
  { text: '[SYNC] Connecting to Crossref............... OK', delay: 900, ok: true },
  { text: '[SYNC] DOI resolver online.................. OK', delay: 1200, ok: true },
  { text: '[BOOT] Scholark-1 initialized. Ready to serve.', delay: 1600, ok: true },
];

const bootContainer = document.getElementById('boot-sequence');

bootMessages.forEach(msg => {
  setTimeout(() => {
    const line = document.createElement('div');
    line.className = 'boot-line' + (msg.ok ? ' ok' : '');
    line.textContent = msg.text;
    line.style.animationDelay = '0s';
    bootContainer.appendChild(line);
  }, msg.delay);
});

// Typed subtitle
const subtitle = 'YOUR AUTONOMOUS RESEARCH INTELLIGENCE';
const typedEl = document.getElementById('typed-subtitle');
let charIndex = 0;

function typeChar() {
  if (charIndex < subtitle.length) {
    typedEl.textContent += subtitle[charIndex];
    charIndex++;
    setTimeout(typeChar, 40 + Math.random() * 60);
  }
}

setTimeout(typeChar, 1400);
</script>

</body>
</html>
