from flask import Flask, request, jsonify, render_template, redirect, session, url_for, flash
import sqlite3
from pwned import *
from flask_cors import CORS
import os


app = Flask(__name__)
app.secret_key = 'cool'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = not app.debug
DB = 'passwords.db'
CORS(app, supports_credentials=True, origins=["chrome-extension://bfhemombiahlnjekihjamikmoghjcccc"])


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
                favorite BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES logins(id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                email TEXT,
                auto_logout BOOLEAN DEFAULT 0,
                breach_notifications BOOLEAN DEFAULT 1,
                theme TEXT DEFAULT 'dark',
                FOREIGN KEY (user_id) REFERENCES logins(id)
            )
        ''')
        
        # Add favorite column if it doesn't exist
        try:
            c.execute('ALTER TABLE credentials ADD COLUMN favorite BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            # Column already exists, ignore error
            pass

        # Create test user if doesn't exist
        c.execute("SELECT * FROM logins WHERE username = ?", ('test',))
        if not c.fetchone():
            c.execute("INSERT INTO logins (username, password) VALUES (?, ?)", ('test', 'test'))
            # Create default settings for test user
            c.execute("INSERT INTO settings (user_id, theme) VALUES (1, 'dark')")

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
                SELECT id, site, username, password, favorite FROM credentials 
                WHERE user_id = ? AND (site LIKE ? OR username LIKE ?)
            ''', (user_id, f'%{query}%', f'%{query}%'))
        else:
            c.execute('SELECT id, site, username, password, favorite FROM credentials WHERE user_id = ?', (user_id,))
        entries = c.fetchall()
    return render_template('index.html', entries=entries, query=query)

# Add credential
@app.route('/add', methods=['POST'])
def add_credential():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    site = request.form['site']
    username = request.form['username']
    password = request.form['password']
    user_id = session.get('user_id')

    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO credentials (user_id, site, username, password, favorite) VALUES (?, ?, ?, ?, 0)',
                  (user_id, site, username, password))
        conn.commit()

    return redirect(url_for('home'))

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

# Toggle favorite status
@app.route('/toggle_favorite/<int:entry_id>', methods=['POST'])
def toggle_favorite(entry_id):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    user_id = session.get('user_id')

    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        # Get current favorite status
        c.execute('SELECT favorite FROM credentials WHERE id = ? AND user_id = ?', (entry_id, user_id))
        result = c.fetchone()
        if result:
            current_status = result[0]
            # Toggle the status
            new_status = 0 if current_status else 1
            c.execute('UPDATE credentials SET favorite = ? WHERE id = ? AND user_id = ?', 
                     (new_status, entry_id, user_id))
            conn.commit()
            return jsonify({'success': True, 'favorite': bool(new_status)})
        return jsonify({'success': False, 'message': 'Entry not found'}), 404

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

@app.route("/favorites")
def favorites():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('SELECT id, site, username, password FROM credentials WHERE user_id = ? AND favorite = 1', (user_id,))
        entries = c.fetchall()
    return render_template('favorites.html', entries=entries)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/settings')
def settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM settings WHERE user_id = ?', (user_id,))
        settings_data = c.fetchone()
        
        if not settings_data:
            # Create default settings if they don't exist
            c.execute('INSERT INTO settings (user_id, theme) VALUES (?, ?)', (user_id, 'dark'))
            conn.commit()
            settings_data = (user_id, None, 0, 1, 'dark')
        
        settings = {
            'email': settings_data[1],
            'auto_logout': bool(settings_data[2]),
            'breach_notifications': bool(settings_data[3]),
            'theme': settings_data[4]
        }
    
    return render_template('settings.html', settings=settings)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    username = request.form.get('username')
    email = request.form.get('email')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    auto_logout = 'auto_logout' in request.form
    breach_notifications = 'breach_notifications' in request.form
    theme = request.form.get('theme', 'dark')

    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        
        # Update username if changed
        if username != session['username']:
            c.execute('UPDATE logins SET username = ? WHERE id = ?', (username, user_id))
            session['username'] = username
        
        # Update password if provided
        if current_password and new_password and confirm_password:
            # Verify current password
            c.execute('SELECT password FROM logins WHERE id = ?', (user_id,))
            stored_password = c.fetchone()[0]
            
            if stored_password != current_password:
                flash('Current password is incorrect')
                return redirect(url_for('settings'))
            
            if new_password != confirm_password:
                flash('New passwords do not match')
                return redirect(url_for('settings'))
            
            c.execute('UPDATE logins SET password = ? WHERE id = ?', (new_password, user_id))
        
        # Update settings
        c.execute('''
            UPDATE settings 
            SET email = ?, auto_logout = ?, breach_notifications = ?, theme = ?
            WHERE user_id = ?
        ''', (email, auto_logout, breach_notifications, theme, user_id))
        
        conn.commit()
    
    flash('Settings updated successfully')
    return redirect(url_for('settings'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    
    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        # Delete user's credentials
        c.execute('DELETE FROM credentials WHERE user_id = ?', (user_id,))
        # Delete user's settings
        c.execute('DELETE FROM settings WHERE user_id = ?', (user_id,))
        # Delete user's login
        c.execute('DELETE FROM logins WHERE id = ?', (user_id,))
        conn.commit()
    
    session.clear()
    return redirect(url_for('login'))

# API route to check login status and return username
@app.route('/api/user')
def api_user():
    if not session.get('logged_in'):
        return jsonify({'logged_in': False})
    return jsonify({
        'logged_in': True,
        'username': session.get('username')
    })
    
# Start the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1')

