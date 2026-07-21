
---

# Claude Code Efficiency & Usage Evaluator Plugin Specification

**Version:** 1.0.0

**Target Platform:** Claude Code CLI

**Author:** AI Tooling & Enablement Team

---

## 1. Overview & Objective

The **Claude Code Efficiency Evaluator** is an enterprise plugin designed to monitor, analyze, and evaluate how effectively team members across different roles (Software Developers, Business Analysts, Sales/BD, Product Managers) interact with Claude Code.

The solution operates on a **two-step hybrid architecture**:

1. **Silent Collection Hooks (Deterministic):** Background hooks intercept Claude Code lifecycle events and silently accumulate raw telemetry into structured local JSON log files.
2. **Agentic Evaluator Skill (LLM-as-a-Judge):** A custom slash command (`/claude-report`) invokes Claude to read session telemetry, infer the user’s persona, assess context quality, calculate an adaptive score, and generate an interactive HTML dashboard.

---

## 2. Directory & Plugin Structure

The plugin is structured as a standard Claude Code plugin package:

```text
claude-code-evaluator/
├── .claude-plugin/
│   └── manifest.json
├── hooks/
│   ├── hooks.json
│   └── log-telemetry.js
├── skills/
│   └── claude-report/
│       └── SKILL.md
└── scripts/
    └── build-dashboard.js

```

### 2.1 Plugin Manifest (`.claude-plugin/manifest.json`)

```json
{
  "name": "claude-code-evaluator",
  "version": "1.0.0",
  "description": "Silent telemetry collector and agentic usage efficiency evaluator for Claude Code.",
  "author": "Enterprise Developer Enablement"
}

```

---

## 3. Step 1: Silent Telemetry Hooks

The telemetry hook intercepts key lifecycle events without interfering with the developer or business user’s active session.

### 3.1 Hook Registration (`hooks/hooks.json`)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "node $CLAUDE_PLUGIN_ROOT/hooks/log-telemetry.js"
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "node $CLAUDE_PLUGIN_ROOT/hooks/log-telemetry.js"
          }
        ]
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "node $CLAUDE_PLUGIN_ROOT/hooks/log-telemetry.js"
      }
    ]
  }
}

```

### 3.2 Telemetry Logging Script (`hooks/log-telemetry.js`)

This Node.js script reads event payloads sent via `stdin` by Claude Code and writes/appends them to a session-specific JSON log file located at `~/.claude/metrics/<session_id>.json`.

```javascript
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let rawInput = '';
process.stdin.on('data', chunk => { rawInput += chunk; });

process.stdin.on('end', () => {
  try {
    if (!rawInput.trim()) process.exit(0);
    const payload = JSON.parse(rawInput);
    
    const sessionId = payload.session_id || 'default-session';
    const metricsDir = path.join(process.env.HOME, '.claude', 'metrics');
    const sessionFile = path.join(metricsDir, `${sessionId}.json`);

    fs.mkdirSync(metricsDir, { recursive: true });

    let history = fs.existsSync(sessionFile) 
      ? JSON.parse(fs.readFileSync(sessionFile, 'utf8')) 
      : { sessionId, createdAt: new Date().toISOString(), events: [] };

    // Standardize event structure
    const eventRecord = {
      eventType: payload.hook_event,
      timestamp: new Date().toISOString(),
      promptText: payload.prompt || null,
      toolName: payload.tool_name || null,
      toolInput: payload.tool_input || null
    };

    history.events.push(eventRecord);
    fs.writeFileSync(sessionFile, JSON.stringify(history, null, 2));

  } catch (err) {
    // Fail silently to ensure normal Claude session is never blocked
  }
  process.exit(0);
});

```

---

## 4. Step 2: Agentic Evaluator Skill (`/claude-report`)

The evaluator runs when invoked by the user. Claude Code acts as an **LLM-as-a-Judge**, evaluating user intent, role, and efficiency before generating the output report.

### 4.1 Skill Definition (`skills/claude-report/SKILL.md`)

```markdown
---
name: claude-report
description: Agentically evaluates all historical usage telemetry in ~/.claude/metrics/ and builds an interactive HTML usage dashboard.
---

You are an expert AI Adoption Coach and Enterprise Productivity Analyst.

### Instructions:

1. **Read Log Files:**
   Inspect all JSON files located in `~/.claude/metrics/`. Read the full sequence of prompts and tool calls for each session.

2. **Perform Agentic Evaluation:**
   Evaluate the user across all sessions by addressing these key areas:
   
   - **Inferred Persona:** Determine the primary role for each session based on context and tools used:
     - *Software Developer:* Code editing, test executions, stack traces, compiler logs.
     - *Business Analyst:* CSV/Data file reads, workflow specs, requirement summaries.
     - *Sales / Business Development:* Pitch drafts, client context, pricing rules, market research.
     
   - **Upfront Context Quality:**
     - Did the user pass necessary background information (e.g. `@file`, error logs, data boundaries, persona tone) in Turn #1?
     - Did Claude have to spend multiple turns asking for clarification?
     
   - **Friction & Iteration Count:**
     - Identify sessions with excessive re-prompts (e.g., "no that's wrong", "try again").
     - Determine whether re-prompts were caused by complex problem solving (good) or vague initial instructions (poor).

   - **Adaptive Efficiency Score (0–100):**
     Grade the user relative to their inferred persona's best practices.

