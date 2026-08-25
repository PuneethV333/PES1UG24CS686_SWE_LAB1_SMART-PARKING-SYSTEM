# PES1UG24CS686_SWE_LAB1_SMART-PARKING-SYSTEM

**Lab 1: Requirements Engineering & UML Use-Case Modelling**  
**Student:** Puneeth V (PES1UG24CS686)  
**Project:** Smart Parking Space Rental & License Validator  
**Domain:** Smart Cities, Transport & Logistics  
**Stakeholders:** Vehicle Owner, Parking Warden  

---

## Repository Structure

```
.
├── requirements/
│   ├── requirements_table.md    # Requirements table (markdown)
│   └── requirements_table.csv   # Requirements table (CSV for Excel)
├── use-case-diagram/
│   └── use_case_diagram.drawio  # UML Use-Case Diagram (open in diagrams.net / draw.io → export PDF)
├── use-case-flow/
│   └── use_case_flow_uc03_book_parking_space.md  # Use-Case Flow for UC-03
└── README.md
```

---

## Deliverables (per Lab 1 Spec)

| # | Deliverable | File(s) | Status |
|---|-------------|---------|--------|
| 1 | **Requirements Table** — 5 FRs (FR-001…FR-005) + 2 NFRs (NFR-001, NFR-002) with ID, Type, Description, Priority, Acceptance Criteria, Rationale | `requirements/requirements_table.md` (and `.csv`) | ✅ Done |
| 2 | **UML Use-Case Diagram** — Actors, ≥5 use cases, associations, ≥1 `«include»`, ≥1 `«extend»` | `use-case-diagram/use_case_diagram.drawio` | ✅ Done |
| 3 | **Use-Case Flow Document** — One core use case (UC-03 Book Parking Space) with Preconditions, Postconditions, Main Success Scenario, Alternate Flows | `use-case-flow/use_case_flow_uc03_book_parking_space.md` | ✅ Done |

---

## How to View / Export

- **Requirements Table:** Open `requirements/requirements_table.md` in any Markdown viewer, or import `requirements_table.csv` into Excel/Google Sheets.
- **Use-Case Diagram:** Open `use-case-diagram/use_case_diagram.drawio` in [diagrams.net (draw.io)](https://app.diagrams.net/) → *File → Import From → Device* → select the `.drawio` file. Then *File → Export As → PDF* for submission.
- **Use-Case Flow:** Open `use-case-flow/use_case_flow_uc03_book_parking_space.md` in any Markdown viewer; export to PDF via your editor (VS Code, Typora, etc.) or print to PDF.

---

## Use-Case Diagram Summary

**Actors:**
- Vehicle Owner (primary)
- Parking Warden (primary)
- Payment Gateway (secondary / system actor)

**Use Cases (≥7):**
- UC-01: Register / Login
- UC-02: Search Parking Spaces
- UC-03: Book Parking Space
- UC-04: Process Payment *(included by UC-03)*
- UC-05: Validate License & Check-in
- UC-06: Extend / Cancel Booking
- UC-07: View Booking History
- UC-08: Report Violation *(extends UC-05)*
- UC-09: Apply Promo Code *(extends UC-03)*

**Relationships:**
- `«include»`: UC-03 → UC-04 (booking always includes payment)
- `«extend»`: UC-05 → UC-08 (violation reported only when license invalid/expired)
- `«extend»`: UC-03 → UC-09 (promo code is optional)

---

## Core Use-Case Flow (UC-03)

**Book Parking Space** — covers search, reservation, payment, confirmation, and three alternate flows:
- AF-01: Payment declined / gateway error (retry once, then cancel)
- AF-02: Space taken by another user (race condition handling)
- AF-03: System error after payment success (auto-refund)

---

## Submission

All files committed to `main` branch. Push to GitHub:

```bash
git push origin main
```

Repository URL: https://github.com/PuneethV333/PES1UG24CS686_LAB1_SMART-PARKING-SYSTEM
