from flask import Flask, request, jsonify, render_template, redirect, session, url_for
import sqlite3
from pwned import *
import favicon

app = Flask(__name__)
app.secret_key = 'cool'
DB = 'passwords.db'

# Initialize DB
def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
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
        # Create test user if doesn't exist
        c.execute("SELECT * FROM logins WHERE username = ?", ('test',))
        if not c.fetchone():
            c.execute("INSERT INTO logins (username, password) VALUES (?, ?)", ('test', 'test'))

        conn.commit()

# Home route (view passwords)
@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    query = request.args.get('query', '')
    user_id = session.get('user_id')

    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        if query:
            c.execute('''
                SELECT id, site, username, password FROM credentials 
                WHERE user_id = ? AND (site LIKE ? OR username LIKE ?)
            ''', (user_id, f'%{query}%', f'%{query}%'))
        else:
            c.execute('SELECT id, site, username, password FROM credentials WHERE user_id = ?', (user_id,))
        entries = c.fetchall()
    return render_template('index.html', entries=entries, query=query)

# Add credential
@app.route('/add', methods=['POST'])
def add_credential():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    site = request.form['site']
    username = request.form['username']
    password = request.form['password']
    user_id = session.get('user_id')

    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO credentials (user_id, site, username, password) VALUES (?, ?, ?, ?)',
                  (user_id, site, username, password))
        conn.commit()
    return redirect('/')

# Delete credential (only if it belongs to user)
@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_credential(entry_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM credentials WHERE id = ? AND user_id = ?', (entry_id, user_id))
        conn.commit()
    return redirect('/')

# Login
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
            session['user_id'] = user[0]  # Store user_id
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM logins WHERE username = ?", (username,))
            existing_user = c.fetchone()

            if existing_user:
                return render_template('register.html', error="Username already exists")

            c.execute("INSERT INTO logins (username, password) VALUES (?, ?)", (username, password))
            conn.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# Dashboard: check passwords with Pwned API
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('SELECT id, site, username, password FROM credentials WHERE user_id = ?', (user_id,))
        entries = c.fetchall()
        entries = [entry + (check_password(entry[3]), ) for entry in entries]
    return render_template('dashboard.html', entries=entries)

@app.route('/settings')
def settings():
    return render_template('settings.html')
# Start the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
