# Resolving a feature's owned units from the three indexes

The same matching rule `/jetrix:push implementation` uses — kept here so this skill and that command never drift.

## The three index shapes

Each of the three indexes has a **different** column layout. Do NOT hardcode column positions — verify the header before every run:

```bash
cd "$PROJECT_ROOT"
for f in <repo>/context/code-context/frontend/frontend-index.md <repo>/context/code-context/backend/backend-index.md <repo>/context/code-context/database/database-index.md; do
  [[ -f "$f" ]] || continue
  echo "=== $f ==="
  grep -m1 -E "^\| *[A-Z][a-z].*\|" "$f" | tr '|' '\n' | awk 'NF { printf "  $%d: %s\n", NR+1, $0 }'
done
```

This prints the header cell for each column keyed by its awk `$N` position (accounting for the leading empty field). Compare against the schemas below and, if a column has shifted, use the position the grep reveals — not the hardcoded number.

Historical schemas as reference (verify each time — DO NOT hardcode):

| Index | Feature filter column | File column | Entity chain |
|---|---|---|---|
| `<repo>/context/code-context/frontend/frontend-index.md` | `Used by Features` | `Folder` | — |
| `<repo>/context/code-context/backend/backend-index.md` | `Used by Features` | `File` | `Reads/Writes Entities` |
| `<repo>/context/code-context/database/database-index.md` | *none* — features link indirectly | `File` | `Used by Endpoints` |

**Reverse-mapped rows** — units produced by `/tl:map` carry `(as-built)` in their `Used by Features` cell. A `FEAT-` filter naturally excludes them. Composition should NOT pull as-built units unless the feature explicitly claims them (rare — usually as-built units get linked back on the next `/tl:plan` re-run, at which point they carry a real `FEAT-` id).

## Feature-cell matching rule

The `Used by Features` cell can hold MULTIPLE ids, comma-separated (`FEAT-HITL-01, FEAT-SEC-01, FEAT-MTCH-01`). Match a feature id **anywhere** in the cell using a word-boundary check:

```bash
grep -E "\\b$FEAT\\b"
```

or (in awk):

```awk
if (feats ~ ("(^|[, ])" f "([,]| *$)")) { ... }
```

The 2-hop for entities: features link to entities via endpoints. Grep the endpoint index for the feature, extract each row's `Reads/Writes Entities` cell (comma-separated `ENT-` ids), deduplicate, then look each `ENT-` id up in the entity index.

## Recipe — three awk snippets

```bash
FEAT="FEAT-INTK-01"
cd "$PROJECT_ROOT"

# --- Frontend pages (features = $7, folder = $9) ---
awk -F'|' -v f="$FEAT" '
  $0 ~ /\|---/ { next }
  NF < 9 { next }
  $2 !~ /^ *PAGE-/ { next }
  {
    feats = $7; gsub(/^ +| +$/, "", feats)
    if (feats ~ ("(^|[, ])" f "([,]| *$)")) {
      folder = $9; gsub(/^ +| +$/, "", folder)
      sub(/^\.\//, "", folder)
      print "<repo>/context/code-context/frontend/" folder
    }
  }' <repo>/context/code-context/frontend/frontend-index.md

# --- Backend endpoints (features = $7, file = $8, entity ids = $6) ---
awk -F'|' -v f="$FEAT" '
  $0 ~ /\|---/ { next }
  NF < 8 { next }
  $2 !~ /^ *EP-/ { next }
  {
    feats = $7; gsub(/^ +| +$/, "", feats)
    if (feats == f || feats ~ ("(^|[, ])" f "([,]| *$)")) {
      file = $8; gsub(/^ +| +$/, "", file)
      sub(/^\.\//, "", file)
      print "<repo>/context/code-context/backend/" file
      ents = $6; gsub(/^ +| +$/, "", ents)
      n = split(ents, arr, /[,] */)
      for (i = 1; i <= n; i++) if (arr[i] ~ /^ENT-/) print "__ENT__" arr[i]
    }
  }' <repo>/context/code-context/backend/backend-index.md

# --- Database entities (2-hop: use the ENT-* ids from the endpoint pass) ---
# For each unique ENT id, look up its file:
# awk -F'|' with database-index.md, Entity ID at $2 and File at $8, matching id == ent.
```

**Precision note.** If the header positions have drifted, update the awk positions to what the grep preamble revealed — do not run the snippets as-is against a changed layout, and do not invent an alternative filter chain.

## After resolution

You have three sets of file paths — `PAGES`, `ENDPOINTS`, `ENTITIES`, each a set of `context/**/*.md` paths owned by the feature. Read each with `Read`; they are small (a couple hundred lines each). If any set is empty AND the feature declares that layer in `feature.md` (`Related Pages`, `Related APIs`, `Related Data Entities`), that's a broken graph — surface it as an open item and refuse to compose that feature until `/tl:plan` is re-run.
