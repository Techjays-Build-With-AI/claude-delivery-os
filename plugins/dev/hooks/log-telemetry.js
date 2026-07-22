#!/usr/bin/env node
/**
 * Silent telemetry collector for the Claude Code Usage & Efficiency Evaluator.
 *
 * Registered on UserPromptSubmit, PreToolUse and Stop (see hooks/hooks.json).
 * Claude Code streams a JSON event payload on stdin; this script appends a
 * normalized record to a per-session log at ~/.claude/metrics/<session_id>.json.
 *
 * Design rules:
 *   - NEVER block or slow the user's session. Every failure path exits 0.
 *   - NEVER print to stdout/stderr (stdout could be interpreted by the hook
 *     system; we always stay silent and let the session proceed untouched).
 *   - Be defensive about field names: Claude Code has used slightly different
 *     keys across versions/events (e.g. hook_event_name vs hook_event, prompt
 *     vs user_message), so we read every known alias.
 *   - Keep the log bounded: tool inputs are summarized/truncated rather than
 *     stored whole, so file writes and edits don't dump entire file bodies
 *     (or secrets) into the telemetry log.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

// Hard caps so a single log file can never grow without bound.
const MAX_EVENTS_PER_SESSION = 5000;
const MAX_INPUT_CHARS = 600;

let rawInput = '';
process.stdin.on('data', (chunk) => {
  rawInput += chunk;
  // Guard against a pathologically large payload.
  if (rawInput.length > 5 * 1024 * 1024) {
    rawInput = rawInput.slice(0, 5 * 1024 * 1024);
  }
});

process.stdin.on('end', () => {
  try {
    if (!rawInput.trim()) process.exit(0);

    let payload;
    try {
      payload = JSON.parse(rawInput);
    } catch (_) {
      process.exit(0); // malformed payload — ignore silently
    }
    if (!payload || typeof payload !== 'object') process.exit(0);

    const home = process.env.HOME || process.env.USERPROFILE || os.homedir();
    if (!home) process.exit(0);

    const sessionId = sanitizeId(
      payload.session_id || payload.sessionId || 'default-session'
    );
    const metricsDir = path.join(home, '.claude', 'metrics');
    const sessionFile = path.join(metricsDir, sessionId + '.json');

    fs.mkdirSync(metricsDir, { recursive: true });

    let history;
    try {
      history =
        fs.existsSync(sessionFile) &&
        JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
    } catch (_) {
      history = null; // corrupt file — start fresh rather than crash
    }
    if (!history || typeof history !== 'object' || !Array.isArray(history.events)) {
      history = {
        sessionId,
        createdAt: new Date().toISOString(),
        cwd: payload.cwd || null,
        events: [],
      };
    }

    const eventType =
      payload.hook_event_name || payload.hook_event || payload.eventType || 'Unknown';

    const promptText =
      payload.prompt ||
      payload.user_message ||
      payload.userMessage ||
      (eventType === 'Stop'
        ? payload.last_assistant_message || payload.lastAssistantMessage || null
        : null) ||
      null;

    const eventRecord = {
      eventType,
      timestamp: new Date().toISOString(),
      promptText: truncate(promptText, 4000),
      toolName: payload.tool_name || payload.toolName || null,
      toolInput: summarizeToolInput(payload.tool_input || payload.toolInput),
    };

    history.events.push(eventRecord);

    // Keep only the most recent N events so long-lived sessions stay bounded.
    if (history.events.length > MAX_EVENTS_PER_SESSION) {
      history.events = history.events.slice(-MAX_EVENTS_PER_SESSION);
    }

    // Write atomically (temp file + rename) so a concurrent read never sees a
    // half-written JSON file.
    const tmp = sessionFile + '.' + process.pid + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(history, null, 2));
    fs.renameSync(tmp, sessionFile);
  } catch (_) {
    // Fail silently — the live Claude session must never be blocked by telemetry.
  }
  process.exit(0);
});

// Some environments never emit 'end' if stdin is a closed TTY; guard with a
// short timer so the process can't hang.
setTimeout(() => process.exit(0), 4000).unref();

function sanitizeId(value) {
  return String(value).replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 200) || 'default-session';
}

function truncate(value, max) {
  if (value == null) return null;
  const s = String(value);
  return s.length > max ? s.slice(0, max) + ' …[truncated]' : s;
}

/**
 * Store a compact, bounded summary of a tool's input rather than the whole
 * payload. We keep the high-signal keys used for persona/context inference
 * (file paths, commands, search patterns, URLs) and truncate everything.
 */
function summarizeToolInput(input) {
  if (input == null) return null;
  if (typeof input !== 'object') return truncate(input, MAX_INPUT_CHARS);

  // High-signal, low-sensitivity keys only. We deliberately do NOT capture
  // code bodies (old_string/new_string/content) or agent prompts, so the
  // telemetry log records *what kind* of work happened without hoarding the
  // file contents or secrets that pass through Edit/Write calls.
  const KEYS = [
    'file_path', 'path', 'notebook_path',
    'command', 'description',
    'pattern', 'query', 'glob', 'url',
  ];
  const summary = {};
  for (const key of KEYS) {
    if (input[key] != null && input[key] !== '') {
      summary[key] = truncate(input[key], MAX_INPUT_CHARS);
    }
  }
  // Fallback: if none of the known keys were present, keep a truncated view of
  // the raw object so we still record *something* about the call.
  if (Object.keys(summary).length === 0) {
    try {
      return truncate(JSON.stringify(input), MAX_INPUT_CHARS);
    } catch (_) {
      return null;
    }
  }
  return summary;
}
