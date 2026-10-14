-- Preaggregate settlements before joining: multiple receipts must not multiply order value.
WITH received AS (
    SELECT order_id, SUM(amount_minor) AS received_minor
    FROM settlements GROUP BY order_id
), classified AS (
    SELECT o.*, COALESCE(r.received_minor,0) AS received_minor,
           CASE
             WHEN o.fulfillment_state='unknown' THEN 'reconcile_unknown_outcome'
             WHEN o.fulfillment_state='submitted' AND o.external_reference IS NULL
               THEN 'missing_fulfillment_reference'
             WHEN o.payment_state='paid' AND o.external_reference IS NULL
               THEN 'paid_without_fulfillment'
             ELSE NULL
           END AS exception
    FROM orders AS o LEFT JOIN received AS r ON r.order_id=o.id
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY currency ORDER BY created_at,id) AS priority
    FROM classified WHERE exception IS NOT NULL
)
SELECT id,currency,amount_minor,received_minor,exception,priority
FROM ranked ORDER BY currency,priority;
