from flask import Flask, request, redirect, render_template, flash
import sqlite3
import hashlib
import re

app = Flask(__name__)
app.secret_key = 'some_secret_key'

# Initialize SQLite database
def init_db():
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS url_mapping
                          (short_url TEXT PRIMARY KEY, original_url TEXT, access_count INTEGER DEFAULT 0)''')

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url']
        custom_alias = request.form.get('alias')

        # Validate URL
        if not re.match(r'http(s)?://', original_url):
            flash('Invalid URL format. Ensure it starts with http:// or https://')
            return redirect('/')

        # Generate short URL
        if custom_alias:
            short_url = custom_alias
        else:
            short_url = hashlib.md5(original_url.encode()).hexdigest()[:6]

        with sqlite3.connect('urls.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO url_mapping (short_url, original_url) VALUES (?, ?)', (short_url, original_url))
            except sqlite3.IntegrityError:
                flash('Custom alias already in use. Choose a different one.')
                return redirect('/')
        return f"Shortened URL: {request.host_url}{short_url}"
    return render_template('index.html')

@app.route('/<short_url>')
def redirect_to_original(short_url):
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT original_url FROM url_mapping WHERE short_url = ?', (short_url,))
        original_url = cursor.fetchone()
        if original_url:
            cursor.execute('UPDATE url_mapping SET access_count = access_count + 1 WHERE short_url = ?', (short_url,))
            return redirect(original_url[0])
    return "URL not found", 404

@app.route('/stats/<short_url>')
def stats(short_url):
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT access_count FROM url_mapping WHERE short_url = ?', (short_url,))
        count = cursor.fetchone()
        if count:
            return f"The URL {request.host_url}{short_url} has been accessed {count[0]} times."
    return "URL not found", 404

if __name__ == '__main__':
    app.run(debug=True)
