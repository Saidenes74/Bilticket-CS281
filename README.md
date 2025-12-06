# Bilticket – Theatre Ticket Selling System (CS281 Project)

This repository contains the full implementation and documentation of **Bilticket**, a theatre ticket management system created
for the CS281 Database Systems course.

The project includes:
- A fully designed **SQLite database**
- Python scripts for interacting with the DB
- Functional requirements implementation
- Admin / Customer / Theatre Officer flows
- Booking, staging, seats, comments, plays & artists

---

## 📂 Repository Structure
Bilticket is organised into a small set of artefacts while we expand the implementation:

- `docs/functional_requirements_theatre.md` – end-to-end functional requirements for customers, admins, and theatre officers.
- `2.py` – SQLite-backed CLI prototype that fulfils the requirements (signup/login, profile management, play search, seat
  booking, admin staging creation, officer bookings lookup, and customer comments).

### Running the prototype
1. Ensure Python 3.10+ is available.
2. Reset and seed the database (optional but recommended):
   ```bash
   python 2.py --init-only
   ```
3. Launch the interactive CLI:
   ```bash
   python 2.py
   ```

Demo credentials after seeding:
- Customer: `customer@example.com` / `pass`
- Admin: `admin@example.com` / `admin`
- Theatre officer: `officer@example.com` / `officer`

When booking seats as a customer, ensure the profile includes a card number. Admins can create new plays, assign artists,
and create non-overlapping stagings with automatic seat creation. Officers can filter upcoming stagings for their theatre
and view attendee contact details and booked seats.
