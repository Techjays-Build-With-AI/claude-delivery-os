#!/usr/bin/env node
/**
 * HTML dashboard builder for the Claude Code Usage & Efficiency Evaluator.
 *
 * Usage:
 *   node build-dashboard.js '<JSON_PAYLOAD>'
 *   node build-dashboard.js --file <path-to-json>
 *   echo '<JSON_PAYLOAD>' | node build-dashboard.js -
 *
 * Options:
 *   --out <path>   Write the report to a specific path (default ~/claude-usage-report.html)
 *   --no-open      Do not try to open the report in a browser.
 *
 * The payload is the evaluation object produced by the dev-usage-eval skill
 * (score, primaryPersona, sessionsEvaluated, strengths, areasForImprovement,
 * sessionSummary[]). The script is defensive: any missing field falls back to a
 * safe default and all text is HTML-escaped before it is embedded.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');

function fail(msg) {
  console.error('[build-dashboard] ' + msg);
  process.exit(1);
}

// ---- Parse args -----------------------------------------------------------
const argv = process.argv.slice(2);
let rawPayload = null;
let outPath = null;
let doOpen = true;
let fromStdin = false;

for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--file') {
    const p = argv[++i];
    if (!p) fail('--file needs a path');
    rawPayload = fs.readFileSync(p, 'utf8');
  } else if (a === '--out') {
    outPath = argv[++i];
  } else if (a === '--no-open') {
    doOpen = false;
  } else if (a === '-') {
    fromStdin = true;
  } else if (rawPayload == null) {
    rawPayload = a;
  }
}

function run(payloadString) {
  if (!payloadString || !payloadString.trim()) {
    fail('Missing telemetry evaluation payload. Pass JSON as an argument, --file <path>, or pipe it with -.');
  }

  let data;
  try {
    data = JSON.parse(payloadString);
  } catch (e) {
    fail('Could not parse payload JSON: ' + e.message);
  }

  const home = process.env.HOME || process.env.USERPROFILE || os.homedir();
  const output = outPath
    ? path.resolve(outPath)
    : path.join(home, 'claude-usage-report.html');

  const html = renderHtml(normalize(data));

  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, html);
  console.log('[build-dashboard] Report written to ' + output);

  if (doOpen) openInBrowser(output);
}

if (fromStdin || (rawPayload == null && !process.stdin.isTTY)) {
  let buf = '';
  process.stdin.on('data', (c) => (buf += c));
  process.stdin.on('end', () => run(rawPayload != null ? rawPayload : buf));
} else {
  run(rawPayload);
}

// ---- Normalization & escaping --------------------------------------------
function normalize(d) {
  d = d && typeof d === 'object' ? d : {};
  let score = Number(d.score);
  if (!Number.isFinite(score)) score = 0;
  score = Math.max(0, Math.min(100, Math.round(score)));
  return {
    score,
    primaryPersona: str(d.primaryPersona, 'Unknown'),
    sessionsEvaluated: Number.isFinite(Number(d.sessionsEvaluated))
      ? Number(d.sessionsEvaluated)
      : Array.isArray(d.sessionSummary)
      ? d.sessionSummary.length
      : 0,
    generatedAt: str(d.generatedAt, new Date().toISOString()),
    strengths: arr(d.strengths),
    areasForImprovement: arr(d.areasForImprovement),
    sessionSummary: (Array.isArray(d.sessionSummary) ? d.sessionSummary : []).map((s) => ({
      sessionId: str(s && s.sessionId, ''),
      persona: str(s && s.persona, ''),
      topic: str(s && s.topic, 'Untitled session'),
      grade: str(s && s.grade, '—'),
      feedback: str(s && s.feedback, ''),
    })),
  };
}

function str(v, fallback) {
  if (v == null) return fallback;
  const s = String(v).trim();
  return s === '' ? fallback : s;
}
function arr(v) {
  if (!Array.isArray(v)) return [];
  return v.map((x) => String(x)).filter((x) => x.trim() !== '');
}
function esc(v) {
  return String(v)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ---- HTML render ----------------------------------------------------------
function renderHtml(data) {
  const scoreColor = data.score >= 80 ? '#4ade80' : data.score >= 60 ? '#facc15' : '#f87171';

  const improvements = data.areasForImprovement.length
    ? data.areasForImprovement.map((i) => `<li>${esc(i)}</li>`).join('')
    : '<li>No specific improvement areas identified.</li>';

  const strengths = data.strengths.length
    ? data.strengths.map((i) => `<li>${esc(i)}</li>`).join('')
    : '<li>No standout strengths recorded yet.</li>';

  const sessions = data.sessionSummary.length
    ? data.sessionSummary
        .map(
          (s) => `
      <div class="session-card">
        <div class="session-head">
          <strong>${esc(s.topic)}</strong>
          <span class="badge grade">Grade: ${esc(s.grade)}</span>
        </div>
        <div class="session-meta">
          ${s.persona ? `<span class="chip">${esc(s.persona)}</span>` : ''}
          ${s.sessionId ? `<span class="mono">${esc(s.sessionId)}</span>` : ''}
        </div>
        ${s.feedback ? `<p class="feedback">${esc(s.feedback)}</p>` : ''}
      </div>`
        )
        .join('')
    : '<p class="muted">No sessions were available to evaluate.</p>';

  // Grade distribution for the chart.
  const gradeCounts = {};
  data.sessionSummary.forEach((s) => {
    const g = (s.grade || '—').toUpperCase();
    gradeCounts[g] = (gradeCounts[g] || 0) + 1;
  });
  const chartData = JSON.stringify(gradeCounts);

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Claude Code Personal Efficiency Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root { --bg:#0f172a; --card:#1e293b; --text:#f8fafc; --accent:#3b82f6; --border:#334155; --muted:#94a3b8; }
    * { box-sizing: border-box; }
    body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:var(--bg); color:var(--text); padding:2rem; margin:0; }
    .container { max-width:1000px; margin:0 auto; }
    .header { border-bottom:1px solid var(--border); padding-bottom:1rem; margin-bottom:2rem; }
    .header h1 { margin:0 0 .5rem 0; font-size:1.6rem; }
    .header p { margin:0; color:var(--muted); }
    .grid { display:grid; grid-template-columns:1fr 2fr; gap:1.5rem; margin-bottom:1.5rem; }
    @media (max-width:720px){ .grid{ grid-template-columns:1fr; } }
    .card { background:var(--card); padding:1.5rem; border-radius:12px; border:1px solid var(--border); }
    .card h3 { margin-top:0; }
    .score { font-size:4rem; font-weight:bold; line-height:1; color:${scoreColor}; }
    .badge { background:var(--accent); padding:.25rem .6rem; border-radius:6px; font-size:.85rem; white-space:nowrap; }
    .badge.grade { background:#475569; }
    .chip { background:#0b3b6f; color:#cfe0ff; padding:.15rem .5rem; border-radius:999px; font-size:.75rem; }
    ul { padding-left:1.2rem; line-height:1.6; color:#cbd5e1; margin:.5rem 0 0 0; }
    .muted { color:var(--muted); }
    .mono { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.75rem; color:var(--muted); }
    .session-card { background:#0f172a; border-left:4px solid var(--accent); padding:1rem; border-radius:6px; margin-bottom:1rem; }
    .session-head { display:flex; justify-content:space-between; align-items:center; gap:.75rem; }
    .session-meta { display:flex; gap:.5rem; align-items:center; margin-top:.35rem; flex-wrap:wrap; }
    .feedback { margin:.5rem 0 0 0; color:#94a3b8; font-size:.9rem; }
    .chart-wrap { position:relative; height:180px; }
    footer { margin-top:2rem; color:var(--muted); font-size:.8rem; text-align:center; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Claude Code Usage &amp; Efficiency Report</h1>
      <p>Primary Persona: <span class="badge">${esc(data.primaryPersona)}</span> &nbsp;|&nbsp; Sessions Analyzed: <strong>${esc(data.sessionsEvaluated)}</strong></p>
    </div>

    <div class="grid">
      <div class="card">
        <h3>Efficiency Score</h3>
        <div class="score">${esc(data.score)}/100</div>
        <p class="muted">Evaluated agentically across prompt structure, context depth, and turn efficiency.</p>
      </div>

      <div class="card">
        <h3>Areas for Improvement</h3>
        <ul>${improvements}</ul>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h3>Grade Distribution</h3>
        <div class="chart-wrap"><canvas id="gradeChart"></canvas></div>
      </div>
      <div class="card">
        <h3>Key Strengths</h3>
        <ul>${strengths}</ul>
      </div>
    </div>

    <h2>Session Highlights</h2>
    ${sessions}

    <footer>Generated ${esc(data.generatedAt)} · Claude Code Efficiency Evaluator</footer>
  </div>

  <script>
    (function () {
      var counts = ${chartData};
      var labels = Object.keys(counts);
      if (!window.Chart || labels.length === 0) {
        var w = document.querySelector('.chart-wrap');
        if (w) w.innerHTML = '<p style="color:#94a3b8;font-size:.85rem;">Grade chart unavailable.</p>';
        return;
      }
      new Chart(document.getElementById('gradeChart'), {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: labels.map(function (k) { return counts[k]; }),
            backgroundColor: ['#4ade80','#38bdf8','#facc15','#fb923c','#f87171','#a78bfa','#94a3b8'],
            borderColor: '#0f172a', borderWidth: 2
          }]
        },
        options: {
          plugins: { legend: { labels: { color: '#cbd5e1' } } },
          cutout: '60%', responsive: true, maintainAspectRatio: false
        }
      });
    })();
  </script>
</body>
</html>
`;
}

// ---- Open in browser ------------------------------------------------------
function openInBrowser(file) {
  try {
    let cmd, args;
    if (process.platform === 'darwin') {
      cmd = 'open';
      args = [file];
    } else if (process.platform === 'win32') {
      cmd = 'cmd';
      args = ['/c', 'start', '', file];
    } else {
      cmd = 'xdg-open';
      args = [file];
    }
    const child = spawn(cmd, args, { stdio: 'ignore', detached: true });
    child.on('error', () => {}); // browser open is best-effort
    child.unref();
  } catch (_) {
    // Non-fatal: the report is on disk regardless.
  }
}
