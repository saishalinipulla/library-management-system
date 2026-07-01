"""
Library Management System - Web Version (Flask + SQLite)
Data persists permanently across restarts and redeploys.
Run locally: python app.py → visit http://127.0.0.1:5000
"""

import sqlite3
import os
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "library-secret-key-2024"
DB = "library.db"
LOAN_DAYS = 14


# ---------- Database setup ----------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            isbn TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            total_copies INTEGER DEFAULT 1,
            available_copies INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS members (
            member_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS borrowed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT NOT NULL,
            isbn TEXT NOT NULL,
            due_date TEXT NOT NULL,
            FOREIGN KEY(member_id) REFERENCES members(member_id),
            FOREIGN KEY(isbn) REFERENCES books(isbn)
        );
    """)
    conn.commit()
    conn.close()


# ---------- HTML template ----------
BASE = """
<!doctype html>
<html>
<head>
  <title>Library Management System</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: Arial, sans-serif;
      background: #f0f4f8;
      padding: 15px;
    }

    .container {
      width: 100%;
      max-width: 1000px;
      margin: 0 auto;
    }

    h1 { color: #1e3a5f; font-size: clamp(18px, 4vw, 28px); margin-bottom: 15px; }
    h2 { color: #1e3a5f; font-size: clamp(15px, 3vw, 22px); margin: 15px 0 10px; }
    h3 { color: #1e3a5f; font-size: clamp(13px, 2.5vw, 18px); margin-bottom: 10px; }

    /* NAV */
    nav {
      background: #1e3a5f;
      padding: 10px 15px;
      border-radius: 8px;
      margin-bottom: 20px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    nav a {
      text-decoration: none;
      color: white;
      font-weight: bold;
      font-size: clamp(12px, 2.5vw, 15px);
      padding: 6px 10px;
      border-radius: 5px;
      flex: 1 1 auto;
      text-align: center;
    }
    nav a:hover { background: #2563eb; }

    /* TABLE - scrollable on small screens */
    .table-wrap { overflow-x: auto; width: 100%; }
    table {
      width: 100%;
      min-width: 400px;
      border-collapse: collapse;
      background: white;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    }
    th, td {
      border: 1px solid #e2e8f0;
      padding: clamp(6px, 1.5vw, 12px);
      text-align: left;
      font-size: clamp(11px, 2vw, 14px);
    }
    th { background: #1e3a5f; color: white; }
    tr:hover { background: #f8fafc; }

    /* FORM */
    form {
      background: white;
      padding: clamp(12px, 3vw, 20px);
      border-radius: 8px;
      margin-top: 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    }
    input {
      padding: 8px;
      margin: 5px 0;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      width: 100%;
      max-width: 320px;
      font-size: 14px;
      display: block;
    }
    button {
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      padding: 10px 20px;
      margin-top: 10px;
      font-size: 14px;
      width: 100%;
      max-width: 320px;
    }
    button:hover { background: #1d4ed8; }

    /* ALERTS */
    .flash-success { background: #d1fae5; padding: 10px 15px; border-radius: 6px; margin-bottom: 15px; color: #065f46; font-size: 14px; }
    .flash-err     { background: #fee2e2; padding: 10px 15px; border-radius: 6px; margin-bottom: 15px; color: #991b1b; font-size: 14px; }

    /* MISC */
    .del          { color: #dc2626; text-decoration: none; font-weight: bold; }
    .del:hover    { color: #991b1b; }
    .borrow-link  { color: #2563eb; text-decoration: none; }
    .badge        { background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
    .overdue      { color: #dc2626; font-weight: bold; }
    a             { font-size: clamp(11px, 2vw, 14px); }

    /* LANDSCAPE phones (wider than 480px) */
    @media (min-width: 480px) {
      body { padding: 20px; }
      nav a { flex: 0 1 auto; text-align: left; }
      input, button { width: 280px; display: inline-block; }
    }

    /* TABLETS and desktops */
    @media (min-width: 768px) {
      body { padding: 30px; }
      input, button { width: 300px; }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>📚 Library Management System</h1>
    <nav>
      <a href="/">📖 Books</a>
      <a href="/members">👥 Members</a>
      <a href="/overdue">⚠️ Overdue</a>
    </nav>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for m in messages %}
          <div class="{{ 'flash-err' if '❌' in m else 'flash-success' }}">{{ m }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    {{ content|safe }}
  </div>
</body>
</html>
"""


# ---------- Routes ----------
@app.route("/")
def index():
    conn = get_db()
    books = conn.execute("SELECT * FROM books ORDER BY title").fetchall()
    conn.close()
    rows = "".join(
        f"<tr><td>{b['isbn']}</td><td>{b['title']}</td><td>{b['author']}</td>"
        f"<td>{b['available_copies']}/{b['total_copies']}</td>"
        f"<td><a class='borrow-link' href='/borrow/{b['isbn']}'>Borrow</a> &nbsp;"
        f"<a class='del' href='/delete/{b['isbn']}' onclick=\"return confirm('Delete this book and all its borrow records?')\">Delete</a></td></tr>"
        for b in books
    )
    content = f"""
    <h2>All Books</h2>
    <div class="table-wrap">
    <table>
      <tr><th>ISBN</th><th>Title</th><th>Author</th><th>Available</th><th>Actions</th></tr>
      {rows if rows else "<tr><td colspan='5' style='text-align:center'>No books added yet</td></tr>"}
    </table>
    </div>
    <form method="post" action="/add">
      <h3>➕ Add a Book</h3>
      ISBN: <input name="isbn" placeholder="e.g. 978-0-06-112008-4" required><br>
      Title: <input name="title" placeholder="Book title" required><br>
      Author: <input name="author" placeholder="Author name" required><br>
      Copies: <input name="copies" type="number" value="1" min="1" style="width:80px"><br>
      <button type="submit">Add Book</button>
    </form>
    """
    return render_template_string(BASE, content=content)


@app.route("/add", methods=["POST"])
def add_book():
    isbn = request.form["isbn"].strip()
    title = request.form["title"].strip()
    author = request.form["author"].strip()
    copies = int(request.form.get("copies", 1))
    conn = get_db()
    existing = conn.execute("SELECT * FROM books WHERE isbn=?", (isbn,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE books SET total_copies=total_copies+?, available_copies=available_copies+? WHERE isbn=?",
            (copies, copies, isbn)
        )
        flash(f"✅ Added {copies} more copies of '{existing['title']}'")
    else:
        conn.execute(
            "INSERT INTO books VALUES (?,?,?,?,?)",
            (isbn, title, author, copies, copies)
        )
        flash(f"✅ Book '{title}' added successfully")
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<isbn>")
def delete_book(isbn):
    conn = get_db()
    book = conn.execute("SELECT title FROM books WHERE isbn=?", (isbn,)).fetchone()
    if book:
        # Cascade: remove from all members' borrowed records first
        conn.execute("DELETE FROM borrowed WHERE isbn=?", (isbn,))
        conn.execute("DELETE FROM books WHERE isbn=?", (isbn,))
        conn.commit()
        flash(f"✅ '{book['title']}' deleted along with all its borrow records")
    else:
        flash("❌ Book not found")
    conn.close()
    return redirect(url_for("index"))


@app.route("/members")
def members():
    conn = get_db()
    members_list = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
    rows = ""
    for m in members_list:
        count = conn.execute(
            "SELECT COUNT(*) as c FROM borrowed WHERE member_id=?", (m["member_id"],)
        ).fetchone()["c"]
        rows += (
            f"<tr><td>{m['member_id']}</td><td>{m['name']}</td>"
            f"<td><span class='badge'>{count} book(s)</span></td>"
            f"<td><a href='/member/{m['member_id']}'>View</a></td></tr>"
        )
    conn.close()
    content = f"""
    <h2>All Members</h2>
    <div class="table-wrap">
    <table>
      <tr><th>ID</th><th>Name</th><th>Books Borrowed</th><th>Details</th></tr>
      {rows if rows else "<tr><td colspan='4' style='text-align:center'>No members added yet</td></tr>"}
    </table>
    </div>
    <form method="post" action="/add_member">
      <h3>➕ Add a Member</h3>
      Member ID: <input name="member_id" placeholder="e.g. M001" required><br>
      Name: <input name="name" placeholder="Full name" required><br>
      <button type="submit">Add Member</button>
    </form>
    """
    return render_template_string(BASE, content=content)


@app.route("/member/<member_id>")
def member_detail(member_id):
    conn = get_db()
    m = conn.execute("SELECT * FROM members WHERE member_id=?", (member_id,)).fetchone()
    if not m:
        flash("❌ Member not found")
        return redirect(url_for("members"))
    borrowed = conn.execute(
        "SELECT b.isbn, b.title, br.due_date FROM borrowed br JOIN books b ON br.isbn=b.isbn WHERE br.member_id=?",
        (member_id,)
    ).fetchall()
    conn.close()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = "".join(
        f"<tr><td>{r['title']}</td>"
        f"<td class='{'overdue' if r['due_date'] < today else ''}'>{r['due_date']} {'⚠️ OVERDUE' if r['due_date'] < today else ''}</td>"
        f"<td><a href='/return/{member_id}/{r['isbn']}'>Return</a></td></tr>"
        for r in borrowed
    )
    content = f"""
    <h2>👤 {m['name']} ({member_id})</h2>
    <h3>Currently Borrowed</h3>
    <table>
      <tr><th>Book</th><th>Due Date</th><th>Action</th></tr>
      {rows if rows else "<tr><td colspan='3' style='text-align:center'>No books currently borrowed</td></tr>"}
    </table>
    <br><a href="/members">← Back to Members</a>
    """
    return render_template_string(BASE, content=content)


@app.route("/add_member", methods=["POST"])
def add_member():
    mid = request.form["member_id"].strip()
    name = request.form["name"].strip()
    conn = get_db()
    existing = conn.execute("SELECT * FROM members WHERE member_id=?", (mid,)).fetchone()
    if existing:
        flash("❌ Member ID already exists")
    else:
        conn.execute("INSERT INTO members VALUES (?,?)", (mid, name))
        conn.commit()
        flash(f"✅ Member '{name}' added")
    conn.close()
    return redirect(url_for("members"))


@app.route("/borrow/<isbn>", methods=["GET", "POST"])
def borrow(isbn):
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE isbn=?", (isbn,)).fetchone()
    if not book:
        flash("❌ Book not found")
        conn.close()
        return redirect(url_for("index"))
    if request.method == "POST":
        mid = request.form["member_id"].strip()
        member = conn.execute("SELECT * FROM members WHERE member_id=?", (mid,)).fetchone()
        if not member:
            flash("❌ Member not found")
        elif book["available_copies"] <= 0:
            flash("❌ No copies available right now")
        else:
            due = (datetime.now() + timedelta(days=LOAN_DAYS)).strftime("%Y-%m-%d")
            conn.execute("INSERT INTO borrowed (member_id, isbn, due_date) VALUES (?,?,?)", (mid, isbn, due))
            conn.execute("UPDATE books SET available_copies=available_copies-1 WHERE isbn=?", (isbn,))
            conn.commit()
            flash(f"✅ '{book['title']}' borrowed by {member['name']}. Due: {due}")
        conn.close()
        return redirect(url_for("index"))
    conn.close()
    content = f"""
    <h2>📖 Borrow: {book['title']}</h2>
    <p>Author: {book['author']} &nbsp;|&nbsp; Available: {book['available_copies']}/{book['total_copies']}</p>
    <form method="post">
      Member ID: <input name="member_id" placeholder="e.g. M001" required><br>
      <button type="submit">Confirm Borrow</button>
    </form>
    <br><a href="/">← Back to Books</a>
    """
    return render_template_string(BASE, content=content)


@app.route("/return/<member_id>/<isbn>")
def return_book(member_id, isbn):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM borrowed WHERE member_id=? AND isbn=?", (member_id, isbn)
    ).fetchone()
    if row:
        conn.execute("DELETE FROM borrowed WHERE member_id=? AND isbn=?", (member_id, isbn))
        conn.execute("UPDATE books SET available_copies=available_copies+1 WHERE isbn=?", (isbn,))
        conn.commit()
        flash("✅ Book returned successfully!")
    else:
        flash("❌ No borrow record found")
    conn.close()
    return redirect(url_for("member_detail", member_id=member_id))


@app.route("/overdue")
def overdue():
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    rows_data = conn.execute("""
        SELECT m.name, m.member_id, b.title, br.due_date
        FROM borrowed br
        JOIN members m ON br.member_id = m.member_id
        JOIN books b ON br.isbn = b.isbn
        WHERE br.due_date < ?
        ORDER BY br.due_date
    """, (today,)).fetchall()
    conn.close()
    rows = "".join(
        f"<tr><td>{r['name']}</td><td>{r['title']}</td>"
        f"<td class='overdue'>{r['due_date']}</td></tr>"
        for r in rows_data
    )
    content = f"""
    <h2>⚠️ Overdue Books</h2>
    <div class="table-wrap">
    <table>
      <tr><th>Member</th><th>Book</th><th>Due Date</th></tr>
      {rows if rows else "<tr><td colspan='3' style='text-align:center'>✅ No overdue books!</td></tr>"}
    </table>
    </div>
    """
    return render_template_string(BASE, content=content)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)