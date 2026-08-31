# Standalone repository completion plan

Status: **complete** (2026-08-31).

This plan moved the ESE Kongress selector out of `codingWithGPT`, made the
standalone repository testable without redistributing congress content, and
added repeatable quality and release automation.

## 1. Preserve the repository history

- [x] Extract the original subdirectory with `git subtree split`.
- [x] Preserve all 10 original commits, including messages, authors, and dates.
- [x] Remove the old copy from `codingWithGPT` only after verifying the split.
- [x] Configure the public repository at
      `github.com/marcelpetrick/ESE_Kongress_Selektor`.

## 2. Make the crawler and bootstrap testable

- [x] Let `crawler/parse.py` accept input and output paths.
- [x] Fail clearly when a raw-data directory contains no timetable pages.
- [x] Raise the supported Python floor to 3.10, matching `requests==2.34.2`.
- [x] Add `run.py --skip-crawl` for deterministic offline rebuilds.
- [x] Keep the Windows virtual-environment path testable.

## 3. Add deterministic quality checks

- [x] Add synthetic Converia-shaped fixtures with invented programme content.
- [x] Cover parsing, classification, bootstrap, cross-file consistency, and
      workflow contracts with 43 unit tests.
- [x] Add `localPipeline.py` as the single local and CI gate:
  compile, unit tests, fixture build, and JavaScript syntax check.
- [x] Add optional live-site and headless-browser checks.
- [x] Add `make check` and `make test` shortcuts.

## 4. Automate quality and releases

- [x] Run the shared offline gate on Python 3.10–3.14 under Ubuntu, plus Python
      3.14 under Windows and macOS.
- [x] Prove the one-command bootstrap on Linux and Windows.
- [x] Keep live network access out of push and pull-request checks; use a weekly
      and manual canary instead.
- [x] On `vMAJOR.MINOR.PATCH`, rerun quality checks, create a tracked-files-only
      ZIP and SHA-256 checksum, and publish an idempotent GitHub Release.
- [x] Pin every referenced GitHub Action to an exact release.

## 5. Finish the public documentation

- [x] Add CI, license, Python, and platform badges.
- [x] Document the one-command bootstrap, every flag, viewer interactions,
      dependencies, CI behavior, and release process.
- [x] Add checked calendar and filtered list screenshots.
- [x] State authorship, GPL-3.0-or-later licensing, and the unofficial/personal
      nature of the tool.

## Verification record

- `python3 localPipeline.py --network --browser`: all six steps pass.
- Unit suite: 43 tests pass against synthetic fixtures.
- `actionlint .github/workflows/*.yml`: both workflows pass.
- The release archive/checksum path is dry-run locally after the atomic commits.
- No generated `data/`, `web/data.js`, virtual environment, or scraped congress
  text is tracked.

## Commit structure

1. `test: add synthetic fixtures and the unit suite`
2. `feat(run): raise the Python floor to 3.10 and add --skip-crawl`
3. `ci: run the shared local pipeline on Linux, Windows and macOS`
4. `ci(release): publish checked source archives for version tags`
5. `docs(readme): badges, screenshots and automation documentation`
