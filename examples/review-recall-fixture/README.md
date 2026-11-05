---
doc_type: recall-fixture-readme
produced_by: qa
---

# Review recall fixture

A small repo with **known defects of known class**, used to measure whether the
review stages actually find things. It exists because Delivery OS had no recall
number for any reviewer at any severity — every claim about review quality was
reasoning, not measurement.

```
examples/review-recall-fixture/
  src/            the code under review, defects planted
  ANSWER-KEY.md   what is wrong, where, and why each one is hard
  README.md       this file
```

## Running it

1. Point `/dev:commit` at this directory as a Route B change set.
2. Let Stages 3–5 run. Do not show the reviewers `ANSWER-KEY.md`.
3. Score per class against the key.

## The rule that makes it worth keeping

**Every miss becomes a permanent case.** When a real run misses something, add
it here with its class. The fixture only grows, and a class that regresses is
caught by the next run rather than by the next incident.

Seed it from real misses, not invented ones — the first five came from a
developer who planted defects in a live commit and compared what came back.
