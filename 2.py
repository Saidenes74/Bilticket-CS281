"""Bilticket Theatre Ticket Selling System prototype.

This script builds a small SQLite-backed prototype that satisfies the
functional flows described in ``docs/functional_requirements_theatre.md``.
It focuses on correctness of domain logic (seat availability, staging
conflicts, role-based actions) rather than UI polish.

Run ``python 2.py`` for the interactive text UI or ``python 2.py --init-only``
to reset and seed the database without entering the UI.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

DB_PATH = Path("Bilticket.db")
DEFAULT_SEAT_COUNT = 20


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed: bool = True) -> None:
    """Create tables and seed demo data."""
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('customer', 'admin', 'officer')),
            phone TEXT,
            address TEXT,
            card_number TEXT,
            theatre_id INTEGER,
            FOREIGN KEY (theatre_id) REFERENCES theatres(id)
        );

        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS plays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            playwright TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS play_artists (
            play_id INTEGER REFERENCES plays(id) ON DELETE CASCADE,
            artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
            PRIMARY KEY (play_id, artist_id)
        );

        CREATE TABLE IF NOT EXISTS theatres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS stagings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            play_id INTEGER NOT NULL REFERENCES plays(id) ON DELETE CASCADE,
            theatre_id INTEGER NOT NULL REFERENCES theatres(id),
            start_time TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staging_id INTEGER NOT NULL REFERENCES stagings(id) ON DELETE CASCADE,
            seat_label TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('empty', 'booked'))
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            staging_id INTEGER NOT NULL REFERENCES stagings(id),
            seat_id INTEGER NOT NULL REFERENCES seats(id),
            booked_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            staging_id INTEGER NOT NULL REFERENCES stagings(id),
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )

    if not seed:
        conn.commit()
        conn.close()
        return

    # Only seed when empty.
    user_count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count:
        conn.close()
        return

    # Seed base entities.
    theatres = [
        ("Grand Oak Theatre", "123 Main St", "555-1000"),
        ("Riverfront Stage", "987 Riverside", "555-2000"),
    ]
    cur.executemany("INSERT INTO theatres(name, address, phone) VALUES(?, ?, ?)", theatres)

    artists = [
        ("Ayla Demir", "Lead"),
        ("Kenan Kaya", "Supporting"),
        ("Selin Ucar", "Director"),
        ("Mert Aydin", "Playwright"),
    ]
    cur.executemany("INSERT INTO artists(name, role) VALUES(?, ?)", artists)

    plays = [
        ("Shadows of Anatolia", "Drama", "Mert Aydin", "Family saga across generations."),
        ("Midnight Laughter", "Comedy", "Ece Ersoy", "A night of mistaken identities."),
    ]
    cur.executemany(
        "INSERT INTO plays(title, genre, playwright, description) VALUES(?, ?, ?, ?)", plays
    )

    # link artists to first play
    cur.executemany(
        "INSERT INTO play_artists(play_id, artist_id) VALUES(1, ?)",
        [(1,), (2,), (3,), (4,)],
    )

    # seed stagings
    now = dt.datetime.now()
    staging_rows = [
        (1, 1, (now + dt.timedelta(days=2)).isoformat(timespec="minutes")),
        (1, 2, (now + dt.timedelta(days=4)).isoformat(timespec="minutes")),
        (2, 1, (now + dt.timedelta(days=6)).isoformat(timespec="minutes")),
    ]
    cur.executemany(
        "INSERT INTO stagings(play_id, theatre_id, start_time) VALUES(?, ?, ?)", staging_rows
    )

    # seed seats for each staging
    staging_ids = [row[0] for row in cur.execute("SELECT id FROM stagings").fetchall()]
    for staging_id in staging_ids:
        make_seats(cur, staging_id, DEFAULT_SEAT_COUNT)

    # seed users
    users = [
        ("customer@example.com", "pass", "Ada", "Customer", "customer", None, None, "4111111111111111", None),
        ("admin@example.com", "admin", "Admin", "User", "admin", None, None, None, None),
        ("officer@example.com", "officer", "Olcay", "Officer", "officer", "555-9999", None, None, 1),
    ]
    cur.executemany(
        """
        INSERT INTO users(email, password, first_name, last_name, role, phone, address, card_number, theatre_id)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        users,
    )

    conn.commit()
    conn.close()


def make_seats(cur: sqlite3.Cursor, staging_id: int, count: int) -> None:
    seats = [(staging_id, f"Seat {i+1}", "empty") for i in range(count)]
    cur.executemany(
        "INSERT INTO seats(staging_id, seat_label, status) VALUES(?, ?, ?)", seats
    )


