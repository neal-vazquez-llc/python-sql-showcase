from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from showcase.queue import Queue
from showcase.commerce import demo_database, report
from showcase.evidence import SYNTHETIC_FACTS, validate_proposal


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 100.0
        self.queue = Queue(Path(self.temp.name) / 'test.sqlite', clock=lambda: self.now)

    def test_idempotency_and_conflict(self):
        first = self.queue.enqueue('request', {'a': 1, 'b': 2})
        self.assertEqual(first, self.queue.enqueue('request', {'b': 2, 'a': 1}))
        with self.assertRaises(ValueError):
            self.queue.enqueue('request', {'a': 2})

    def test_concurrent_claimants(self):
        self.queue.enqueue('request', {})
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(self.queue.claim, ['worker-a','worker-b']))
        self.assertEqual(sum(claim is not None for claim in claims), 1)

    def test_generation_fences_same_owner_after_recovery(self):
        self.queue.enqueue('request', {})
        stale = self.queue.claim('worker', lease_seconds=1)
        self.now += 1
        replacement = self.queue.claim('worker')
        with self.assertRaises(ValueError):
            self.queue.complete(stale, {'value': 'stale'})
        self.queue.complete(replacement, {'value': 'current'})
        with self.queue.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM results').fetchone()[0], 1)

    def test_expired_claim_cannot_complete(self):
        self.queue.enqueue('request', {})
        claim = self.queue.claim('worker', lease_seconds=1)
        self.now += 1
        with self.assertRaises(ValueError):
            self.queue.complete(claim, {})

    def test_retry_exhaustion(self):
        self.queue.enqueue('request', {})
        for _ in range(3):
            self.assertIsNotNone(self.queue.claim('worker', lease_seconds=1))
            self.now += 1
        self.assertIsNone(self.queue.claim('worker'))
        with self.queue.connection() as db:
            self.assertEqual(db.execute('SELECT state FROM jobs').fetchone()[0], 'failed')

    def test_result_and_state_roll_back_together(self):
        identifier = self.queue.enqueue('request', {})
        claim = self.queue.claim('worker')
        with self.queue.connection(write=True) as db:
            db.execute('INSERT INTO results VALUES(?,?)', (identifier, '{}'))
        with self.assertRaises(sqlite3.IntegrityError):
            self.queue.complete(claim, {})
        with self.queue.connection() as db:
            self.assertEqual(db.execute('SELECT state FROM jobs').fetchone()[0], 'running')

    def test_bound_parameters(self):
        key = "request'); DROP TABLE jobs; --"
        self.queue.enqueue(key, {'text': key})
        self.assertEqual(self.queue.claim('worker')['request_key'], key)

    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):
            self.queue.enqueue('request', {'score': float('nan')})

    def test_unknown_database_preserved(self):
        path = Path(self.temp.name) / 'unknown.sqlite'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE original(value TEXT)')
            db.execute("INSERT INTO original VALUES('preserved')")
        with self.assertRaises(ValueError):
            Queue(path)
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute('SELECT value FROM original').fetchone()[0], 'preserved')

    def test_newer_schema_rejected(self):
        with self.queue.connection(write=True) as db:
            db.execute('PRAGMA user_version=2')
        with self.assertRaises(ValueError):
            Queue(self.queue.path)


class CommerceTests(unittest.TestCase):
    def setUp(self):
        self.db = demo_database()
        self.addCleanup(self.db.close)

    def test_split_receipts_do_not_duplicate_paid_orders(self):
        rows = {r['currency']: r for r in report(self.db, 'cash_summary')}
        self.assertEqual(rows['USD']['paid_order_minor'], 25000)
        self.assertEqual(rows['USD']['received_minor'], 17000)
        self.assertEqual(rows['USD']['pending_minor'], 6000)
        self.assertEqual(rows['EUR']['paid_order_minor'], 9000)
        self.assertEqual(rows['EUR']['received_minor'], 0)

    def test_exception_precedence_and_ranking(self):
        rows = {r['id']: r for r in report(self.db, 'reconciliation')}
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows['demo-02']['exception'], 'reconcile_unknown_outcome')
        self.assertEqual(rows['demo-02']['priority'], 2)
        self.assertEqual(rows['demo-04']['priority'], 1)

    def test_invalid_amount_and_orphan_receipt(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO settlements VALUES('bad','missing',1)")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE orders SET amount_minor=-1 WHERE id='demo-01'")


class EvidenceTests(unittest.TestCase):
    def proposal(self, ids):
        return json.dumps({'headline': 'Business automation', 'fact_ids': ids})

    def test_preserves_exact_evidence_and_draft_status(self):
        result = validate_proposal(self.proposal(['example-02']), SYNTHETIC_FACTS)
        self.assertEqual(result['bullets'], [SYNTHETIC_FACTS['example-02']])
        self.assertEqual(result['status'], 'draft_for_human_review')

    def test_unknown_and_duplicate_references(self):
        for ids in [['invented'], ['example-01','example-01'], [], [1]]:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                validate_proposal(self.proposal(ids), SYNTHETIC_FACTS)

    def test_ai_cannot_add_freeform_claims(self):
        with self.assertRaises(ValueError):
            validate_proposal(json.dumps({'headline': 'Business automation',
                'fact_ids': ['example-01'], 'revenue': 'invented'}), SYNTHETIC_FACTS)


if __name__ == '__main__':
    unittest.main()
