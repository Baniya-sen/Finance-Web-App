from flask import Flask, render_template, redirect, g, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

# Functions in helpers.py
from helpers import get_db, login_required, apology, rupees, lookup, buy_datapoint, sell_datapoint

# App configurations
app = Flask(__name__)
app.config['DATABASE'] = 'finance.db'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Custom filter for Rupees format
app.template_filter("INR")(rupees)


# Closing db connection after each request
@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Cache system must be re-validated and to not store
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Homepage
@app.route("/")
@login_required
def index():
    # Database instance
    cursor = get_db().cursor()

    # Get username and account balance info from database in dict format
    cursor.execute(
        "SELECT username, cash FROM users WHERE id = ?",
        (session["user_id"],)
    )
    info_column = [heading[0] for heading in cursor.description]
    info_rows = cursor.fetchall()
    user_info_dict = [dict(zip(info_column, row)) for row in info_rows]

    # Get user's stock holdings info from database in dict format
    user_stocks_info = cursor.execute(
        "SELECT * FROM stocks_holdings WHERE user_id = ?",
        (session["user_id"],)
    )
    stock_column = [heading[0] for heading in cursor.description]
    stock_rows = cursor.fetchall()
    stock_info_dict = [dict(zip(stock_column, row)) for row in stock_rows]

    # Current price of all users stocks
    price_list = [lookup(symbol["stock_symbol"])["price"] for symbol in stock_info_dict]

    return render_template(
        "index.html",
        user_info=user_info_dict,
        stock_info=stock_info_dict,
        stocks_current_price=price_list)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Clear all session data to login fresh
    session.clear()

    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":

        # Check if username and password not empty
        if not request.form.get("username") or not request.form.get("password"):
            return apology("Atleast provide a username/password!")

        db = get_db()
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Check if username exists
        try:
            existing_username = dict(cursor.execute(
                "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchone())
        except TypeError:
            return apology(f"Username '{request.form.get('username')}' does not exists!")

        # Check if password matches with the hash
        if not check_password_hash(existing_username["hash"], request.form.get("password")):
            return apology("Incorrect password!")

        # Set user_id as current session_id
        session["user_id"] = existing_username["id"]

        # Redirect to homepage
        return redirect("/")


@app.route("/logout")
@login_required
def logout():
    # Clear session id and return to login
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":

        # Check if username password field not mpty, and passwords matchtes
        if not request.form.get("username") or not request.form.get("password"):
            return apology("Atleat enter user/password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords mismatch!")

        db = get_db()
        cursor = db.cursor()

        # Check if username already exists
        existing_username = cursor.execute(
            "SELECT username FROM users WHERE username = ?",
            (request.form.get("username"),)
        ).fetchone()
        if existing_username is not None:
            return apology("Username already taken!")

        # If verifications passes, update database
        cursor.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (request.form.get("username"), generate_password_hash(request.form.get("password")))
        )
        db.commit()

        return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
        return render_template("quote.html")
    elif request.method == "POST":
        # Get symbol from user input
        if not request.form.get("symbol"):
            return apology("Atleast Provide a symbol!")
        elif lookup(request.form.get("symbol")) is None:
            return apology(f"There is no symbol '{request.form.get("symbol")}'")

        # Render page with stocks info
        return render_template("quoted.html", stock=lookup(request.form.get("symbol")))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")

    elif request.method == "POST":

        # Check if symbol and shares field not empty
        if not request.form.get("symbol"):
            return apology("Atleast provide a symbol!")
        elif lookup(request.form.get("symbol")) is None:
            return apology(f"There is no symbol '{request.form.get('symbol')}")

        # Checks if shares is a number
        try:
            if int(request.form.get("shares")) < 1:
                return apology("Buy atleast 1 share!!")
        except ValueError:
            return apology("Invalid shares!")

        # Check if user has enough balance for purchase
        stock = lookup(request.form.get("symbol"))
        user_balance = get_db().cursor().execute(
            "SELECT cash FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()[0]
        if int(request.form.get("shares")) * stock["price"] > user_balance:
            return apology("You dont have enough balance!")

        # Add stock transaction to user's stocks database
        buy_datapoint(
            stock["symbol"],
            float(request.form.get("shares")),
            stock["price"],
            transaction_type="bought"
        )

        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    # Get all user's stocks
    cursor = get_db().cursor()
    user_stocks = cursor.execute(
        "SELECT stock_symbol FROM stocks_holdings WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    stocks_set = sorted({item[0] for item in user_stocks})

    # Render page with stocks info
    if request.method == "GET":
        return render_template("sell.html", stocks=stocks_set)

    # If user sells stocks
    elif request.method == "POST":
        if not request.form.get("symbol") in stocks_set:
            return apology(f'You dont have any stock named "{request.form.get("symbol")}"!')
        try:
            shares = int(request.form.get("shares"))
            if shares < 1:
                return apology("Atleast sell 1 share!")
        except TypeError:
            return apology("Invalid shares!")

        # Check stock quantity user have
        stock_quantity = cursor.execute(
            "SELECT quantity FROM stocks_holdings WHERE user_id = ? And stock_symbol = ?",
            (session["user_id"], request.form.get("symbol").upper(),)
        ).fetchone()
        print(stock_quantity)
        if int(request.form.get("shares")) > stock_quantity[0]:
            return apology(f"You don't have that much stocks in '{request.form.get("symbol")}'")

        # Add stock transaction to database
        sell_datapoint(
            request.form.get("symbol").upper(),
            int(request.form.get("shares")),
            lookup(request.form.get("symbol"))["price"],
            transaction_type="sold"
        )

        return redirect("/")


@app.route("/history")
@login_required
def history():
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Get users all transaction
    cursor.execute(
        "SELECT * FROM all_transactions WHERE user_id = ? ORDER BY transaction_date DESC",
        (session["user_id"],)
    )
    # Get column names
    columns = [column[0] for column in cursor.description]
    # Fetch all rows
    rows = cursor.fetchall()
    # Convert rows to a list of dictionaries
    user_transactions = [dict(zip(columns, row)) for row in rows]

    return render_template("history.html", transactions=user_transactions)


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    # Get users account balance
    db = get_db()
    cursor = db.cursor()
    user_balance = cursor.execute(
        "SELECT cash FROM users WHERE id = ?", (session["user_id"],)).fetchone()[0]

    if request.method == "GET":
        return render_template("cash.html", balance=user_balance)

    elif request.method == "POST":

        # Check if input is a float number
        try:
            if float(request.form.get("cash")) < 100:
                return apology("Minimum deposit >= ₹100")
            elif float(request.form.get("cash")) > 1000000:
                return apology("Bro Ambaani! Huge money deposit! ED coming...")
        except TypeError:
            return apology("Invalid Input Bro!")

        # Add balance to user account
        cursor.execute(
            """UPDATE users SET cash = cash + ? WHERE id = ?""",
            (float(request.form.get("cash")), session["user_id"],)
        )
        db.commit()
        return redirect("/")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    db = get_db()
    cursor = db.cursor()
    user_info = cursor.execute(
        "SELECT username, cash FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    # Render user info
    if request.method == "GET":
        return render_template("account.html", userinfo=user_info)

    # If user decided to change password
    elif request.method == "POST":

        # Get get current password
        current_hash = cursor.execute(
            "SELECT hash FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        # Verifications
        if not request.form.get("newPassword") or not request.form.get("confirmPassword"):
            return apology("Enter password/confirm pasword!")
        elif request.form.get("newPassword") != request.form.get("confirmPassword"):
            return apology("Password mismatch!")
        elif check_password_hash(current_hash[0], request.form.get("newPassword")):
            return apology("New password can't be same as old password!")

        # If verify, save new password
        cursor.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            (generate_password_hash(request.form.get("newPassword")), session["user_id"],)
        )
        db.commit()

        return redirect("/")


if __name__ == "__main__":
    app.run()
