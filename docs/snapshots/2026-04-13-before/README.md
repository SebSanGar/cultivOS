# Pre-improvement snapshot — cultivOS baseline

This directory is the before-state for the agency's first full improvement cycle on cultivOS. It was created by the overnight agent on 2026-04-14 as the first item in the improvement queue.

Everything here is read-only historical record. Do not edit these files after the fact.

## Contents

- `metrics.json` — machine-captured scalar metrics: LOC counts, test results, route counts, accessibility gaps, security posture flags
- `audit.md` — ~400-word narrative covering repo shape, backend health, frontend health, ops, and security red flags as of 2026-04-13
- `README.md` — this file

Visual capture (screenshots, Lighthouse report) was deferred to a local run — the remote sandbox has Playwright available but no running app server at snapshot time. Run `./run.sh` locally and execute `playwright screenshot` against `http://localhost:3000` to capture visuals if needed.

## Why this exists

cultivOS is the first agency project to go through a structured audit → improvement → case-study cycle. The before-snapshot and the eventual after-snapshot (`docs/snapshots/uplifted-YYYY-MM-DD/`) form the DELTA.md artifact that becomes the agency's improvement-cycle template for all future projects.

## Improvement queue

The full backlog, session protocol, and safety clamps are in [`.improvement-cycle/backlog.md`](../../../.improvement-cycle/backlog.md).
