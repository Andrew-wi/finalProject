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


@app.route("/watch", methods=["GET", "POST"])
@login_required
def index():
    """shows the homepage, consisting of an invitation
    to a friend, and then the link you want to watch"""
    if request.method == "POST":
        if not request.form.get("email"):
            return apology("please enter your friend's email", 403)
        elif not request.form.get("link"):
            return apology("please enter a link", 403)

        # https://www.youtube.com/watch?v=SxAp27sFaIM
        oldLink = request.form.get("link")
        newLink = oldLink[:23] + "/embed/" + oldLink[32:]
        print(newLink)

        return render_template("watched.html", link=newLink)
    else:
        return render_template("watch.html")

# @app.route("/watch", methods=["GET", "POST"])
# @login_required
# def watch():



# @app.route("/history")
# @login_required
# def history():
#     """Show history of transactions"""



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # uses the old template from the finance pset
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
        return redirect("/watch")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


# @app.route("/friends", methods=["GET", "POST"])
# @login_required
# def friends():



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # requires that users input a username
        if not request.form.get("username"):
            return apology("must provide username", 400)
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password and confirmation", 400)
        elif not request.form.get("email"):
            return apology("must provide email", 403)

        # check database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # check if username taken
        if len(rows) > 0:
            return apology("username already taken", 400)

        # check if email is taken
        emailRows = db.execute("SELECT * FROM users WHERE email = :email",
                               email=request.form.get("email"))
        if len(emailRows) > 0:
            return apology("email already taken", 403)

        # check for filling out correct password/confirmation fields
        if not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must fill out password and confirmation fields", 403)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation must match", 400)

        # hashed_pass = generate_password_hash(request.form.get("confirmation"), method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (username, hash, email) VALUES (:username, :hashed_pass, :email)",
                   username=request.form.get("username"),
                   hashed_pass=generate_password_hash(request.form.get("confirmation"), method='pbkdf2:sha256', salt_length=8),
                   email=request.form.get("email"))
        return redirect("/")
    else:
        return render_template("register.html")


# @app.route("/sell", methods=["GET", "POST"])
# @login_required
# def sell():


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
