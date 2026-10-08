import os
from flask import Flask, render_template, request, redirect, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'bitacora-amor-2024')
os.makedirs('instance', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

DB_PATH = os.path.join('instance', 'bitacora.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user_id INTEGER, pareja TEXT, fecha TEXT, actividad TEXT, foto TEXT, musica TEXT)')
    conn.commit()
    conn.close()
init_db()

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db()
    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username=?', (request.form['username'],)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            return redirect('/')
        return "Usuario o clave mal"
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        try:
            conn = get_db()
            conn.execute('INSERT INTO users (username,password) VALUES (?,?)', (request.form['username'], generate_password_hash(request.form['password'])))
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            return "Usuario ya existe"
    return render_template('register.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    if 'user_id' not in session:
        return redirect('/login')
    pareja = request.form.get('pareja','')
    actividad = request.form.get('actividad','')
    musica = request.form.get('musica','')
    if 'youtube.com/watch?v=' in musica:
        musica = musica.replace('watch?v=', 'embed/')
    elif 'youtu.be/' in musica:
        musica = musica.replace('youtu.be/', 'www.youtube.com/embed/')
    foto_name = ''
    if 'foto' in request.files:
        f = request.files['foto']
        if f.filename != '':
            foto_name = secure_filename(datetime.now().strftime("%Y%m%d%H%M%S_") + f.filename)
            f.save(os.path.join('uploads', foto_name))
    conn = get_db()
    conn.execute('INSERT INTO posts (user_id,pareja,fecha,actividad,foto,musica) VALUES (?,?,?,?,?,?)', (session['user_id'], pareja, datetime.now().strftime("%d/%m/%Y"), actividad, foto_name, musica))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/salir')
def salir():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run()
