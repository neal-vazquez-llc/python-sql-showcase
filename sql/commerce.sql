-- Synthetic ledger. Currency and minor-unit amounts remain separate.
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    currency TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK(amount_minor >= 0),
    payment_state TEXT NOT NULL CHECK(payment_state IN ('paid','pending','refunded')),
    fulfillment_state TEXT NOT NULL CHECK(fulfillment_state IN ('new','unknown','submitted')),
    external_reference TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE settlements (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(id),
    amount_minor INTEGER NOT NULL CHECK(amount_minor > 0)
);
