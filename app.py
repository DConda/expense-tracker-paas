import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL", "sqlite:///local_expenses.db")

# Railway/Postgres compatibility fix for older URL format
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "item": self.item,
            "category": self.category,
            "amount": self.amount,
            "note": self.note,
            "created_at": self.created_at.isoformat()
        }


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Daily Expense Tracker</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                background-color: #f4f6f8;
            }
            .box {
                background: white;
                padding: 24px;
                border-radius: 10px;
                max-width: 760px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            input, button {
                padding: 10px;
                margin: 6px 0;
                width: 100%;
                box-sizing: border-box;
            }
            button {
                cursor: pointer;
            }
            code {
                background: #eee;
                padding: 2px 5px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>Daily Expense Tracker API</h1>
            <p>This application is deployed using Flask and a PaaS platform.</p>

            <h2>Add Expense</h2>
            <form action="/expenses" method="post">
                <input name="item" placeholder="Item name, example: Lunch" required>
                <input name="category" placeholder="Category, example: Food" required>
                <input name="amount" type="number" step="0.01" placeholder="Amount, example: 25000" required>
                <input name="note" placeholder="Optional note">
                <button type="submit">Add Expense</button>
            </form>

            <h2>Available Endpoints</h2>
            <ul>
                <li><code>GET /</code> - Homepage</li>
                <li><code>GET /health</code> - Health check</li>
                <li><code>GET /expenses</code> - View all expenses</li>
                <li><code>POST /expenses</code> - Add expense</li>
                <li><code>GET /expenses/&lt;id&gt;</code> - View one expense</li>
                <li><code>DELETE /expenses/&lt;id&gt;</code> - Delete expense</li>
                <li><code>GET /summary</code> - Expense summary</li>
            </ul>

            <p><a href="/expenses">View expenses</a></p>
            <p><a href="/health">Health check</a></p>
            <p><a href="/summary">Summary</a></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "database_configured": bool(os.environ.get("DATABASE_URL")),
        "app_name": os.environ.get("APP_NAME", "Expense Tracker PaaS")
    })


@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if request.method == "POST":
        data = request.get_json(silent=True)

        if data:
            item = data.get("item")
            category = data.get("category")
            amount = data.get("amount")
            note = data.get("note")
        else:
            item = request.form.get("item")
            category = request.form.get("category")
            amount = request.form.get("amount")
            note = request.form.get("note")

        if not item or not category or amount is None:
            return jsonify({
                "error": "item, category, and amount are required"
            }), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({
                "error": "amount must be a number"
            }), 400

        expense = Expense(
            item=item,
            category=category,
            amount=amount,
            note=note
        )

        db.session.add(expense)
        db.session.commit()

        if request.form:
            return """
            <p>Expense added successfully.</p>
            <p><a href="/">Back to homepage</a></p>
            <p><a href="/expenses">View expenses</a></p>
            """

        return jsonify({
            "message": "Expense added successfully",
            "data": expense.to_dict()
        }), 201

    all_expenses = Expense.query.order_by(Expense.created_at.desc()).all()

    return jsonify({
        "count": len(all_expenses),
        "data": [expense.to_dict() for expense in all_expenses]
    })


@app.route("/expenses/<int:expense_id>")
def get_expense(expense_id):
    expense = Expense.query.get(expense_id)

    if not expense:
        return jsonify({
            "error": "Expense not found"
        }), 404

    return jsonify(expense.to_dict())


@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)

    if not expense:
        return jsonify({
            "error": "Expense not found"
        }), 404

    db.session.delete(expense)
    db.session.commit()

    return jsonify({
        "message": "Expense deleted successfully",
        "deleted_id": expense_id
    })


@app.route("/summary")
def summary():
    expenses = Expense.query.all()
    total = sum(expense.amount for expense in expenses)

    categories = {}
    for expense in expenses:
        categories[expense.category] = categories.get(expense.category, 0) + expense.amount

    return jsonify({
        "total_expenses": len(expenses),
        "total_amount": total,
        "by_category": categories
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)