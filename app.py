"""
Library Management System - Web Version (Flask)
Run locally with: python app.py
Then visit http://127.0.0.1:5000
"""

import json
import os
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, redirect, url_for, flash

DATA_FILE = "library_data.json"
LOAN_DAYS = 14

app = Flask(__name__)
app.secret_key = "change-this-secret-key"


# ---------- Data layer ----------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"books": {}, "members": {}}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------- Templates (inline for simplicity) ----------
BASE = """
<!doctype html>
<html>
<head>
  <title>Library Management System</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 900px; margin: 30px auto; background: #f5f5f5; }
    nav a { margin-right: 15px; text-decoration: none; color: #2563eb; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; background: white; margin-top: 15px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background: #2563eb; color: white; }
    form { background: white; padding: 15px; border-radius: 8px; margin-top: 15px; }
    input, button { padding: 6px; margin: 4px 0; }
    button { background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; padding: 8px 14px; }
    .flash { background: #fef3c7; padding: 10px; border-radius: 6px; margin-top: 10px; }
  </style>
</head>
<body>
  <h1>📚 Library Management System</h1>
  <nav>
    <a href="/">Books</a>
    <a href="/members">Members</a>
    <a href="/overdue">Overdue</a>
  </nav>
  {% with messages = get_flashed_messages() %}
    {% if messages %}{% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}{% endif %}
  {% endwith %}
  {{ content|safe }}
</body>
</html>
"""


# ---------- Routes ----------
@app.route("/")
def index():
    data = load_data()
    rows = "".join(
        f"<tr><td>{isbn}</td><td>{b['title']}</td><td>{b['author']}</td>"
        f"<td>{b['available_copies']}/{b['total_copies']}</td>"
        f"<td><a href='/borrow/{isbn}'>Borrow</a> | <a href='/delete/{isbn}'>Delete</a></td></tr>"
        for isbn, b in data["books"].items()
    )
    content = f"""
    <h2>Books</h2>
    <table><tr><th>ISBN</th><th>Title</th><th>Author</th><th>Available</th><th>Actions</th></tr>{rows}</table>
    <form method="post" action="/add">
      <h3>Add a Book</h3>
      ISBN: <input name="isbn" required><br>
      Title: <input name="title" required><br>
      Author: <input name="author" required><br>
      Copies: <input name="copies" type="number" value="1" min="1"><br>
      <button type="submit">Add Book</button>
    </form>
    """
    return render_template_string(BASE, content=content)


@app.route("/add", methods=["POST"])
def add_book():
    data = load_data()
    isbn = request.form["isbn"].strip()
    title = request.form["title"].strip()
    author = request.form["author"].strip()
    copies = int(request.form.get("copies", 1))

    if isbn in data["books"]:
        data["books"][isbn]["total_copies"] += copies
        data["books"][isbn]["available_copies"] += copies
    else:
        data["books"][isbn] = {
            "title": title, "author": author,
            "total_copies": copies, "available_copies": copies,
        }
    save_data(data)
    flash(f"Added '{title}'")
    return redirect(url_for("index"))


@app.route("/delete/<isbn>")
def delete_book(isbn):
    data = load_data()
    if isbn in data["books"]:
        del data["books"][isbn]
        save_data(data)
        flash("Book deleted")
    return redirect(url_for("index"))


@app.route("/members")
def members():
    data = load_data()
    rows = "".join(
        f"<tr><td>{mid}</td><td>{m['name']}</td><td>{len(m['borrowed'])}</td></tr>"
        for mid, m in data["members"].items()
    )
    content = f"""
    <h2>Members</h2>
    <table><tr><th>ID</th><th>Name</th><th>Books Borrowed</th></tr>{rows}</table>
    <form method="post" action="/add_member">
      <h3>Add a Member</h3>
      Member ID: <input name="member_id" required><br>
      Name: <input name="name" required><br>
      <button type="submit">Add Member</button>
    </form>
    """
    return render_template_string(BASE, content=content)


@app.route("/add_member", methods=["POST"])
def add_member():
    data = load_data()
    mid = request.form["member_id"].strip()
    name = request.form["name"].strip()
    if mid in data["members"]:
        flash("Member ID already exists")
    else:
        data["members"][mid] = {"name": name, "borrowed": {}}
        save_data(data)
        flash(f"Member '{name}' added")
    return redirect(url_for("members"))


@app.route("/borrow/<isbn>", methods=["GET", "POST"])
def borrow(isbn):
    data = load_data()
    if request.method == "POST":
        mid = request.form["member_id"].strip()
        if mid not in data["members"]:
            flash("Member not found")
        elif data["books"][isbn]["available_copies"] <= 0:
            flash("No copies available")
        else:
            due = (datetime.now() + timedelta(days=LOAN_DAYS)).strftime("%Y-%m-%d")
            data["members"][mid]["borrowed"][isbn] = due
            data["books"][isbn]["available_copies"] -= 1
            save_data(data)
            flash(f"Borrowed. Due {due}")
        return redirect(url_for("index"))

    book = data["books"].get(isbn)
    content = f"""
    <h2>Borrow: {book['title']}</h2>
    <form method="post">
      Member ID: <input name="member_id" required><br>
      <button type="submit">Confirm Borrow</button>
    </form>
    """
    return render_template_string(BASE, content=content)


@app.route("/overdue")
def overdue():
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = ""
    for mid, m in data["members"].items():
        for isbn, due in m["borrowed"].items():
            if due < today:
                title = data["books"].get(isbn, {}).get("title", isbn)
                rows += f"<tr><td>{m['name']}</td><td>{title}</td><td>{due}</td></tr>"
    content = f"""
    <h2>Overdue Books</h2>
    <table><tr><th>Member</th><th>Book</th><th>Due Date</th></tr>{rows}</table>
    """
    return render_template_string(BASE, content=content)


if __name__ == "__main__":
    app.run(debug=True)