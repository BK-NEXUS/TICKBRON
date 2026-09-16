# PAYMENTS CONTRACT

Payments use an adapter model. Webhooks must be signed, timestamp/replay resistant and idempotent. Raw card data must not be stored. Booking/payment state transitions must be deterministic and auditable.
