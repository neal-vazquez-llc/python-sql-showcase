# Python + SQL: Applied AI Engineering

A focused code portfolio from **Neal Vazquez LLC**: turning AI-assisted project work into inspectable, testable software for business and professional goals.

These runnable examples adapt patterns from actual media, commerce, and career-document projects. They are newly isolated demonstrations with entirely synthetic data, not production source exports. Original implementation history and operational context remain private.

## Run it in two minutes

Requires Python 3.11+ with SQLite 3.25+. No external packages, credentials, network calls, paid model access, or provider accounts.

```sh
python3 -m showcase
python3 -m unittest discover -s tests -v
```

Run from the repository root. The demo uses a temporary job database and an in-memory commerce database; it cleans up after itself.

## Explore the code

| Example | Python | SQL | What to inspect |
| --- | --- | --- | --- |
| Durable media-style jobs | [queue.py](showcase/queue.py) | [jobs.sql](sql/jobs.sql) | Idempotency conflicts, transactional claims, bounded retries, generation fencing, atomic results |
| Commerce exceptions and cash | [commerce.py](showcase/commerce.py) | [reconciliation.sql](sql/reconciliation.sql), [cash_summary.sql](sql/cash_summary.sql) | CTEs, join cardinality, window functions, deterministic priorities, currency isolation |
| Evidence-backed career drafts | [evidence.py](showcase/evidence.py) | — | Structured proposal validation, approved fact selection, human review boundary |

The synthetic commerce demo produces three exceptions. Its USD summary contains 25,000 paid-order minor units, 17,000 received minor units, and 6,000 pending minor units; EUR stays in a separate row. These are fixture outputs, not company revenue or performance claims.

## AI as part of engineering

AI can accelerate decomposition, implementation, query design, documentation, and adversarial test ideas. Reliability still depends on explicit contracts and executable checks. This release was prepared with Codex assistance at the owner's request; it does not claim unaided authorship or independently verified historical productivity gains.

The third example models a concrete AI boundary: an assistant proposes approved fact IDs; Python resolves exact approved text and rejects invented references or extra claim fields. The offline demo supplies a simulated proposal. It does not call an AI model or pretend that synthetic statements describe a real candidate.

For a technical walkthrough, see [design decisions](docs/DESIGN.md). For derivation and limitations, see [provenance](docs/PROVENANCE.md). For publication boundaries, see [security](SECURITY.md).

## Scope

These examples demonstrate engineering choices, not live integrations, deployed readiness, financial advice, or measured commercial outcomes. The job queue is at-least-once; downstream side effects need their own idempotency. The cash report is a simplified positive-receipt ledger, not accounting software. The drafting validator cannot establish whether its approved source facts are true.

Copyright © 2026 Neal Vazquez LLC. No open-source license is granted in this initial showcase. Public viewing does not itself grant unrestricted reuse; GitHub's applicable platform terms still apply.
