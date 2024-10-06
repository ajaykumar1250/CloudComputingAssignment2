from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Define the database and upload directories
DATABASE = '/home/ubuntu/mydatabase.db'
UPLOAD_FOLDER = '/home/ubuntu/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

        # Insert user details into the database (without file path or word count)
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

        # Redirect to the profile page with word count after successful registration
        return redirect(url_for('profile', username=username, word_count=word_count))

    return render_template('register.html')

# Route for the profile page that shows user info and word count
@app.route('/profile')
def profile():
    username = request.args.get('username')
    word_count = request.args.get('word_count')

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

if __name__ == '__main__':
    create_table()
    app.run(debug=True)
