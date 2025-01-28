from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)

def add_to_db(website, username, password, db):
    ###############################
    #                             #
    #       ADDING TO TABLES      #
    #                             #
    ###############################
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()


        c.execute("""INSERT INTO User (username, password) 
                     VALUES (?, ?)""", (username, password))


        user_id = c.lastrowid


        c.execute("""INSERT INTO Websites (user_id, name, url) 
                     VALUES (?, ?, ?)""", (user_id, website, f"{website}.com"))


        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Error inserting into the database: {e}")
    finally:
        conn.close()

def get_data_from_db(db):
    ###############################
    #                             #
    #       deleting things       #
    #                             #
    ###############################
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()


        c.execute("""
            SELECT Websites.name, Websites.url, User.username, User.password
            FROM Websites
            JOIN User ON Websites.user_id = User.user_id
        """)
        data = c.fetchall()  
        return data
    except sqlite3.Error as e:
        print(f"Error fetching data from database: {e}")
        return []
    finally:
        conn.close()

def delete_from_db(website, db):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()


        c.execute("DELETE FROM Websites WHERE name = ?", (website,))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting data from database: {e}")
    finally:
        conn.close()

def importdb(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    ###############################
    #                             #
    #       Making tables         #
    #                             #
    ###############################

    c.execute("""CREATE TABLE IF NOT EXISTS User (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )""")


    c.execute("""CREATE TABLE IF NOT EXISTS Websites (
        website_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
    )""")

    conn.close()

@app.route("/", methods=["POST", "GET"])
def form():
    db = "database.db"

    if request.method == "POST":
        website = request.form.get("website")
        username = request.form.get("username")
        password = request.form.get("password")

        # Add data to the database
        add_to_db(website, username, password, db)

        # Redirect to avoid duplicate submissions
        return redirect(url_for('form'))

    # Fetch data to display on the page
    data = get_data_from_db(db)
    return render_template("index.html", data=data)

@app.route("/delete", methods=["POST"])
def delete():
    db = "database.db"
    website = request.form.get("website")
    delete_from_db(website, db)
    return redirect(url_for('form'))

# Call the function to set up the database
importdb("database.db")
@app.route("/autocomplete")
def menu():
    return render_template("autocomplete.html")
@app.route("/index")
def menu1():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