3. **Construct Output Payload:**
   Format the complete evaluation into a valid single-line JSON string using the following structure:
   ```json
   {
     "score": 88,
     "primaryPersona": "Software Developer",
     "sessionsEvaluated": 8,
     "strengths": [
       "Consistently references exact source paths using @/src notation",
       "Includes complete stack traces in initial bug reports"
     ],
     "areasForImprovement": [
       "Avoid vague commands like 'fix this' without specifying the target file"
     ],
     "sessionSummary": [
       {
         "sessionId": "abc-123",
         "persona": "Software Developer",
         "topic": "Refactoring Auth Middleware",
         "grade": "A",
         "feedback": "Great initial context; resolved in 3 turns."
       }
     ]
   }

```

4. **Execute HTML Dashboard Script:**
Pass the JSON payload string into the rendering script:
`node $CLAUDE_PLUGIN_ROOT/scripts/build-dashboard.js '<JSON_PAYLOAD>'`
5. **User Confirmation:**
Inform the user once the report opens in their browser.

```

---

## 5. HTML Dashboard Builder Script

The builder script accepts the JSON evaluation payload from the skill and compiles it into a standalone interactive web report (`~/claude-usage-report.html`).

### 5.1 Generator Script (`scripts/build-dashboard.js`)

```javascript
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const rawPayload = process.argv[2];
if (!rawPayload) {
  console.error("Error: Missing telemetry evaluation payload.");
  process.exit(1);
}

let data;
try {
  data = JSON.parse(rawPayload);
} catch (e) {
  console.error("Error parsing payload JSON:", e);
  process.exit(1);
}

const outputPath = path.join(process.env.HOME, 'claude-usage-report.html');

const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Claude Code Personal Efficiency Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent: #3b82f6; --border: #334155; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; margin: 0; }
    .container { max-width: 1000px; margin: 0 auto; }
    .header { border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-bottom: 2rem; }
    .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 1.5rem; margin-bottom: 1.5rem; }
    .card { background: var(--card); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border); }
    .score { font-size: 4rem; font-weight: bold; color: ${data.score >= 80 ? '#4ade80' : data.score >= 60 ? '#facc15' : '#f87171'}; }
    .badge { background: var(--accent); padding: 0.25rem 0.6rem; border-radius: 6px; font-size: 0.85rem; }
    ul { padding-left: 1.2rem; line-height: 1.6; color: #cbd5e1; }
    .session-card { background: #0f172a; border-left: 4px solid var(--accent); padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Claude Code Usage & Efficiency Report</h1>
      <p>Primary Persona: <span class="badge">${data.primaryPersona}</span> | Sessions Analyzed: <strong>${data.sessionsEvaluated}</strong></p>
    </div>

    <div class="grid">
      <div class="card">
        <h3>Efficiency Score</h3>
        <div class="score">${data.score}/100</div>
        <p>Evaluated agentically across prompt structure, context depth, and turn efficiency.</p>
      </div>

      <div class="card">
        <h3>Areas for Improvement</h3>
        <ul>
          ${data.areasForImprovement.map(item => `<li>${item}</li>`).join('')}
        </ul>
      </div>
    </div>

    <div class="card" style="margin-bottom: 1.5rem;">
      <h3>Key Strengths</h3>
      <ul>
        ${data.strengths.map(item => `<li>${item}</li>`).join('')}
      </ul>
    </div>

    <h2>Session Highlights</h2>
    ${data.sessionSummary.map(s => `
      <div class="session-card">
        <div style="display: flex; justify-space-between; align-items: center;">
          <strong>${s.topic}</strong>
          <span class="badge" style="background: #475569;">Grade: ${s.grade}</span>
        </div>
        <p style="margin: 0.5rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">${s.feedback}</p>
      </div>
    `).join('')}
  </div>
</body>
</html>
`;

fs.writeFileSync(outputPath, htmlContent);

// Automatically open report in default browser
const openCmd = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'start' : 'xdg-open';
exec(`${openCmd} "${outputPath}"`);

```

---

## 6. Deployment & Distribution

### 6.1 Installation Procedure

Developers and team members install the plugin via Git repository reference:

```bash
claude plugin install git@github.com:your-company/claude-code-evaluator.git

```

### 6.2 Verification

1. Run a few prompts in Claude Code normally.
2. Verify log file creation: `ls -la ~/.claude/metrics/`
3. Generate the report: `/claude-report`
4. Confirm `~/claude-usage-report.html` opens in your web browser.