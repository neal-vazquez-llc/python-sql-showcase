"""Idempotent enqueue, bounded retries, and fenced completion in SQLite.

At-least-once execution: a lease does not make external side effects exactly once.
The generation token prevents a stale claimant from committing a local result.
"""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time
import uuid

SQL = Path(__file__).resolve().parents[1] / 'sql'


class Queue:
    def __init__(self, path, *, clock=time.time, max_attempts=3):
        if max_attempts < 1:
            raise ValueError('max_attempts must be positive')
        self.path, self.clock, self.max_attempts = str(path), clock, max_attempts
        with self.connection(write=True) as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version == 0:
                if db.execute("SELECT 1 FROM sqlite_master WHERE type='table'").fetchone():
                    raise ValueError('Refusing to initialize an unknown database')
                # Execute individual DDL statements without executescript's implicit commit.
                statement = ''
                for line in (SQL / 'jobs.sql').read_text().splitlines(keepends=True):
                    statement += line
                    if sqlite3.complete_statement(statement):
                        db.execute(statement)
                        statement = ''
                if statement.strip():
                    raise ValueError('Incomplete schema statement')
                db.execute('PRAGMA user_version=1')
            elif version != 1:
                raise ValueError('Unsupported schema version')

    @contextmanager
    def connection(self, *, write=False):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            if write:
                db.execute('BEGIN IMMEDIATE')
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    def enqueue(self, request_key, payload):
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
        if not request_key:
            raise ValueError('request_key is required')
        with self.connection(write=True) as db:
            existing = db.execute('SELECT id,payload FROM jobs WHERE request_key=?',
                                  (request_key,)).fetchone()
            if existing:
                if existing['payload'] != encoded:
                    raise ValueError('Idempotency key reused with different payload')
                return existing['id']
            identifier = uuid.uuid4().hex
            db.execute('INSERT INTO jobs(id,request_key,payload,state,created_at) '
                       "VALUES(?,?,?,'queued',?)",
                       (identifier, request_key, encoded, self.clock()))
            return identifier

    def claim(self, owner, *, lease_seconds=30):
        if not owner or lease_seconds <= 0:
            raise ValueError('Owner and positive lease required')
        now = self.clock()
        with self.connection(write=True) as db:
            db.execute("UPDATE jobs SET state=CASE WHEN attempts>=? THEN 'failed' "
                       "ELSE 'queued' END, owner=NULL,lease_until=NULL "
                       "WHERE state='running' AND lease_until<=?", (self.max_attempts, now))
            row = db.execute("SELECT id FROM jobs WHERE state='queued' "
                             'ORDER BY created_at,id LIMIT 1').fetchone()
            if row is None:
                return None
            db.execute("UPDATE jobs SET state='running',attempts=attempts+1,"
                       'generation=generation+1,owner=?,lease_until=? WHERE id=?',
                       (owner, now + lease_seconds, row['id']))
            return dict(db.execute('SELECT * FROM jobs WHERE id=?', (row['id'],)).fetchone())

    def complete(self, claim, result):
        encoded = json.dumps(result, sort_keys=True, allow_nan=False)
        with self.connection(write=True) as db:
            updated = db.execute("UPDATE jobs SET state='succeeded',owner=NULL,lease_until=NULL "
                                 "WHERE id=? AND state='running' AND owner=? "
                                 'AND generation=? AND lease_until>?',
                                 (claim['id'], claim['owner'], claim['generation'], self.clock()))
            if updated.rowcount != 1:
                raise ValueError('Lease expired or claimant superseded')
            db.execute('INSERT INTO results VALUES(?,?)', (claim['id'], encoded))
