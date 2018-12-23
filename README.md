# Project 1

Web Programming with Python and JavaScript

import.py

  This was used to upload book data to the heroku site.

  Key elements were -

  -amending the CSV file to delete the header (which was erroneously uploaded - and caused errors - otherwise)

  -checking the length of ISBN numbers - those ISBN numbers with trailing zeros had had those zeros cut off, meaning the right references couldn't be found on Goodreads.  zfill was used to fill in missing zeros

application.py

 This was the main application used for managing users and their reviews of books.  Key elements include -

  -checking for enviornment variables (the DATABASE_URL and GOODREADS_KEY) which have to therefore be entered on the command login_required

  -login_required: this was a "wrapped_view" that checks whether a "usid" has been set (in the session variable), i.e. that a user had logged in.  If not, it directs the user to the login page for all views that require a login

  -index route: can only be reached if user logged in.  When reached by GET - just gives you a form (in index.html) which allows you to search for a book by isbn, title or author.  When reached by POST - i.e. when you've submitted the form - it will check your seartext is valid and then carry out a search from the database according to criteria you've set. LIKE is used - alongside % before and after the search term - to allow for a range of results that contain that term.  If results are found those are then added on the bottom of the index page (using jinja in index.html that checks for result)

  -login route: if reached by GET just gives you a login form in login.html.  If reached by POST - i.e. you've submitted the form - it will check username and password against the database.  check_password_hash hash is used to verify if the password is correct (from werkzeug.security)

  -register route: if reached by GET just gives you a register form in register.html.  If reached by POST - i.e. you've submitted the form - it will first check a username and password has actually been entered; and second check that the username does not already exist.  Assuming both of these are teh case, it will insert the username and password into the users table in the database.  generate_password_hash hash is used to verify if the password is correct (from werkzeug.security)

  -book/<isbn> route: this can either be reached from the index page (after a search has returned a number of books) or by directly entering an isbn in the address bar.  The route will then check whether a book with this ISBN actually exists, sending the user back to the index page if not.

    If the book does exist, the programme then searches for all reviews on the book, also getting the username through a join with the users table (on userid).  It then also searches for whether the logged in user has left a review.

    Jinga in book.html will check whether myreview exists - if it does, it will display that review.  If it doesn't, it provides a form that allows the user to enter a review (and the POST elements in the route handle the submitting of that review)

    Lastly the route gets uses the goodreads API, "review_counts" to get data on the average rating and number of ratings given on goodreads, using the goodreads key (an environment variable) and the book's ISBN.  If the API successfully returns (i.e. status_code 200) then this data is extracted from the resulting json file (slightly torturously so)   

    -api/<isbn> route: this route provides a json output of the books title, author, year, isbn, review count and average review score.  First the route checks that there is a valid isbn in the url (i.e. there is data for the book int he books table).  The review count and average score have to be calculated through interrogating the reviews table (first the COUNT or reviews for that isbn, then the AVG rating).  If there are no reviews, the average is set manually as zero. The reviewavg has to be transformed using a float() command as otherwise it comes out as a "decimal" that can't be handled by jsonify, the handler used to create the json output

    -logout route: this similar clear the userid that had been set in the "session" variable and redirects the user to the login pages

    -layout.html: sets the basic layout of the pages.  This includes a bootstrap navbar which differs on whether the user is logged in or not (userid has to be sent to the page for this to work; a better way might be to use a global variable g.user in future).  The layout also includes provision for alerts, which draw on bootstrap alert formatting (alert alert-info).  Error messages are built into the individual pages (drawing on bootstrap's alert alert-danger).  It might be more efficient to rationalise these in a future release.
