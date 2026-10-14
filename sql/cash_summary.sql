WITH received AS (
    SELECT order_id,SUM(amount_minor) AS received_minor FROM settlements GROUP BY order_id
)
SELECT o.currency,
       SUM(CASE WHEN o.payment_state='paid' THEN o.amount_minor ELSE 0 END) AS paid_order_minor,
       SUM(COALESCE(r.received_minor,0)) AS received_minor,
       SUM(CASE WHEN o.payment_state='pending' THEN o.amount_minor ELSE 0 END) AS pending_minor
FROM orders o LEFT JOIN received r ON r.order_id=o.id
GROUP BY o.currency ORDER BY o.currency;
