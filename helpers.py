import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid
import re
import sqlite3

from flask import redirect, render_template, session, g, current_app
from functools import wraps


def get_db():
    """Opens database connection if does'nt exists"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config['DATABASE'])
        cursor = db.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        create_tables(cursor)
        cursor.execute("COMMIT;")
        db.commit()
    return db


def login_required(f):
    """Checks if a user is currently logged in or not"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, code=400):
    """Render message as an apology to user"""
    def string_handle(s):
        """Filters invalid symbols from message"""
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                        ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=string_handle(message)), code


def lookup(symbol):
    """Lookup stocks-price from yahoo.com database using API"""
    symbol = symbol.upper()

    # Get last 7 days stock prices from Yahoo.com
    end = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    start = end - datetime.timedelta(days=7)

    # API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Request to Yahoo.com for stock info
    try:
        response = requests.get(
            url, cookies={"session": str(uuid.uuid4())}, headers={"User-Agent": "python-request", "Accept": "*/*"}
        )
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        quotes.reverse()
        price = round(float(quotes[0]["Adj Close"]), 2)
        return {
            "name": symbol,
            "price": price,
            "symbol": symbol
        }
    except (requests.RequestException, KeyError, ValueError, IndexError):
        return None


def rupees(value):
    """Format value as Indian Rupees $."""
    return f"₹{value:,.2f}"


def create_tables(database_cursor):
    """Creates tables to store data in finance.db if doesnt exists"""
    # Table to store users info
    database_cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            username TEXT NOT NULL,
                            hash TEXT NOT NULL,
                            cash NUMERIC NOT NULL DEFAULT 10000.00)""")

    # Unique index for username in users table
    database_cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_username ON users (username);")

    # Table to store all transactions
    database_cursor.execute("""CREATE TABLE IF NOT EXISTS all_transactions (
                            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            transaction_type TEXT NOT NULL,
                            user_id INTEGER NOT NULL,
                            stock_name TEXT NOT NULL,
                            stock_symbol TEXT NOT NULL,
                            stock_price FLOAT NOT NULL,
                            quantity INTEGER NOT NULL,
                            amount NUMERIC NOT NULL,
                            transaction_date TIME NOT NULL,
                            UNIQUE(transaction_id),
                            FOREIGN KEY(user_id) REFERENCES users(id)
                            )""")

    # Table to store stocks holdings
    database_cursor.execute("""CREATE TABLE IF NOT EXISTS stocks_holdings (
                            user_id INTEGER NOT NULL,
                            stock_symbol TEXT NOT NULL,
                            quantity INTEGER NOT NULL,
                            amount NUMERIC NOT NULL,
                            PRIMARY KEY (user_id, stock_symbol)
                            )""")


def buy_datapoint(symbol, shares, price, transaction_type):
    """Stores user purchase transaction into database"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("BEGIN TRANSACTION;")

        # Deduct cash from user for shares values
        cursor.execute("UPDATE users SET cash = cash - ?", (shares * price,))

        # Add shares to user's stocks holdings
        cursor.execute(
            """INSERT OR REPLACE INTO stocks_holdings (user_id, stock_symbol, quantity, amount)
            VALUES
            (?, ?, COALESCE((SELECT quantity FROM stocks_holdings WHERE user_id = ? AND stock_symbol = ?), 0) + ?,
            COALESCE((SELECT amount FROM stocks_holdings WHERE user_id = ? AND stock_symbol = ?), 0) + ?)""",
            (session["user_id"], symbol, session["user_id"], symbol, shares, session["user_id"], symbol, price * shares)
        )

        # Add transaction to all transactions table
        cursor.execute(
            """INSERT INTO all_transactions VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (transaction_type.upper(), session["user_id"],
            symbol, symbol, price, shares, price * shares,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        cursor.execute("COMMIT;")
        
    except sqlite3.OperationalError:
        db.rollback()
        print("SOMETHING WENT WRONG")


def sell_datapoint(symbol, shares, price, transaction_type):
    """Stores user sell transaction into database"""
    try:
        db = get_db()
        cursor = db.cursor()

        # Get user's shares
        quantity = cursor.execute(
            "SELECT quantity FROM stocks_holdings WHERE user_id = ? AND stock_symbol = ?",
            (session["user_id"], symbol,)
            ).fetchone()

        # If user selling all shares of stock, delete row
        cursor.execute("BEGIN TRANSACTION;")
        if shares == quantity[0]:
            cursor.execute(
                """DELETE FROM stocks_holdings WHERE user_id = ? AND stock_symbol = ?""",
                (session["user_id"], symbol,)
            )

        # Else, deduct shares from user's stocks holdings
        else:
            cursor.execute(
                """UPDATE stocks_holdings
                SET quantity = quantity - ?, amount = ?
                WHERE user_id = ? AND stock_symbol = ?""",
                (shares, price * shares, session["user_id"], symbol)
            )

        # Add cash to user's account
        cursor.execute("UPDATE users SET cash = cash + ?", (shares * price,))

        # Add transaction to all transaction table
        cursor.execute(
            """INSERT INTO all_transactions VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (transaction_type.upper(), session["user_id"],
            symbol, symbol, price, shares, price * shares,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        cursor.execute("COMMIT;")

    except sqlite3.OperationalError:
        db.rollback()
        print("SOMETHING WENT WRONG")
