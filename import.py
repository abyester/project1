import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("postgres://grsjdnffxwzfts:a79db4f2af1db503e002d89257980bc9ff0acdc2f9389c1b07af74e473d3a5a9@ec2-54-75-251-84.eu-west-1.compute.amazonaws.com:5432/dnihkrbr0dt0g"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book with ISBN number {isbn} and title {title}.")
    db.commit()

if __name__ == "__main__":
    main()
