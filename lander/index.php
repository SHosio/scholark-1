<?php
$db = new SQLite3(__DIR__ . '/analytics.db');
$db->exec('CREATE TABLE IF NOT EXISTS clicks (id INTEGER PRIMARY KEY, clicked_at TEXT, ip TEXT, ua TEXT)');
$db->exec('CREATE TABLE IF NOT EXISTS robot_clicks (id INTEGER PRIMARY KEY, total INTEGER DEFAULT 0)');
$db->exec('INSERT OR IGNORE INTO robot_clicks (id, total) VALUES (1, 0)');

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    if ($_POST['action'] === 'cta_click') {
        $stmt = $db->prepare('INSERT INTO clicks (clicked_at, ip, ua) VALUES (:at, :ip, :ua)');
        $stmt->bindValue(':at', date('c'));
        $stmt->bindValue(':ip', $_SERVER['REMOTE_ADDR'] ?? '');
        $stmt->bindValue(':ua', $_SERVER['HTTP_USER_AGENT'] ?? '');
        $stmt->execute();
        $count = $db->querySingle('SELECT COUNT(*) FROM clicks');
        header('Content-Type: application/json');
        echo json_encode(['ok' => true, 'total' => $count]);
        exit;
    }
    if ($_POST['action'] === 'robot_click') {
        $db->exec('UPDATE robot_clicks SET total = total + 1 WHERE id = 1');
        $total = $db->querySingle('SELECT total FROM robot_clicks WHERE id = 1');
        header('Content-Type: application/json');
        echo json_encode(['total' => $total]);
        exit;
    }
}

$robotClicks = $db->querySingle('SELECT total FROM robot_clicks WHERE id = 1') ?: 0;
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SCHOLARK-1 // Autonomous Research Intelligence</title>
<meta name="description" content="Free, open-source MCP server that gives your AI agent access to real academic papers, real citations, and real BibTeX. No hallucinated references.">
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

.entity-icon {
  font-size: clamp(120px, 20vw, 200px);
  line-height: 1;
  animation: entity-breathe 4s ease-in-out infinite;
  filter: grayscale(1) brightness(0.8) sepia(1) hue-rotate(70deg) saturate(5);
  cursor: pointer;
  user-select: none;
  transition: transform 0.1s ease;
}

.entity-icon:active {
  transform: scale(0.9);
}

.entity-icon.clicked {
  animation: robot-bonk 0.3s ease;
}

@keyframes robot-bonk {
  0% { transform: scale(1) rotate(0deg); }
  25% { transform: scale(1.15) rotate(-5deg); }
  50% { transform: scale(0.95) rotate(3deg); }
  75% { transform: scale(1.05) rotate(-2deg); }
  100% { transform: scale(1) rotate(0deg); }
}

.robot-counter {
  font-size: 10px;
  color: var(--green-dark);
  letter-spacing: 0.1em;
  margin-top: 8px;
  transition: color 0.3s ease;
}

.robot-counter.flash {
  color: var(--green);
}

.click-particle {
  position: absolute;
  font-size: 14px;
  pointer-events: none;
  animation: particle-fly 0.8s ease-out forwards;
  z-index: 100;
}

@keyframes particle-fly {
  0% { opacity: 1; transform: translateY(0) scale(1); }
  100% { opacity: 0; transform: translateY(-60px) scale(0.5); }
}