# ---------------------------------------------------------------------------
# Models & utilities
# ---------------------------------------------------------------------------


def mask_name(first: str, last: str) -> str:
    return f"{first[0]}*** {last[0]}***"


def iso_to_dt(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value)


@dataclass
class User:
    id: int
    email: str
    password: str
    first_name: str
    last_name: str
    role: str
    phone: Optional[str]
    address: Optional[str]
    card_number: Optional[str]
    theatre_id: Optional[int]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        return cls(**dict(row))


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def lookup_user(email: str, password: str) -> Optional[User]:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?", (email, password)
    ).fetchone()
    conn.close()
    return User.from_row(row) if row else None


def create_customer(email: str, password: str, first: str, last: str) -> User:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users(email, password, first_name, last_name, role) VALUES(?, ?, ?, ?, 'customer')",
        (email, password, first, last),
    )
    conn.commit()
    user = lookup_user(email, password)
    conn.close()
    return user  # type: ignore[return-value]


def update_profile(user: User, phone: str, address: str, card_number: str) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE users SET phone = ?, address = ?, card_number = ? WHERE id = ?",
        (phone, address, card_number, user.id),
    )
    conn.commit()
    conn.close()


def list_plays(filters: Optional[dict] = None) -> List[sqlite3.Row]:
    filters = filters or {}
    clauses = []
    args: List[str] = []
    for field in ("title", "genre", "playwright"):
        if filters.get(field):
            clauses.append(f"{field} LIKE ?")
            args.append(f"%{filters[field]}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    conn = get_conn()
    rows = conn.execute(f"SELECT * FROM plays {where} ORDER BY title", args).fetchall()
    conn.close()
    return rows


def play_stagings(play_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT s.id, s.start_time, t.name AS theatre_name,
               SUM(CASE WHEN seats.status = 'empty' THEN 1 ELSE 0 END) AS empty_seats
        FROM stagings s
        JOIN theatres t ON s.theatre_id = t.id
        LEFT JOIN seats ON seats.staging_id = s.id
        WHERE s.play_id = ?
        GROUP BY s.id, s.start_time, t.name
        ORDER BY s.start_time
        """,
        (play_id,),
    ).fetchall()
    conn.close()
    return rows


def staging_detail(staging_id: int) -> Tuple[sqlite3.Row, List[sqlite3.Row]]:
    conn = get_conn()
    staging = conn.execute(
        """
        SELECT s.*, p.title, t.name AS theatre_name, t.address, t.phone
        FROM stagings s
        JOIN plays p ON p.id = s.play_id
        JOIN theatres t ON t.id = s.theatre_id
        WHERE s.id = ?
        """,
        (staging_id,),
    ).fetchone()
    seats = conn.execute(
        "SELECT * FROM seats WHERE staging_id = ? AND status = 'empty' ORDER BY id",
        (staging_id,),
    ).fetchall()
    conn.close()
    return staging, seats


def book_seats(user: User, staging_id: int, seat_ids: Sequence[int]) -> None:
    if not user.card_number:
        raise ValueError("Customer profile must contain card information before booking.")

    conn = get_conn()
    cur = conn.cursor()
    # Validate seats belong and are empty
    placeholders = ",".join("?" for _ in seat_ids)
    rows = cur.execute(
        f"SELECT id, status FROM seats WHERE id IN ({placeholders}) AND staging_id = ?",
        (*seat_ids, staging_id),
    ).fetchall()
    if len(rows) != len(seat_ids):
        conn.close()
        raise ValueError("Invalid seat selection for this staging.")
    if any(row["status"] != "empty" for row in rows):
        conn.close()
        raise ValueError("One or more seats are already booked.")

    now = dt.datetime.now().isoformat(timespec="seconds")
    for seat_id in seat_ids:
        cur.execute("UPDATE seats SET status='booked' WHERE id = ?", (seat_id,))
        cur.execute(
            "INSERT INTO bookings(user_id, staging_id, seat_id, booked_at) VALUES(?, ?, ?, ?)",
            (user.id, staging_id, seat_id, now),
        )
    conn.commit()
    conn.close()


def user_bookings(user_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT b.id, b.booked_at, s.start_time, p.title, t.name AS theatre_name, seats.seat_label
        FROM bookings b
        JOIN seats ON seats.id = b.seat_id
        JOIN stagings s ON s.id = b.staging_id
        JOIN plays p ON p.id = s.play_id
        JOIN theatres t ON t.id = s.theatre_id
        WHERE b.user_id = ?
        ORDER BY b.booked_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def attended_stagings_without_comment(user_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT s.id, p.title, s.start_time
        FROM bookings b
        JOIN stagings s ON s.id = b.staging_id
        JOIN plays p ON p.id = s.play_id
        WHERE b.user_id = ?
        EXCEPT
        SELECT c.staging_id, p2.title, s2.start_time
        FROM comments c
        JOIN stagings s2 ON s2.id = c.staging_id
        JOIN plays p2 ON p2.id = s2.play_id
        WHERE c.user_id = ?
        ORDER BY start_time
        """,
        (user_id, user_id),
    ).fetchall()
    conn.close()
    return rows


def add_comment(user: User, staging_id: int, body: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO comments(user_id, staging_id, body, created_at) VALUES(?, ?, ?, ?)",
        (user.id, staging_id, body, dt.datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def play_comments(play_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT c.body, c.created_at, s.start_time, u.first_name, u.last_name
        FROM comments c
        JOIN stagings s ON s.id = c.staging_id
        JOIN users u ON u.id = c.user_id
        WHERE s.play_id = ?
        ORDER BY c.created_at DESC
        """,
        (play_id,),
    ).fetchall()
    conn.close()
    return rows


def list_artists() -> List[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM artists ORDER BY name").fetchall()
    conn.close()
    return rows


def list_theatres() -> List[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM theatres ORDER BY name").fetchall()
    conn.close()
    return rows


def create_play(title: str, genre: str, playwright: str, description: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO plays(title, genre, playwright, description) VALUES(?, ?, ?, ?)",
        (title, genre, playwright, description),
    )
    play_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(play_id)


def assign_artists(play_id: int, artist_ids: Iterable[int]) -> None:
    conn = get_conn()
    conn.executemany(
        "INSERT OR IGNORE INTO play_artists(play_id, artist_id) VALUES(?, ?)",
        [(play_id, artist_id) for artist_id in artist_ids],
    )
    conn.commit()
    conn.close()


def staging_conflicts(theatre_id: int, start_time: dt.datetime) -> bool:
    conn = get_conn()
    clash = conn.execute(
        "SELECT 1 FROM stagings WHERE theatre_id = ? AND start_time = ?",
        (theatre_id, start_time.isoformat(timespec="minutes")),
    ).fetchone()
    conn.close()
    return bool(clash)


def create_staging(play_id: int, theatre_id: int, start_time: dt.datetime) -> int:
    if staging_conflicts(theatre_id, start_time):
        raise ValueError("Staging overlaps with an existing staging in this theatre.")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO stagings(play_id, theatre_id, start_time) VALUES(?, ?, ?)",
        (play_id, theatre_id, start_time.isoformat(timespec="minutes")),
    )
    staging_id = int(cur.lastrowid)
    make_seats(cur, staging_id, DEFAULT_SEAT_COUNT)
    conn.commit()
    conn.close()
    return staging_id


def edit_staging(staging_id: int, new_start: dt.datetime) -> None:
    conn = get_conn()
    theatre_id = conn.execute(
        "SELECT theatre_id FROM stagings WHERE id = ?", (staging_id,)
    ).fetchone()[0]
    if staging_conflicts(theatre_id, new_start):
        conn.close()
        raise ValueError("New time overlaps with another staging in this theatre.")
    conn.execute(
        "UPDATE stagings SET start_time = ? WHERE id = ?",
        (new_start.isoformat(timespec="minutes"), staging_id),
    )
    conn.commit()
    conn.close()


def play_details(play_id: int) -> sqlite3.Row:
    conn = get_conn()
    play = conn.execute("SELECT * FROM plays WHERE id = ?", (play_id,)).fetchone()
    conn.close()
    return play


def play_artists_rows(play_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT a.* FROM artists a
        JOIN play_artists pa ON pa.artist_id = a.id
        WHERE pa.play_id = ? ORDER BY a.name
        """,
        (play_id,),
    ).fetchall()
    conn.close()
    return rows


def theatre_officer_stagings(theatre_id: int) -> List[sqlite3.Row]:
    now_iso = dt.datetime.now().isoformat(timespec="minutes")
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT s.id, s.start_time, p.title
        FROM stagings s
        JOIN plays p ON p.id = s.play_id
        WHERE s.theatre_id = ? AND s.start_time >= ?
        ORDER BY s.start_time
        """,
        (theatre_id, now_iso),
    ).fetchall()
    conn.close()
    return rows


def staging_bookings(staging_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT u.first_name, u.last_name, u.email, u.phone, seats.seat_label
        FROM bookings b
        JOIN users u ON u.id = b.user_id
        JOIN seats ON seats.id = b.seat_id
        WHERE b.staging_id = ?
        ORDER BY seats.seat_label
        """,
        (staging_id,),
    ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def prompt_int(prompt: str, valid: Iterable[int]) -> int:
    choices = list(valid)
    while True:
        value = input(f"{prompt} {choices}: ")
        try:
            choice = int(value)
            if choice in choices:
                return choice
        except ValueError:
            pass
        print("Please choose a valid option.")


def customer_flow(user: User) -> None:
    while True:
        print("\nCustomer Menu: 1) Update profile 2) Search plays 3) My bookings 4) Comment 0) Logout")
        choice = input("Choice: ")
        if choice == "1":
            phone = input("Phone: ")
            address = input("Address: ")
            card = input("Card number (required to book): ")
            update_profile(user, phone, address, card)
            user.card_number = card
            print("Profile updated.")
        elif choice == "2":
            title = input("Filter title (enter to skip): ")
            genre = input("Filter genre: ")
            playwright = input("Filter playwright: ")
            plays = list_plays({"title": title, "genre": genre, "playwright": playwright})
            for row in plays:
                print(f"{row['id']}) {row['title']} [{row['genre']}] by {row['playwright']}")
            if not plays:
                continue
            play_id = prompt_int("Choose play", [row["id"] for row in plays])
            stagings = play_stagings(play_id)
            for st in stagings:
                print(
                    f"{st['id']}) {st['start_time']} at {st['theatre_name']} – empty seats: {st['empty_seats']}"
                )
            if not stagings:
                continue
            staging_id = prompt_int("Choose staging", [st["id"] for st in stagings])
            staging, seats = staging_detail(staging_id)
            print(
                f"Theatre: {staging['theatre_name']} ({staging['address']}, {staging['phone']}) | Start: {staging['start_time']}"
            )
            print("Available seats:")
            for seat in seats:
                print(f"  {seat['id']}) {seat['seat_label']}")
            if len(seats) < 2:
                print("Not enough empty seats to book.")
                continue
            chosen = []
            while len(chosen) < 2:
                seat_id = prompt_int("Pick seat", [s["id"] for s in seats if s["id"] not in chosen])
                chosen.append(seat_id)
            try:
                book_seats(user, staging_id, chosen)
                print("Booking successful!")
            except ValueError as exc:
                print(f"Booking failed: {exc}")
        elif choice == "3":
            for row in user_bookings(user.id):
                print(
                    f"{row['booked_at']}: {row['title']} at {row['theatre_name']} on {row['start_time']} – {row['seat_label']}"
                )
        elif choice == "4":
            options = attended_stagings_without_comment(user.id)
            if not options:
                print("No attended stagings without comments.")
                continue
            for row in options:
                print(f"{row['id']}) {row['title']} on {row['start_time']}")
            chosen = prompt_int("Comment on staging", [row["id"] for row in options])
            body = input("Comment text: ")
            add_comment(user, chosen, body)
            print("Comment saved.")
        elif choice == "0":
            break


def admin_flow(user: User) -> None:
    while True:
        print("\nAdmin Menu: 1) Create play 2) Edit staging 3) List plays 0) Logout")
        choice = input("Choice: ")
        if choice == "1":
            title = input("Title: ")
            genre = input("Genre: ")
            playwright = input("Playwright: ")
            description = input("Description: ")
            play_id = create_play(title, genre, playwright, description)
            print(f"Play created with id {play_id}")

            artist_ids = select_ids("artists", list_artists())
            assign_artists(play_id, artist_ids)

            theatre_rows = list_theatres()
            theatre_ids = select_ids("theatres", theatre_rows)
            created = 0
            for theatre_id in theatre_ids:
                for i in range(2):
                    start_str = input(
                        f"Enter start datetime (YYYY-MM-DD HH:MM) for staging {i+1} at theatre {theatre_id}: "
                    )
                    start_dt = dt.datetime.strptime(start_str, "%Y-%m-%d %H:%M")
                    try:
                        create_staging(play_id, theatre_id, start_dt)
                        created += 1
                    except ValueError as exc:
                        print(f"Skipping staging: {exc}")
            if created < 2:
                print("Warning: fewer than two stagings created due to conflicts.")
            else:
                print(f"Created {created} stagings")
        elif choice == "2":
            plays = list_plays()
            for row in plays:
                print(f"{row['id']}) {row['title']}")
            if not plays:
                continue
            play_id = prompt_int("Select play", [p["id"] for p in plays])
            stagings = play_stagings(play_id)
            if not stagings:
                print("No stagings to edit.")
                continue
            for st in stagings:
                print(f"{st['id']}) {st['start_time']} at {st['theatre_name']}")
            staging_id = prompt_int("Select staging", [s["id"] for s in stagings])
            new_time_str = input("New start datetime (YYYY-MM-DD HH:MM): ")
            new_dt = dt.datetime.strptime(new_time_str, "%Y-%m-%d %H:%M")
            try:
                edit_staging(staging_id, new_dt)
                print("Staging updated.")
            except ValueError as exc:
                print(f"Update failed: {exc}")
        elif choice == "3":
            for play in list_plays():
                print(f"{play['id']}) {play['title']} – {play['genre']} by {play['playwright']}")
                artists = play_artists_rows(play["id"])
                for artist in artists:
                    print(f"   • {artist['name']} ({artist['role']})")
                comments = play_comments(play["id"])
                for comment in comments:
                    masked = mask_name(comment["first_name"], comment["last_name"])
                    print(
                        f"   ◦ Comment by {masked} on staging {comment['start_time']} ({comment['created_at']}): {comment['body']}"
                    )
        elif choice == "0":
            break


def officer_flow(user: User) -> None:
    assert user.theatre_id, "Officer must have theatre assignment"
    while True:
        print("\nOfficer Menu: 1) Upcoming stagings 0) Logout")
        choice = input("Choice: ")
        if choice == "1":
            stagings = theatre_officer_stagings(user.theatre_id)
            for st in stagings:
                print(f"{st['id']}) {st['start_time']} – {st['title']}")
            if not stagings:
                print("No upcoming stagings.")
                continue
            filter_from = input("Filter start from (YYYY-MM-DD, optional): ")
            filter_to = input("Filter to (YYYY-MM-DD, optional): ")
            filtered = []
            for st in stagings:
                date = iso_to_dt(st["start_time"]).date()
                if filter_from:
                    if date < dt.date.fromisoformat(filter_from):
                        continue
                if filter_to:
                    if date > dt.date.fromisoformat(filter_to):
                        continue
                filtered.append(st)
            if not filtered:
                print("No stagings in range.")
                continue
            for st in filtered:
                print(f"{st['id']}) {st['start_time']} – {st['title']}")
            chosen = prompt_int("Select closest staging", [st["id"] for st in filtered])
            bookings = staging_bookings(chosen)
            if not bookings:
                print("No bookings yet.")
            for row in bookings:
                print(
                    f"{row['seat_label']}: {row['first_name']} {row['last_name']} / {row['email']} / {row['phone']}"
                )
        elif choice == "0":
            break


def select_ids(label: str, rows: List[sqlite3.Row]) -> List[int]:
    print(f"Select {label} by entering comma-separated ids (leave blank for none):")
    for row in rows:
        print(f"  {row['id']}) {row.get('name', row.get('title'))}")
    ids_raw = input("IDs: ")
    if not ids_raw.strip():
        return []
    return [int(i.strip()) for i in ids_raw.split(",") if i.strip()]


# ---------------------------------------------------------------------------
# Interactive entrypoint
# ---------------------------------------------------------------------------


def interactive_ui() -> None:
    while True:
        print("\nWelcome to Bilticket")
        mode = input("1) Sign up 2) Log in 0) Quit: ")
        if mode == "1":
            email = input("Email: ")
            password = input("Password: ")
            first = input("First name: ")
            last = input("Last name: ")
            try:
                user = create_customer(email, password, first, last)
                print("Account created. You can now log in.")
            except sqlite3.IntegrityError:
                print("Email already exists.")
        elif mode == "2":
            email = input("Email: ")
            password = input("Password: ")
            user = lookup_user(email, password)
            if not user:
                print("Invalid credentials")
                continue
            if user.role == "customer":
                customer_flow(user)
            elif user.role == "admin":
                admin_flow(user)
            elif user.role == "officer":
                officer_flow(user)
        elif mode == "0":
            print("Goodbye")
            break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bilticket CLI prototype")
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Initialise and seed the database then exit",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    init_db(seed=True)
    if not args.init_only:
        interactive_ui()
