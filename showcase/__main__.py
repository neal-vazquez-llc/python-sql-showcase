import json
from pathlib import Path
from tempfile import TemporaryDirectory
from .queue import Queue
from .commerce import demo_database, report
from .evidence import SYNTHETIC_FACTS, validate_proposal


def main():
    with TemporaryDirectory() as directory:
        queue = Queue(Path(directory) / 'demo.sqlite')
        job_id = queue.enqueue('synthetic-export-01', {'asset': 'example-asset'})
        assert job_id == queue.enqueue('synthetic-export-01', {'asset': 'example-asset'})
        claim = queue.claim('demo-worker')
        queue.complete(claim, {'status': 'synthetic_result'})
        print('QUEUE: duplicate request resolved to one durable job; result committed.')
    db = demo_database()
    try:
        print('EXCEPTIONS:', json.dumps(report(db, 'reconciliation'), indent=2))
        print('CASH:', json.dumps(report(db, 'cash_summary'), indent=2))
    finally:
        db.close()
    raw = json.dumps({'headline': 'Analytical engineering', 'fact_ids': ['example-01','example-02']})
    print('EVIDENCE DRAFT:', json.dumps(validate_proposal(raw, SYNTHETIC_FACTS), indent=2))


if __name__ == '__main__':
    main()
