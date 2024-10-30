# Importa le librerie necessarie
from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Sostituisci con una chiave segreta sicura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///piano_alimentare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
migrate = Migrate(app, db)

def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db)

init_app(app)

# Definizione dei modelli del database
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)  # Campo per la password hash
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    activity_level = db.Column(db.String(20), nullable=False)
    goal = db.Column(db.String(20), nullable=False)
    meals = db.relationship('Meal', backref='user', lazy=True)
    weight_entries = db.relationship('WeightEntry', backref='user', lazy=True)

    # Metodo per impostare la password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Metodo per verificare la password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Meal(db.Model):
    __tablename__ = 'meal'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    fiber = db.Column(db.Float, nullable=False)
    vitamins = db.Column(db.Text)  # JSON string
    minerals = db.Column(db.Text)  # JSON string
    notes = db.Column(db.Text)
    ingredients = db.Column(db.Text)  # JSON string
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class WeightEntry(db.Model):
    __tablename__ = 'weight_entry'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    weight = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Percorso del file JSON con i dati alimentari
FOOD_DATA_PATH = 'food_data.json'  # Assicurati che il file si trovi nella stessa directory

# Funzione per caricare i dati alimentari
def load_food_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        food_data = json.load(f)
    return food_data

food_data = load_food_data(FOOD_DATA_PATH)

# Funzione per ottenere l'utente corrente
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

# Filtro per formattare le date nel template
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%A %d/%m/%Y'):
    return datetime.strptime(value, '%Y-%m-%d').strftime(format)

# Funzione per calcolare i bisogni nutrizionali dell'utente
def calculate_user_needs(user):
    # Calcolo del metabolismo basale (BMR) usando la formula di Mifflin-St Jeor
    if user.gender.lower() == 'male':
        bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age + 5
    else:
        bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age - 161

    # Fattore di attività
    activity_levels = {
        'sedentary': 1.2,
        'lightlyActive': 1.375,
        'moderatelyActive': 1.55,
        'veryActive': 1.725
    }
    activity_factor = activity_levels.get(user.activity_level, 1.2)

    # Calorie totali giornaliere (TDEE)
    tdee = bmr * activity_factor

    # Adatta le calorie in base all'obiettivo
    if user.goal == 'weightLoss':
        tdee -= 500
    elif user.goal == 'muscleGain':
        tdee += 500

    # Macronutrienti
    protein = user.weight * 1.8  # 1.8g per kg di peso corporeo
    fat = tdee * 0.25 / 9        # 25% delle calorie dai grassi
    carbs = (tdee - (protein * 4) - (fat * 9)) / 4

    return {
        'calories': round(tdee, 2),
        'protein': round(protein, 2),
        'fat': round(fat, 2),
        'carbs': round(carbs, 2)
    }

# Rotta per la home (reindirizza alla dashboard se autenticato, altrimenti alla pagina di login)
@app.route('/', methods=['GET'])
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Rotta per la registrazione
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = int(request.form['age'])
        gender = request.form['gender']
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        activity_level = request.form['activity_level']
        goal = request.form['goal']

        # Controlla se l'username esiste già
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Questo username è già in uso. Per favore, scegline un altro.')
            return redirect(url_for('register'))

        # Crea un nuovo utente
        user = User(
            username=username,
            age=age,
            gender=gender,
            weight=weight,
            height=height,
            activity_level=activity_level,
            goal=goal
        )
        user.set_password(password)  # Imposta la password hashata
        db.session.add(user)
        db.session.commit()

        # Calcola i bisogni nutrizionali dell'utente
        user_needs = calculate_user_needs(user)

        # Imposta la sessione dell'utente
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))

    return render_template('register.html')

# Rotta per il login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Username o password non validi.')
            return redirect(url_for('login'))

    return render_template('login.html')

# Rotta per il logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Rotta per la dashboard
@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    # Ricalcola i bisogni nutrizionali dell'utente
    user_needs = calculate_user_needs(user)

    # Pasti di oggi
    meals = Meal.query.filter_by(user_id=user.id, date=date.today()).all()
    return render_template('dashboard.html', user=user, meals=meals, user_needs=user_needs)

# Avvio dell'applicazione
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
