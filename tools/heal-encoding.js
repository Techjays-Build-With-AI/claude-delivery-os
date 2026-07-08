#!/usr/bin/env node
/**
 * heal-encoding.js — repair a file whose UTF-8 was double-encoded into mojibake.
 *
 * WHEN TO USE
 * -----------
 * Reports generated *before* the UTF-8-safe injector (assets/inject.js) can have
 * their non-ASCII glyphs already corrupted: "§" stored as "Â§", "—" as "â€"",
 * "…" as "â€¦", "→" as "â†'", etc. This happens when UTF-8 bytes are
 * re-interpreted through a Windows code page (cp1252) and re-saved as UTF-8.
 * The injector prevents *new* corruption; this tool repairs files already
 * written. (For freshly generated reports, use assets/inject.js — you shouldn't
 * need this.)
 *
 * WHAT IT DOES
 * ------------
 * Finds runs of cp1252-range characters, reinterprets each run as the cp1252
 * bytes it really was, and decodes those bytes as UTF-8. A run is only rewritten
 * when it decodes to *valid* UTF-8 with no replacement characters, so healthy
 * text (including correctly-encoded accents) is left untouched and re-running the
 * tool is a no-op (idempotent). It writes a `.bak` copy before overwriting.
 *
 * USAGE
 * -----
 *   node tools/heal-encoding.js <file.html>              # repair in place (+ .bak)
 *   node tools/heal-encoding.js <file.html> --check      # report only, exit 1 if mojibake
 *
 * Works on any text file (.html, .md, .json, ...), not just reports.
 */
'use strict';
const fs = require('fs');

// Map every cp1252 byte to the character it decodes to, and invert it.
const dec1252 = new TextDecoder('windows-1252');
const charToByte = new Map();
for (let b = 0; b < 256; b++) {
  const ch = dec1252.decode(Uint8Array.of(b));
  if (ch === '�') continue; // 0x81/0x8D/0x8F/0x90/0x9D are undefined in cp1252
  charToByte.set(ch, b);
}
const utf8strict = new TextDecoder('utf-8', { fatal: true });

// A char is mojibake-suspicious if it maps to a cp1252 byte >= 0x80.
const suspicious = (ch) => { const b = charToByte.get(ch); return b !== undefined && b >= 0x80; };

// Reinterpret a run of suspicious chars as cp1252 bytes decoded as UTF-8.
function healRun(run) {
  const bytes = [];
  for (const ch of run) { const b = charToByte.get(ch); if (b === undefined) return null; bytes.push(b); }
  try {
    const decoded = utf8strict.decode(Uint8Array.from(bytes));
    if (decoded && !decoded.includes('�')) return decoded;
  } catch (e) { /* not valid UTF-8 -> not mojibake, leave it */ }
  return null;
}

function heal(text) {
  const chars = Array.from(text);
  let out = '', i = 0, healed = 0;
  while (i < chars.length) {
    if (suspicious(chars[i])) {
      let j = i;
      while (j < chars.length && suspicious(chars[j])) j++;
      const run = chars.slice(i, j).join('');
      const fixed = healRun(run);
      if (fixed !== null && fixed !== run) { out += fixed; healed++; } else { out += run; }
      i = j;
    } else {
      out += chars[i++];
    }
  }
  return { text: out, healed };
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const checkOnly = args.includes('--check');
  const file = args.find(a => !a.startsWith('--'));
  if (!file) {
    process.stderr.write('usage: node heal-encoding.js <file> [--check]\n');
    process.exit(64);
  }
  const orig = fs.readFileSync(file, 'utf8');
  const { text, healed } = heal(orig);
  if (text === orig) {
    process.stdout.write('No mojibake found — ' + file + ' is already clean.\n');
    process.exit(0);
  }
  if (checkOnly) {
    process.stdout.write('Mojibake detected in ' + file + ' (' + healed + ' run(s) would be repaired).\n');
    process.exit(1);
  }
  fs.copyFileSync(file, file + '.bak');
  fs.writeFileSync(file, text, 'utf8');
  process.stdout.write('Healed ' + healed + ' run(s) in ' + file + ' (backup: ' + file + '.bak)\n');
}

module.exports = { heal };
