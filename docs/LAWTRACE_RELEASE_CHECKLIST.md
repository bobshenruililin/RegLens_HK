# LawTrace HK — release checklist (executable gates)

Objective pass/fail gates for a future agent. Do not mark Website RC1 complete unless every **Required** gate passes.

## A. Environment

- [ ] `make lawtrace-doctor` exits 0
- [ ] `python3`, `npm`, `node` reported ok
- [ ] Working tree inspected; LawTrace branch identified

## B. Data

- [ ] Cap. 614: 12/12 English snapshots; sampling `complete=true`
- [ ] Cap. 614 reconstruction: all supported pairs pass (demo export)
- [ ] Cap. 599G local-real: extracts present OR documented official-source blocker
- [ ] If Cap. 599G present: sampling label matches reality (`complete` only if all available snapshots included; otherwise explicit “N of M”)
- [ ] Root `manifest.json` `dataset_mode` matches build intent (`demo` vs `local`)
- [ ] No tracked files under `apps/lawtrace/public/data/instruments/cap-599g/`
- [ ] No tracked raw ZIP/XML under LawTrace public data
- [ ] No `private-data/**` tracked

## C. Product surfaces (running site)

Start with `make lawtrace-open` (or open-local). Then verify:

- [ ] Landing opens; “Explore a real change” reaches a comparison in ≤3 interactions
- [ ] Global search finds instrument and section
- [ ] Collections show Cap. 614 and Cap. 599G (when local)
- [ ] Instrument explorer: timeline, activity, section list
- [ ] Transition explorer: filter/sort; aggregates link to comparisons
- [ ] Comparator: inline redline, side-by-side, structure/status human text, provenance, copyable URL
- [ ] Added and removed section routes render
- [ ] Section history lists snapshots with comparison links
- [ ] Insights metrics link to evidence
- [ ] Methodology shows pipeline and limitations
- [ ] Direct route refresh does not 404 (static server index behaviour)
- [ ] Snapshot language uses “Official open-data snapshot dated …”
- [ ] Required DATA.GOV.HK / HKeL disclaimer present
- [ ] No “in force on”, commencement/effective-date implication, verified-copy claim, or legal-importance claim

## D. Local review workspace

- [ ] Ordinary `make lawtrace-build` / CI: `/review` and `/audit` absent from `out/`
- [ ] With `LAWTRACE_LOCAL_REVIEW=1` / open-local: `/review` present
- [ ] Not linked from ordinary nav
- [ ] CONFIRM/REJECT/UNCERTAIN + notes + JSON export work locally
- [ ] No automatic write-back of human-confirmed into source artifacts

## E. Build & CI

- [ ] `pytest tests/lawtrace` pass
- [ ] `make lawtrace-ci` pass
- [ ] Production `apps/lawtrace/out/index.html` exists
- [ ] Representative static routes exist (collections, insights, methodology, cap-614)
- [ ] RegLens isolation: LawTrace changes do not break `make verify` when required by shared surfaces
- [ ] No public deployment performed for this checklist

## F. Reviews & assets

- [ ] At least one adversarial pass covering student, lawyer, researcher, trust, a11y roles with task-level evidence
- [ ] Critical/high findings fixed or explicitly blocking
- [ ] Screenshots under `docs/assets/lawtrace/` for required surfaces
- [ ] `docs/LAWTRACE_OPERATIONS.md` still accurate

## G. One-command access

- [ ] `make lawtrace-open` prints a clickable `http://127.0.0.1:<port>/` URL
- [ ] `make lawtrace-stop` stops the preview
- [ ] Server uses `scripts/lawtrace_static_server.py` (no directory listings)

## Pass criterion

All **Required** boxes above checked with evidence (command output, route URL, or screenshot path). Medium issues may be documented as non-blocking limitations.
