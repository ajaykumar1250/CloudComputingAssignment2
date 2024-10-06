from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Define the database and upload directories
DATABASE = '/home/ubuntu/mydatabase.db'
UPLOAD_FOLDER = '/home/ubuntu/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('register.html')

# Function to connect to the SQLite database
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # So we can access rows as dictionaries
    return conn

# Create the users table if it doesn't exist
def create_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Route for registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')

        # Handle file upload
        file = request.files.get('file')
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, f"{username}_file.txt")
            file.save(file_path)

            # Word count logic
            with open(file_path, 'r') as f:
                content = f.read()
                word_count = len(content.split())
        else:
            flash('Please upload a text file.')
            return redirect(url_for('register'))

        # Insert user details into the database
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, firstname, lastname, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password, firstname, lastname, email))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            flash('Username already exists!')
            return redirect(url_for('register'))

        # Save the word count in the session for later use
        session['word_count'] = word_count

        # Redirect to the login page after successful registration
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

# Route for the profile page that shows user info and word count
@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('You need to login first.')
        return redirect(url_for('login'))

    username = session['username']
    word_count = session.get('word_count')  # Retrieve word count from session

    # Retrieve user details from the database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username, firstname, lastname, email FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        flash('User not found!')
        return redirect(url_for('register'))

    return render_template('profile.html', user=user, word_count=word_count)

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the user exists in the database and verify password
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username

            # Retrieve the word count for this user from session if registered before login
            word_count = session.get('word_count')
            if word_count:
                flash('Login successful!')
                return redirect(url_for('profile'))
            else:
                flash('Login successful, but no word count available.')
                return redirect(url_for('profile'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

    return render_template('login.html')

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/download/<filename>')
def download_file(filename):
    # Ensure that the username is in session to restrict access
    if 'username' not in session:
        flash('You need to login first.')
        return redirect(url_for('login'))

    # Use send_from_directory to send the file for download
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    create_table()
    app.run(debug=True)

