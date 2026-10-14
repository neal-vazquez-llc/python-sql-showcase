# Design decisions

## Durable work

Duplicate submissions return the original job only when their canonical JSON payloads agree. A reused key with changed content fails visibly. `BEGIN IMMEDIATE` serializes claim selection and update, avoiding two workers taking the same queued row.

A worker receives a lease and an increasing generation. Completion checks identity, state, owner, generation, and expiry in one update. Even reuse of the same worker name cannot revive an earlier claim. The result insert and terminal state change share one transaction. A failed result insert rolls back the state update.

An interrupted worker is recovered at the next claim, with terminal failure after the retry budget. This demo intentionally omits heartbeats, distributed coordination, payload encryption, retention, external delivery, and administrative recovery. An external action may run twice; this SQLite design does not make external effects exactly once.

## Business analysis

The commerce query groups receipts per order *before* joining orders. Joining raw receipts first would inflate order values for split settlements. Reports separate payment state, receipt evidence, and pending amounts. Currency is always a grouping key; the example never adds USD and EUR.

Exception classification gives an unknown fulfillment outcome precedence over a missing reference. The appropriate next operation is reconciliation, not blind resubmission. `ROW_NUMBER` expresses oldest-first priority within each currency, with an ID tie-breaker.

This simplified ledger omits fees, refunds as negative cash movements, chargebacks, tax, exchange rates, and settlement dates. Extending it requires modeling those events explicitly. Paid-order amount is not profit, cash available to spend, or accounting revenue.

## AI proposal validation

The model-facing contract permits a headline from an approved set and one to five unique evidence IDs. The validator disallows freeform claims and returns source text verbatim. This trades expressive rewriting for inspectable attribution. The owner still reviews the draft and verifies the underlying facts.

An eventual live-model adapter would need its own privacy review, bounded inputs, authentication, rate and cost limits, refusal handling, and evaluation. No live adapter or private prompt is included.