@keyframes entity-breathe {
  0%, 100% {
    filter: grayscale(1) brightness(0.8) sepia(1) hue-rotate(70deg) saturate(5) drop-shadow(0 0 10px var(--green-glow));
  }
  50% {
    filter: grayscale(1) brightness(1) sepia(1) hue-rotate(70deg) saturate(6) drop-shadow(0 0 30px rgba(0,255,65,0.3));
  }
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

/* Problem section */
.problem-section {
  text-align: center;
  margin: 0 0 50px;
  opacity: 0;
  animation: fadeUp 0.8s ease forwards 1.7s;
}

.problem-text {
  font-size: 14px;
  color: var(--green-dim);
  line-height: 1.8;
  max-width: 700px;
  margin: 0 auto;
}

.problem-text .highlight {
  color: var(--green);
}

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

/* Setup section */
.setup-section {
  margin: 50px 0;
  opacity: 0;
  animation: fadeUp 0.8s ease forwards 2.6s;
}

.setup-code {
  background: rgba(0, 255, 65, 0.03);
  border: 1px solid var(--green-dark);
  padding: 20px 24px;
  font-size: 12px;
  color: var(--green-dim);
  line-height: 1.8;
  margin-top: 16px;
  overflow-x: auto;
}

.setup-code .comment {
  color: var(--green-dark);
}

.setup-code .command {
  color: var(--green);
}

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
  content: '[ OPEN SOURCE ]';
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

.cta-secondary {
  margin-top: 18px;
  font-size: 10px;
  color: var(--green-dark);
  letter-spacing: 0.05em;
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

.footer a {
  color: var(--green-dark);
  text-decoration: none;
  transition: color 0.3s ease;
}

.footer a:hover {
  color: var(--green-dim);
}

.footer .author {
  color: var(--green-dark);
  margin-bottom: 12px;
  font-size: 10px;
}

.footer .promo {
  color: rgba(0, 204, 51, 0.25);
  margin-top: 12px;
  font-size: 10px;
  letter-spacing: 0.1em;
  font-style: italic;
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
    <div>FREE & OPEN SOURCE</div>
    <div>MIT LICENSE</div>
  </div>

  <!-- Entity -->
  <div class="ascii-entity">
    <div class="entity-icon" id="robot-btn" title="Click me.">&#x1F916;</div>
    <div class="robot-counter" id="robot-counter"><?= number_format($robotClicks) ?> researchers have poked the robot</div>
    <div id="boot-sequence" style="margin-top: 16px;"></div>
  </div>

  <!-- Title -->
  <div class="title-section">
    <h1 class="title-main">SCHOLARK-1</h1>
    <div class="title-sub">
      <span id="typed-subtitle"></span><span class="typed-cursor"></span>
    </div>
  </div>

  <!-- Problem -->
  <div class="problem-section">
    <p class="problem-text">
      Your AI assistant is brilliant at reasoning. But it <span class="highlight">invents paper titles</span>,
      <span class="highlight">fabricates DOIs</span>, and <span class="highlight">hallucinates citation counts</span>.
      Scholark-1 connects it to real academic databases so every reference it gives you actually exists.
    </p>
  </div>

  <div class="divider"><span>SYSTEM MANIFEST</span></div>

  <!-- Capabilities -->
  <div class="capabilities">
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>WHAT</div>
      <div class="cap-value">An MCP server that gives your AI agent direct access to real academic papers, real metadata, real BibTeX, and real open access PDFs. 6 tools, 5 databases, zero hallucinated references.</div>
    </div>
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>HOW</div>
      <div class="cap-value">Searches 4 databases in parallel. Deduplicates results by DOI. Falls back automatically when a source is down. Caches lookups in SQLite. Every result cites its source.</div>
    </div>
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>SETUP</div>
      <div class="cap-value">Clone. Install. Go. Zero API keys required. Works with Claude Code, Claude Desktop, Cursor, Windsurf, or any MCP-compatible client.</div>
    </div>
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>COST</div>
      <div class="cap-value">Free. Forever. MIT licensed. All underlying APIs are free for research use. No paid tier, no usage limits, no tracking.</div>
    </div>
    <div class="cap-row">
      <div class="cap-label"><span class="pulse-marker"></span>TRUST</div>
      <div class="cap-value">Every result states its source. 4 databases cross-checked and deduplicated by DOI. Uncertainty flagged, never hidden. Your AI stops making things up.</div>
    </div>
  </div>

  <!-- Tools -->
  <div class="tools-section">
    <div class="tools-header">// ACTIVE TOOLS</div>
    <div class="tool-block">
      <div class="tool-name">search_papers</div>
      <div class="tool-desc">Search 4 databases in parallel. Results deduplicated by DOI. Source attribution on every paper.</div>
    </div>
    <div class="tool-block">
      <div class="tool-name">fetch_paper_details</div>
      <div class="tool-desc">Deep metadata with automatic fallback across 4 sources. Cached for speed.</div>
    </div>
    <div class="tool-block">
      <div class="tool-name">search_by_topic</div>
      <div class="tool-desc">Topic search with year range filtering. Find what was published on X between 2020 and 2025.</div>
    </div>
    <div class="tool-block">
      <div class="tool-name">doi_to_bibtex</div>
      <div class="tool-desc">Any DOI to a BibTeX entry. Paste a DOI, get a .bib-ready citation. Cached for 90 days.</div>
    </div>
    <div class="tool-block">
      <div class="tool-name">find_open_access</div>
      <div class="tool-desc">Find free, legal PDFs via Unpaywall. See OA status, version, license, and download links.</div>
    </div>
    <div class="tool-block">
      <div class="tool-name">get_citation_context</div>
      <div class="tool-desc">The actual sentences where other papers cite a work. See how a finding was received, criticized, or extended.</div>
    </div>
  </div>

  <!-- Data Sources -->
  <div class="sources">
    <div class="tools-header">// DATA SOURCES</div>
    <div class="source-grid">
      <div class="source-tag"><span>SEMANTIC SCHOLAR</span></div>
      <div class="source-tag"><span>OPENALEX</span></div>
      <div class="source-tag"><span>CROSSREF</span></div>
      <div class="source-tag"><span>EUROPE PMC</span></div>
      <div class="source-tag"><span>UNPAYWALL</span></div>
    </div>
  </div>

  <!-- Setup -->
  <div class="setup-section">
    <div class="tools-header">// 3-STEP SETUP</div>
    <div class="setup-code">
      <span class="comment"># 1. Clone and install</span><br>
      <span class="command">git clone https://github.com/SHosio/scholark-1.git && cd scholark-1 && uv sync</span><br><br>
      <span class="comment"># 2. Register in Claude Code (or any MCP client)</span><br>
      <span class="command">claude mcp add scholark-1 -- uv run --project /path/to/scholark-1 python server.py</span><br><br>
      <span class="comment"># 3. Ask your AI to search for papers. That's it.</span><br>
      <span class="command">"Find recent papers on retrieval-augmented generation for scientific literature"</span>
    </div>
  </div>

  <!-- CTA -->
  <div class="cta-section">
    <div class="cta-box">
      <div class="cta-text">
        Free and open source. MIT licensed.<br>
        Give your AI agent the academic literature it's been missing.
      </div>
      <a href="https://github.com/SHosio/scholark-1" class="cta-command" id="cta-btn" onclick="ctaClick(event)">git clone scholark-1</a>
      <div class="cta-secondary">
        No API keys required to start. All 5 core tools work immediately.
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div class="author">Built by <a href="https://simohosio.com" target="_blank" rel="noopener">Professor Simo Hosio</a></div>
    <div class="version">MIT LICENSE // STDIO TRANSPORT // OPEN SOURCE</div>
    <div>SCHOLARK-1 IS WATCHING THE LITERATURE SO YOU DON'T HAVE TO</div>
    <div class="promo">Too busy to learn tools like this? You might be doing academia wrong.<br><a href="https://edgeacademia.com/powertrio" target="_blank" rel="noopener">PhD Power Trio Framework</a> — a better way to PhD.</div>
  </div>

</div>

<script>
// CTA click handler — tracks interest, then redirects to GitHub
function ctaClick(e) {
  e.preventDefault();
  fetch(window.location.href, {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'action=cta_click'
  }).catch(() => {});
  window.open('https://github.com/SHosio/scholark-1', '_blank');
}

// Robot cookie clicker
const robotBtn = document.getElementById('robot-btn');
const robotCounter = document.getElementById('robot-counter');
const particles = ['+1', '📄', '📚', '🔬', '🧪', '📖', '🎓', '⚡'];

robotBtn.addEventListener('click', function(e) {
  // Bonk animation
  this.classList.remove('clicked');
  void this.offsetWidth; // force reflow
  this.classList.add('clicked');

  // Flash counter
  robotCounter.classList.add('flash');
  setTimeout(() => robotCounter.classList.remove('flash'), 300);

  // Floating particle
  const particle = document.createElement('span');
  particle.className = 'click-particle';
  particle.textContent = particles[Math.floor(Math.random() * particles.length)];
  particle.style.left = (e.clientX - 10) + 'px';
  particle.style.top = (e.clientY - 10) + 'px';
  particle.style.position = 'fixed';
  document.body.appendChild(particle);
  setTimeout(() => particle.remove(), 800);

  // Send to server
  fetch(window.location.href, {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'action=robot_click'
  })
  .then(r => r.json())
  .then(data => {
    robotCounter.textContent = Number(data.total).toLocaleString() + ' researchers have poked the robot';
  })
  .catch(() => {});
});

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
  { text: '[INIT] Loading research intelligence...', delay: 300 },
  { text: '[SYNC] Semantic Scholar.................... OK', delay: 500, ok: true },
  { text: '[SYNC] OpenAlex............................ OK', delay: 700, ok: true },
  { text: '[SYNC] Crossref............................ OK', delay: 900, ok: true },
  { text: '[SYNC] Europe PMC.......................... OK', delay: 1100, ok: true },
  { text: '[SYNC] Unpaywall........................... OK', delay: 1300, ok: true },
  { text: '[CACHE] SQLite DOI cache online............ OK', delay: 1500, ok: true },
  { text: '[BOOT] 6 tools active. 0 API keys required.', delay: 1800, ok: true },
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
