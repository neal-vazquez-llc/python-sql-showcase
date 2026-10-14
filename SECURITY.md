# Publication boundaries

This repository contains isolated examples and synthetic fixtures. It excludes credentials, provider identifiers, production configurations, internal service addresses, deployment workflows, personal records, customer information, and original private Git history.

Do not submit secrets, customer records, or private system details in issues or pull requests. If you find a disclosure concern, use a contact route already published by the owner and describe the concern without reproducing sensitive values publicly.

Before changes are published, review every file and the complete outgoing diff. Run the tests and `python3 tools/release_check.py`. That check enforces this release's file allowlist and flags a limited set of suspicious literals; it cannot certify that arbitrary content is safe or secret-free.

Keep demonstrations offline and fixtures synthetic. New dependencies, live integrations, private-source excerpts, broader release scope, or an open-source license require a deliberate owner decision. No automated merges or production deployment are configured.
