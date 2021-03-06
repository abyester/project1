import os
import requests

from functools import wraps
from flask import Flask, flash, jsonify, session, render_template, request, redirect, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = 'devkey'

# Check for environment variables - first database url then goodreads key
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
if not os.getenv("GOODREADS_KEY"):
    raise RuntimeError("GOODREADS_KEY is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
#Set key
key=os.getenv("GOODREADS_KEY")

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'userid' not in session:
            flash('Please login or register to continue')
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    #redirect to login if a userid hasn't yet been set (and stored in the session dictionary)
    error = None

    if request.method == 'POST':
        searchtext = request.form.get('searchtext')
        searchby = request.form.get('searchby')

        if searchtext is "":
            error = 'No search term entered'
            results = None
            return render_template('index.html', error=error)

        if searchby == "ISBN":
            results = db.execute("SELECT * FROM books WHERE isbn LIKE :searchtext LIMIT 20", {"searchtext": '%'+searchtext+'%'}).fetchall()
        elif searchby == "Title":
            results = db.execute("SELECT * FROM books WHERE title LIKE :searchtext LIMIT 20", {"searchtext": '%'+searchtext+'%'}).fetchall()
        elif searchby == "Author":
            results = db.execute("SELECT * FROM books WHERE author LIKE :searchtext LIMIT 20", {"searchtext": '%'+searchtext+'%'}).fetchall()

        if len(results) == 0:
            flash('No results. Search terms are case sensitive')
        return render_template('index.html', error=error, results=results, userid=session['userid'])

    return render_template('index.html', error=error, userid=session['userid'])

@app.route("/login", methods=['GET', 'POST'])
def login():

    # get username and password from form
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        if error is None:
            session.clear()
            session['userid'] = user['userid']
            flash('You successfully logged in')
            return redirect(url_for('index'))

    return render_template('login.html', error=error)

@app.route("/register", methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            "SELECT userid FROM users WHERE username = :username", {"username": username}
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            db.execute(
                "INSERT INTO users (username, password) VALUES (:username, :password)",
                        {"username": username, "password": generate_password_hash(password)}
            )
            db.commit()
            flash('You successfully registered')
            return redirect(url_for('login'))

    return render_template('register.html', error=error)

@app.route("/book/<isbn>", methods=['GET', 'POST'])
@login_required
def book(isbn):

    error = None
    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return render_template("index.html", error="No such book.  Search again")

    # Get all reviews.  NB need to join users and reviews table to be able to get the reviews with username
    # todo = omit my review from this list
    reviews = db.execute("SELECT username, review, rating, reviews.userid FROM reviews JOIN users ON users.userid = reviews.userid WHERE isbn = :isbn",
                            {"isbn": isbn}).fetchall()

    # Get my review (if it exists)
    myreview = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND userid = :userid",
                            {"isbn": isbn, "userid": session['userid']}).fetchone()

    #check if user has submitted review
    if request.method == 'POST':
        review = request.form.get('review')
        rating = int(request.form.get('rating'))

        if not review:
            error = 'No review text entered.'
        elif not rating or rating < 1 or rating  >5:
            error = 'Rating between 1 and 5 required.'
        elif myreview:
            error =' User review already entered.'

        if error is None:
            db.execute(
            "INSERT INTO reviews (review, rating, isbn, userid) VALUES (:review, :rating, :isbn, :userid)",
                    {"review": review, "rating": rating, "isbn": isbn, "userid": session['userid']}
                    )
            db.commit()
            flash('You successfully entered a review')
            myreview = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND userid = :userid",
                                    {"isbn": isbn, "userid": session['userid']}).fetchone()

    #Get goodreads reviews - note that the average_rating and ratings_count are both found in the first entry of the list of books
    #which explains the slightly complex terminology used
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    if res.status_code != 200:
        goodrating = None
        goodcount = None
    else:
        goodreads = res.json()
        goodrating = goodreads["books"][0]["average_rating"]
        goodcount = goodreads["books"][0]["ratings_count"]

    return render_template("book.html", book=book, myreview=myreview, reviews=reviews, userid=session['userid'], goodrating = goodrating, goodcount = goodcount, error=error)

@app.route("/api/<isbn>")
def book_api(isbn):

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Invalid ISBN"}), 404

    # Get all reviews.  NB need to join users and reviews table to be able to get the reviews with username
    # todo = omit my review from this list
    reviewcount = db.execute("SELECT COUNT(review) FROM reviews WHERE isbn = :isbn",
                            {"isbn": isbn}).fetchone()
    reviewcount = reviewcount[0]
    if reviewcount != 0:
        reviewavg = db.execute("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn",
                            {"isbn": isbn}).fetchone()
        reviewavg = float(reviewavg[0])
    else:
        reviewavg = 0

    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": reviewcount,
            "average_score": reviewavg
                })


@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully logged out")
    return redirect(url_for('login'))
