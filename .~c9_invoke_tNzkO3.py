from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # returns list of rows joined at userid (list of dictionaries)
    stock_list = db.execute("SELECT sales.user_id, sales.stock_name, sales.quantity FROM sales INNER JOIN users ON sales.user_id = users.id WHERE id = :user_id",
                            user_id=session["user_id"])
    # gets cash from session's userid
    cash = db.execute("SELECT cash FROM users WHERE id = :user_id",
                      user_id=session["user_id"])[0]["cash"]
    total = 0
    # loop through stocks in the joint list, looks up the price,
    # multiplies by stock number, adds to total
    for stock in stock_list:
        total += stock["quantity"] * lookup(stock["stock_name"])["price"]
    return render_template("index.html",
                           stock_list=stock_list,
                           lookup=lookup,
                           usd=usd,
                           cash=cash,
                           total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # checking for entry of fields symbol and shares
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("must provide stock symbol and number of shares", 403)

        try:
            int(float(request.form.get("shares")))
        except:
            return apology("number of shares must be a positive integer value", 400)
        # testing for x.0*y format and negatives
        # inspired by stackoverflow
        if int(float(request.form.get("shares"))) != float(request.form.get("shares")) or request.form.get("shares").startswith('-'):
            return apology("number of shares must be a positive integer value", 400)
        share_numbers = int(float(request.form.get("shares")))

        if not lookup(request.form.get("symbol")):
            return apology("stock symbol not found", 400)

        stock_price = lookup(request.form.get("symbol").strip())["price"]
        user_info = db.execute("SELECT cash FROM users WHERE id = :session",
                               session=session["user_id"])
        # some math about total share price
        total_shares_cost = stock_price * share_numbers
        # getting user cash and checking if enough
        user_cash = user_info[0]["cash"]
        if user_cash - total_shares_cost < 0:
            return apology("not enough cash", 403)
        user_shares = db.execute("SELECT * FROM sales WHERE user_id = :user_id AND stock_name = :stock_name",
                                 user_id=session["user_id"],
                                 stock_name=request.form.get("symbol").upper().strip())
        # checking if the stock exists and inserting if it doesnt,
        # updating if it does
        if len(user_shares) == 0:
            db.execute("INSERT INTO sales VALUES (:user_id, :stock_name, :quantity)",
                       user_id=session["user_id"],
                       stock_name=request.form.get("symbol").strip().upper(),
                       quantity=share_numbers)
            db.execute("UPDATE users SET cash = cash - :cash WHERE id = :user_id",
                       cash=total_shares_cost,
                       user_id=session["user_id"])
            db.execute("INSERT INTO history (symbol, shares, price, transacted) VALUES (:symbol, :shares, :price, :transacted)",
                       symbol=request.form.get("symbol").strip().upper(),
                       shares=share_numbers,
                       price=stock_price,
                       transacted=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else:
            db.execute("UPDATE sales SET quantity = quantity + :quantity WHERE user_id = :user_id AND stock_name = :stock_name",
                       quantity=share_numbers,
                       user_id=session["user_id"],
                       stock_name=request.form.get("symbol").strip().upper())
            db.execute("UPDATE users SET cash = :cash WHERE id = :user_id",
                       cash=user_cash,
                       user_id=session["user_id"])
            db.execute("INSERT INTO history (symbol, shares, price, transacted) VALUES (:symbol, :shares, :price, :transacted)",
                       symbol=request.form.get("symbol").strip().upper(),
                       shares=share_numbers,
                       price=stock_price,
                       transacted=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # just rendering the same template with an additional
        # to show that the purchase was made
        return render_template("bought.html")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    total_history = db.execute("SELECT * FROM history")
    return render_template("history.html",
                           history=total_history,
                           usd=usd)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # checking if the post request is valid
        if not request.form.get("symbol"):
            return apology("must provide stock name", 400)
        # look up the value of the stock
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("stock query not found", 400)
        # returning the values of the dictionary lookup returned
        return render_template("quoted.html",
                               symbol=stock["symbol"],
                               name=stock["name"],
                               price=usd(stock["price"]))
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # requires that users input a username
        if not request.form.get("username"):
            return apology("must provide username", 400)
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password and confirmation", 400)
        # check database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        # check if username taken
        if len(rows) > 0:
            return apology("username already taken", 400)
        # check for filling out correct password/confirmation fields
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must fill out password and confirmation fields", 403)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation must match", 400)
        # hashed_pass = generate_password_hash(request.form.get("confirmation"), method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashed_pass)",
                   username=request.form.get("username"),
                   hashed_pass=generate_password_hash(request.form.get("confirmation"), method='pbkdf2:sha256', salt_length=8))
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # fill out the fields
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("must fill out stock symbol and number of shares fields", 403)
        # testing for - or x.y decimal format (not equal to x.0 format)
        if int(float(request.form.get("shares"))) != float(request.form.get("shares")) or request.form.get("shares").startswith('-'):
            return apology("number of shares must be a positive integer value", 400)
        share_numbers = int(float(request.form.get("shares")))
        # check if the user has the shares at all
        user_shares = db.execute("SELECT * FROM sales WHERE user_id = :user_id AND stock_name = :stock_name",
                                 user_id=session["user_id"],
                                 stock_name=request.form.get("symbol").upper())
        if len(user_shares) == 0:
            return apology("shares not found", 404)
        final_shares = user_shares[0]["quantity"] - share_numbers
        stock_price = lookup(request.form.get("symbol"))["price"]
        new_cash = stock_price * share_numbers
        if final_shares < 0:
            return apology("not enough shares to sell", 403)
        db.execute("UPDATE sales SET quantity = :final_shares WHERE user_id = :user_id AND stock_name = :stock_name",
                   final_shares=final_shares,
                   user_id=session["user_id"],
                   stock_name=request.form.get("symbol").upper())
        db.execute("UPDATE users SET cash = cash + :cash WHERE id = :user_id",
                   user_id=session["user_id"],
                   cash=new_cash)
        db.execute("INSERT INTO history (symbol, shares, price, transacted) VALUES (:symbol, :shares, :price, :transacted)",
                   symbol=request.form.get("symbol").upper(),
                   shares=share_numbers,
                   price=stock_price,
                   transacted=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return render_template("sold.html")
    return render_template("sell.html")


@app.route('/addValue', methods=['GET', 'POST'])
@login_required
def addValue():
    '''Adds value to their account'''
    if request.method == "POST":
        if not request.form.get("cash"):
            return apology("must fill out value to add field", 403)
        if int(request.form.get("cash")) < 0:
            return apology("cash must be positive integer value", 400)
        db.execute("UPDATE users SET cash = cash + :cash WHERE id = :user_id",
                   cash=int(request.form.get("cash")),
                   user_id=session["user_id"])
        return render_template("addedValue.html")
    return render_template("addValue.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
