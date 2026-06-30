"""
Library Management System
A simple console-based app to manage books, members, and borrowing.
Data is persisted to a local JSON file (library_data.json).
"""

import json
import os
from datetime import datetime, timedelta

DATA_FILE = "library_data.json"
LOAN_DAYS = 14


class Library:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.books = {}      # isbn -> book dict
        self.members = {}    # member_id -> member dict
        self.load()

    # ---------- Persistence ----------
    def load(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                data = json.load(f)
                self.books = data.get("books", {})
                self.members = data.get("members", {})

    def save(self):
        with open(self.data_file, "w") as f:
            json.dump({"books": self.books, "members": self.members}, f, indent=2)

    # ---------- Book management ----------
    def add_book(self, isbn, title, author, copies=1):
        if isbn in self.books:
            self.books[isbn]["total_copies"] += copies
            self.books[isbn]["available_copies"] += copies
        else:
            self.books[isbn] = {
                "title": title,
                "author": author,
                "total_copies": copies,
                "available_copies": copies,
            }
        self.save()
        print(f"Added: {title} ({copies} copies)")

    def remove_book(self, isbn):
        if isbn in self.books:
            del self.books[isbn]
            self.save()
            print("Book removed.")
        else:
            print("Book not found.")

    def search_books(self, keyword):
        keyword = keyword.lower()
        results = [
            (isbn, b) for isbn, b in self.books.items()
            if keyword in b["title"].lower() or keyword in b["author"].lower()
        ]
        return results

    # ---------- Member management ----------
    def add_member(self, member_id, name):
        if member_id in self.members:
            print("Member ID already exists.")
            return
        self.members[member_id] = {"name": name, "borrowed": {}}
        self.save()
        print(f"Member added: {name}")

    # ---------- Borrowing ----------
    def borrow_book(self, member_id, isbn):
        if member_id not in self.members:
            print("Member not found.")
            return
        if isbn not in self.books:
            print("Book not found.")
            return
        book = self.books[isbn]
        if book["available_copies"] <= 0:
            print("No copies available.")
            return
        due_date = (datetime.now() + timedelta(days=LOAN_DAYS)).strftime("%Y-%m-%d")
        self.members[member_id]["borrowed"][isbn] = due_date
        book["available_copies"] -= 1
        self.save()
        print(f"'{book['title']}' borrowed. Due: {due_date}")

    def return_book(self, member_id, isbn):
        if member_id not in self.members:
            print("Member not found.")
            return
        borrowed = self.members[member_id]["borrowed"]
        if isbn not in borrowed:
            print("This member hasn't borrowed that book.")
            return
        del borrowed[isbn]
        self.books[isbn]["available_copies"] += 1
        self.save()
        print("Book returned. Thank you!")

    def list_overdue(self):
        today = datetime.now().strftime("%Y-%m-%d")
        overdue = []
        for mid, m in self.members.items():
            for isbn, due in m["borrowed"].items():
                if due < today:
                    overdue.append((m["name"], self.books.get(isbn, {}).get("title", isbn), due))
        return overdue


def menu():
    lib = Library()
    actions = {
        "1": "Add book",
        "2": "Remove book",
        "3": "Search books",
        "4": "Add member",
        "5": "Borrow book",
        "6": "Return book",
        "7": "List overdue books",
        "8": "List all books",
        "0": "Exit",
    }

    while True:
        print("\n--- Library Menu ---")
        for k, v in actions.items():
            print(f"{k}. {v}")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            isbn = input("ISBN: ").strip()
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            copies = int(input("Copies: ") or 1)
            lib.add_book(isbn, title, author, copies)

        elif choice == "2":
            isbn = input("ISBN to remove: ").strip()
            lib.remove_book(isbn)

        elif choice == "3":
            keyword = input("Search keyword: ").strip()
            for isbn, b in lib.search_books(keyword):
                print(f"{isbn}: {b['title']} by {b['author']} ({b['available_copies']}/{b['total_copies']} available)")

        elif choice == "4":
            member_id = input("Member ID: ").strip()
            name = input("Name: ").strip()
            lib.add_member(member_id, name)

        elif choice == "5":
            member_id = input("Member ID: ").strip()
            isbn = input("ISBN: ").strip()
            lib.borrow_book(member_id, isbn)

        elif choice == "6":
            member_id = input("Member ID: ").strip()
            isbn = input("ISBN: ").strip()
            lib.return_book(member_id, isbn)

        elif choice == "7":
            overdue = lib.list_overdue()
            if not overdue:
                print("No overdue books.")
            for name, title, due in overdue:
                print(f"{name} - '{title}' was due {due}")

        elif choice == "8":
            for isbn, b in lib.books.items():
                print(f"{isbn}: {b['title']} by {b['author']} ({b['available_copies']}/{b['total_copies']} available)")

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    menu()