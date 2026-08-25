# Use-Case Flow Specification: UC-03 Book Parking Space

**Project:** Smart Parking Space Rental & License Validator  
**Actor:** Vehicle Owner  
**Use Case ID:** UC-03  
**Use Case Name:** Book Parking Space  
**Priority:** High  
**Related Requirements:** FR-002, FR-003, NFR-001  

---

## Preconditions

1. Vehicle Owner is registered and logged into the system (UC-01 completed).
2. At least one parking space is available for the desired time slot and location.
3. Payment Gateway service is reachable and operational.
4. Vehicle Owner has a verified payment method (UPI ID / saved card / wallet) on file or is ready to enter one.

## Postconditions

**On Success:**
- Parking space is reserved exclusively for the Vehicle Owner for the selected time slot.
- Payment is authorized and recorded.
- Booking confirmation with space details, slot timing, amount, and QR code is sent to Vehicle Owner (app/email/SMS).
- Space status updates to "Occupied/Reserved" in real-time for other users.

**On Failure:**
- No reservation is created; space remains available.
- No payment is captured.
- Vehicle Owner receives a clear error message with reason (e.g., "Space no longer available", "Payment declined").

---

## Main Success Scenario (MSS)

| Step | Actor Action | System Response |
|------|--------------|-----------------|
| 1 | Vehicle Owner opens app, taps **"Book a Space"**. | System displays **Search Parking Spaces** screen (UC-02) with map/list view. |
| 2 | Vehicle Owner enters **location**, selects **date/time slot**, applies optional filters (price, distance, EV charging). | System queries availability in real-time; returns matching spaces within **2 seconds** (NFR-001). |
| 3 | Vehicle Owner selects a **specific parking space** from results. | System shows space details (address, photos, rate, amenities) and **"Reserve & Pay"** button. |
| 4 | Vehicle Owner taps **"Reserve & Pay"**. | System **locks the space** for this user for **5 minutes** (soft hold) to prevent double-booking. |
| 5 | System presents **Payment Summary**: space, slot, duration, base fare, taxes, total. | Vehicle Owner reviews; may optionally tap **"Apply Promo Code"** (UC-09 extend). |
| 6 | Vehicle Owner selects **payment method** (UPI / saved card / wallet) and confirms. | System initiates **Process Payment** (UC-04 «include») via Payment Gateway. |
| 7 | Payment Gateway returns **authorization success**. | System: (a) creates **Booking Record** (space ID, user ID, slot, amount, timestamp, status=CONFIRMED); (b) marks space **Reserved** for the slot; (c) generates **QR code** for check-in. |
| 8 | System displays **Booking Confirmation** screen with QR code, space navigation link, and "Add to Calendar". | Confirmation sent via **push notification, email, and SMS**. |
| 9 | Vehicle Owner acknowledges confirmation. | **Use case ends successfully.** |

---

## Alternate Flow(s)

### AF-01: Payment Declined / Gateway Error
**Trigger:** Step 7 — Payment Gateway returns *decline*, *timeout*, or *network error*.

| Step | Actor Action | System Response |
|------|--------------|-----------------|
| 7a1 | — | System displays **Payment Failed** message with reason (e.g., "Insufficient funds", "Card expired", "Gateway timeout"). |
| 7a2 | — | System **releases the 5-min hold** on the space; space becomes available to others immediately. |
| 7a3 | Vehicle Owner taps **"Try Another Payment Method"**. | System returns to **Step 5** (Payment Summary) with previous promo (if any) retained. |
| 7a4 | Vehicle Owner selects a different payment method and confirms. | System retries **Process Payment** (UC-04). |
| 7a5 | *If second attempt fails:* System shows **"Payment failed twice. Booking cancelled. Please try again later."** | Soft hold released; booking record **not created**; Vehicle Owner returned to Search screen (Step 2). |

### AF-02: Space No Longer Available (Race Condition)
**Trigger:** Step 4 — After Vehicle Owner taps "Reserve & Pay", another user completes booking for the same space/slot before payment finishes.

| Step | Actor Action | System Response |
|------|--------------|-----------------|
| 4a1 | — | System detects conflict when attempting to create booking record (optimistic lock / unique constraint violation). |
| 4a2 | — | System **aborts payment initiation** (voids any pending auth). |
| 4a3 | Vehicle Owner sees **"Space just booked by another user. Please select another space."** | System returns to **Step 2** (Search Results) with updated availability; no charge attempted. |

### AF-03: Network / System Error During Booking Creation
**Trigger:** Step 7 — Payment succeeds but booking record creation fails (DB error, timeout).

| Step | Actor Action | System Response |
|------|--------------|-----------------|
| 7b1 | — | System detects booking persistence failure **after** payment authorization. |
| 7b2 | — | System **automatically initiates refund/void** via Payment Gateway (idempotent). |
| 7b3 | Vehicle Owner sees **"Booking could not be confirmed. Payment will be refunded within 5–7 business days. Please try again."** | Space hold released; no booking record; error logged for ops review. |

---

## Non-Functional Notes

- **Latency:** Steps 2→3 (search→select) and 6→7 (pay→confirm) must meet NFR-001 (p95 ≤ 2 s).
- **Security:** All PII & payment data encrypted in transit (TLS 1.2+) and at rest (AES-256) per NFR-002.
- **Concurrency:** Soft hold (5 min) + DB unique constraint on (space_id, slot_start, slot_end) prevents double-booking under load.

---

## Traceability

| Flow Step | Requirement(s) |
|-----------|----------------|
| 1–3 | FR-002 (search/display) |
| 4–7 | FR-003 (reserve + pay), NFR-001 (latency) |
| 5 (optional) | FR-003 + UC-09 «extend» |
| 6–7 | UC-04 «include» Process Payment |
| 7, 8 | FR-003 (confirmation), NFR-002 (data protection) |
| AF-01, AF-02, AF-03 | FR-003 (atomicity), NFR-001 (error handling) |