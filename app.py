import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TAX_RATE = 0.05  # 5% GST

MENU = {
    "Starters": [
        {"id": "s1", "name": "Paneer Tikka", "price": 220, "icon": "🧀", "desc": "Char-grilled cottage cheese with spices"},
        {"id": "s2", "name": "Veg Spring Rolls", "price": 160, "icon": "🥟", "desc": "Crispy rolls with a sweet chilli dip"},
        {"id": "s3", "name": "Chicken 65", "price": 260, "icon": "🍗", "desc": "Spicy South Indian fried chicken"},
    ],
    "Main Course": [
        {"id": "m1", "name": "Butter Chicken", "price": 340, "icon": "🍛", "desc": "Creamy tomato gravy, tender chicken"},
        {"id": "m2", "name": "Paneer Butter Masala", "price": 300, "icon": "🍲", "desc": "Rich, mildly sweet paneer curry"},
        {"id": "m3", "name": "Veg Biryani", "price": 250, "icon": "🍚", "desc": "Fragrant basmati with garden vegetables"},
        {"id": "m4", "name": "Garlic Naan", "price": 60, "icon": "🫓", "desc": "Tandoor-baked, brushed with garlic butter"},
    ],
    "Desserts": [
        {"id": "d1", "name": "Gulab Jamun", "price": 90, "icon": "🍮", "desc": "Warm milk dumplings in rose syrup"},
        {"id": "d2", "name": "Chocolate Brownie", "price": 140, "icon": "🍫", "desc": "Fudgy brownie with ice cream"},
    ],
    "Drinks": [
        {"id": "k1", "name": "Mango Lassi", "price": 110, "icon": "🥭", "desc": "Thick, chilled yoghurt and mango"},
        {"id": "k2", "name": "Masala Chai", "price": 50, "icon": "☕", "desc": "Ginger and cardamom milk tea"},
        {"id": "k3", "name": "Fresh Lime Soda", "price": 80, "icon": "🍋", "desc": "Sweet, salted or mixed"},
    ],
}
ITEMS = {i["id"]: i for group in MENU.values() for i in group}


def save(name, record):
    """Append a record to data/<name>.json."""
    path = DATA_DIR / f"{name}.json"
    rows = json.loads(path.read_text()) if path.exists() else []
    rows.append(record)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))


def error(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


@app.route("/")
def index():
    return render_template("index.html", menu=MENU, today=date.today().isoformat())


@app.post("/api/order")
def order():
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "")).strip()
    phone = str(d.get("phone", "")).strip()
    if not name:
        return error("Please enter your name.")
    if not re.fullmatch(r"[0-9+\-\s]{7,15}", phone):
        return error("Please enter a valid phone number.")

    lines, subtotal = [], 0
    for item_id, qty in (d.get("items") or {}).items():
        try:
            qty = int(qty)
        except (TypeError, ValueError):
            continue
        if item_id in ITEMS and 0 < qty <= 50:
            item = ITEMS[item_id]
            amount = item["price"] * qty
            subtotal += amount
            lines.append({"name": item["name"], "price": item["price"], "qty": qty, "amount": amount})
    if not lines:
        return error("Your order is empty. Add at least one item.")

    tax = round(subtotal * TAX_RATE, 2)
    bill = {
        "order_id": uuid.uuid4().hex[:8].upper(),
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "name": name, "phone": phone, "lines": lines,
        "subtotal": subtotal, "tax_rate": int(TAX_RATE * 100),
        "tax": tax, "total": round(subtotal + tax, 2),
    }
    save("orders", bill)
    return jsonify({"ok": True, "bill": bill})


@app.post("/api/book")
def book():
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "")).strip()
    time = str(d.get("time", "")).strip()
    try:
        when = date.fromisoformat(str(d.get("date", "")))
        guests = int(d.get("guests", 0))
    except ValueError:
        return error("Please choose a valid date and number of guests.")
    if not name:
        return error("Please enter your name.")
    if when < date.today():
        return error("Please pick today or a future date.")
    if not re.fullmatch(r"\d{2}:\d{2}", time):
        return error("Please select a time.")
    if not 1 <= guests <= 20:
        return error("We can seat 1 to 20 guests per booking.")

    booking = {"booking_id": "TB" + uuid.uuid4().hex[:5].upper(), "name": name,
               "date": when.isoformat(), "time": time, "guests": guests}
    save("bookings", booking)
    return jsonify({"ok": True, "booking": booking})


@app.post("/api/feedback")
def feedback():
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "")).strip() or "Anonymous"
    message = str(d.get("message", "")).strip()
    try:
        rating = int(d.get("rating", 0))
    except ValueError:
        rating = 0
    if not 1 <= rating <= 5:
        return error("Please select a star rating.")
    if not message:
        return error("Please write a short review.")
    save("feedback", {"name": name, "rating": rating, "message": message[:1000],
                      "time": datetime.now().isoformat(timespec="seconds")})
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
