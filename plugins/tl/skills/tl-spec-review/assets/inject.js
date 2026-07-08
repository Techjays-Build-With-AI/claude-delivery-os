#!/usr/bin/env node
/**
 * inject.js — inject a review/audit JSON data object into an HTML report
 * template, writing the result as guaranteed UTF-8.
 *
 * WHY THIS EXISTS
 * ---------------
 * The reports embed non-ASCII characters (section signs §, em dashes —, arrows
 * →, etc.) both in the template chrome and in the injected review text. Pasting
 * the assembled HTML through a shell/editor that assumes a Windows code page
 * (cp1252) double-encodes those bytes: UTF-8 gets re-read as cp1252 and
 * re-encoded as UTF-8, so "§" is stored as "Â§" and "—" as "â€"" (mojibake),
 * even though <meta charset="utf-8"> is present.
 *
 * Node reads and writes UTF-8 explicitly and deterministically, so doing the
 * token replacement here removes the double-encoding vector entirely. The
 * script also fails loudly if the input JSON is invalid or if classic mojibake
 * is detected, so a bad byte can never ship silently.
 *
 * USAGE
 * -----
 *   node inject.js <template.html> <data.json> <TOKEN> <output.html>
 *
 * Example:
 *   node inject.js assets/report.html scope-review-2026-07-08-215230.json \
 *     __REVIEW_DATA__ scope-review-2026-07-08-215230.html
 *
 * Steps: build the review data object, write it to the .json sidecar first
 * (with the file Write tool, which is clean UTF-8), then run this script to
 * produce the .html. Never hand-assemble the full HTML through a shell.
 */
'use strict';
const fs = require('fs');

function die(msg, code) {
  process.stderr.write('inject.js: ' + msg + '\n');
  process.exit(code || 1);
}

const [templatePath, dataPath, token, outputPath] = process.argv.slice(2);
if (!templatePath || !dataPath || !token || !outputPath) {
  die('usage: node inject.js <template.html> <data.json> <TOKEN> <output.html>', 64);
}

// Read both inputs as UTF-8 — this is the whole point.
let template, raw;
try { template = fs.readFileSync(templatePath, 'utf8'); }
catch (e) { die('cannot read template ' + templatePath + ': ' + e.message); }
try { raw = fs.readFileSync(dataPath, 'utf8'); }
catch (e) { die('cannot read data ' + dataPath + ': ' + e.message); }

// Strip a UTF-8 BOM if the sidecar happens to carry one.
raw = raw.replace(/^﻿/, '').trim();

// Validate the JSON so an invalid payload can't render the empty-state page.
try { JSON.parse(raw); }
catch (e) { die('data file is not valid JSON: ' + e.message + '\n  Fix the sidecar and re-run.'); }

if (!template.includes(token)) {
  die('token "' + token + '" not found in template ' + templatePath);
}

// Inject the validated JSON verbatim so the embedded copy matches the sidecar.
const html = template.split(token).join(raw);

// Guard: refuse to write recognizable double-encoding (mojibake) signatures.
const moji = html.match(/Â[ §±°·º–—»«]|â€[”“˜™"']|Ã[©¨¤¢£]/);
if (moji) {
  die('mojibake detected after injection (e.g. "' + moji[0] + '"). ' +
      'The data sidecar is already double-encoded — regenerate it as clean UTF-8.', 2);
}

// Write UTF-8, no BOM.
try { fs.writeFileSync(outputPath, html, { encoding: 'utf8' }); }
catch (e) { die('cannot write output ' + outputPath + ': ' + e.message); }

process.stdout.write(
  'Wrote ' + outputPath + ' (' + Buffer.byteLength(html, 'utf8') + ' bytes, UTF-8, clean).\n'
);
