"""Offline analytical demonstration; does not connect to payment providers."""
import sqlite3
from .queue import SQL


def demo_database():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript((SQL / 'commerce.sql').read_text())
    db.executemany('INSERT INTO orders VALUES(?,?,?,?,?,?,?)', [
        ('demo-01','USD',12000,'paid','new',None,'2026-01-01'),
        ('demo-02','USD',8000,'paid','unknown',None,'2026-01-02'),
        ('demo-03','USD',6000,'pending','new',None,'2026-01-03'),
        ('demo-04','EUR',9000,'paid','submitted',None,'2026-01-01'),
        ('demo-05','USD',5000,'paid','submitted','synthetic-ref','2026-01-04'),
    ])
    db.executemany('INSERT INTO settlements VALUES(?,?,?)', [
        ('receipt-01','demo-01',7000), ('receipt-02','demo-01',5000),
        ('receipt-03','demo-05',5000),
    ])
    return db


def report(db, name):
    if name not in {'reconciliation', 'cash_summary'}:
        raise ValueError('Unknown report')
    return [dict(row) for row in db.execute((SQL / f'{name}.sql').read_text())]
