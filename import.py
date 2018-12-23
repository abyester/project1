import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

##link here to heroku engine

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

##don't forget to remove csv file headers before seeking to upload

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        ##correct for missing zeros in isbns
        if len(isbn) < 10:
            isbn=isbn.zfill(10)
        elif len(isbn) > 10 and len(isbn) < 13:
            isbn=isbn.zfill(13)

        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book with ISBN number {isbn} and title {title}.")
    db.commit()

if __name__ == "__main__":
    main()
