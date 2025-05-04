from flask import Flask, request, jsonify, render_template, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'  # Required for sessions
DB = 'passwords.db'

# Database Initialization
def init_db():
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()

        # Create users (logins) table
        c.execute('''
            CREATE TABLE IF NOT EXISTS logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Create credentials table linked to users
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

        # Insert default user if doesn't exist
        c.execute("SELECT * FROM logins WHERE username = ?", ('test',))
        if not c.fetchone():
            c.execute("INSERT INTO logins (username, password) VALUES (?, ?)", ('test', 'test'))

        conn.commit()


# Home page (requires login)
@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('SELECT id, site, username, password FROM credentials')
        entries = c.fetchall()
    return render_template('index.html', entries=entries)

# Add credential
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

# Delete credential
@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_credential(entry_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM credentials WHERE id = ?', (entry_id,))
        conn.commit()
    return redirect('/')

# Login route
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
            session['username'] = username  # optional, for personalizing later
            return redirect('/')  # ✅ Goes to index.html via home() route
        else:
            print("nope")
            return render_template('login.html', error="Invalid username or password")
            

    return render_template('login.html')



# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Run server
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
