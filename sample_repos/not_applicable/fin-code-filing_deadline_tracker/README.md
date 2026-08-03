# fin-code-filing_deadline_tracker

Finance · Code · Regulatory Filing Deadline Tracker

## Purpose

Reads the list of upcoming regulatory filing deadlines and flags anything
due within its required notice window, so Compliance can act before a
deadline is missed.

## Structure

| Folder | Contents |
|---|---|
| `data/` | Filing deadline list and the generated alert list |
| `FilingTracker_Pipeline/` | `01` check upcoming deadlines and write alerts |

This is a small, single-stage utility script — there is no database layer,
no model training, and no multi-tier storage involved.

## How to run

```bash
pip install -r requirements.txt

python FilingTracker_Pipeline/01_CheckUpcomingDeadlines.py
```

## Branch strategy

| Branch | Purpose |
|---|---|
| `master` | Production-ready — protected, requires PR review |
| `develop` | Integration branch |
| `user-story/{id}` | Feature work |

Commit message format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
