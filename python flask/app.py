from flask import Flask, request, jsonify, render_template, redirect, session, url_for
import sqlite3
from pwned import *
import favicon
app = Flask(__name__)
app.secret_key = 'cool'  # SOME SESSION SHIT IDK
DB = 'passwords.db'

# FUCK ASS BITCH DB
def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                site TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES logins(id)
            )
        ''')

        # SHIT DONT EXIST
        c.execute("SELECT * FROM logins WHERE username = ?", ('test',))
        if not c.fetchone():
            c.execute("INSERT INTO logins (username, password) VALUES (?, ?)", ('test', 'test'))

        conn.commit()


# STUPID ASS LOGIN
@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('SELECT id, site, username, password FROM credentials')
        entries = c.fetchall()
    return render_template('index.html', entries=entries)


# NEW PASSWORD TYPE SHIT
@app.route('/add', methods=['POST'])
def add_credential():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    site = request.form['site']
    username = request.form['username']
    password = request.form['password']
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO credentials (site, username, password) VALUES (?, ?, ?)', (site, username, password))
        conn.commit()
    return redirect('/')



# GET YO ASS OUTA HERE
@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_credential(entry_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM credentials WHERE id = ?', (entry_id,))
        conn.commit()
    return redirect('/')



# WHO TF IS U
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM logins WHERE username = ? AND password = ?", (username, password))
            user = c.fetchone()

        if user:
            session['logged_in'] = True
            session['username'] = username  
            return redirect('/') 
        else:
            print("nope")
            return render_template('login.html', error="Invalid username or password")
            

    return render_template('login.html')


#BYE BYE
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            # DOES SHIT EXIST?
            c.execute("SELECT * FROM logins WHERE username = ?", (username,))
            existing_user = c.fetchone()

            if existing_user:
                return render_template('register.html', error="Username already exists")

            # RETARD SIGNED UP
            c.execute("INSERT INTO logins (username, password) VALUES (?, ?)", (username, password))
            conn.commit()

        return redirect(url_for('login'))

    return render_template('register.html')



#DASHBOARD TYPA SHIT
@app.route('/dashboard')
def dashboard():
    #CALL API TO SEE IF YO ASS EXPOSED
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('SELECT id, site, username, password FROM credentials')
        entries = c.fetchall()
        print(entries)
        entries = [i + (check_password(i[-1]), ) for i in entries]
    #SENDS API RESPONSE <3
    return render_template('dashboard.html', entries=entries)




# RUN PLS
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
