# BOOKING CONTRACT

Booking creation must be transactional and concurrency-safe. Availability/inventory must prevent double booking. Price calculations must be deterministic. Cancellation and inventory restoration must be tested.

## Booking Expiry (Checkpoint 14)

### Requirements
- Pending bookings must have an expiry timestamp (15 minutes from creation)
- Expiry must be automatically set when booking is created with pending status
- Expired bookings must be automatically cancelled with inventory restoration
- Expiry cancellation must set specific cancellation reason
- State transitions must be deterministic and validated
- Management command must be available for processing expired bookings

### State Transitions
- pending -> cancelled (user cancellation via cancel endpoint)
- pending -> cancelled (expiry via process_expired_bookings)
- pending -> confirmed (payment completion - future implementation)
- confirmed -> cancelled (user cancellation)
- confirmed -> completed (checkout - future implementation)
- confirmed -> no_show (guest didn't arrive - future implementation)

### Expiry Process
1. Booking created with pending status automatically gets expires_at = created_at + 15 minutes
2. Management command or periodic task finds bookings where status='pending' and expires_at < now
3. Each expired booking calls expire_booking() method
4. expire_booking() validates status is pending
5. Uses transaction to restore inventory atomically
6. Sets status to cancelled, cancelled_at, and cancellation_reason
7. Returns count of processed bookings

### Inventory Restoration
- Expiry must restore inventory using same logic as cancellation
- Must use row-level locking (SELECT FOR UPDATE) for safety
- Must handle transaction rollback on errors
- Must restore exact number of rooms booked for each date

### Security Requirements
- Expiry field must be indexed for performance
- Expiry cannot be manipulated through API (read-only)
- Only pending bookings can be expired
- Concurrent expiry attempts must be handled safely
- Management command must have proper error handling
