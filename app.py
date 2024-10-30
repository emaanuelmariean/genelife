# app.py

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
app.config['SECRET_KEY'] = 'tua_chiave_segreta_qui'  # Sostituisci con una chiave segreta sicura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///piano_alimentare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

        # Genera il piano alimentare per 7 giorni
        meal_plan = generate_meal_plan(user_needs, food_data, days=7)

        # Salva i pasti nel database
        for meal in meal_plan:
            new_meal = Meal(
                date=meal['date'],
                meal_type=meal['meal_type'],
                name=meal['name'],
                calories=meal['calories'],
                protein=meal['protein'],
                carbs=meal['carbs'],
                fat=meal['fat'],
                fiber=meal['fiber'],
                vitamins=meal['vitamins'],
                minerals=meal['minerals'],
                notes=meal.get('notes', ''),
                ingredients=meal['ingredients'],
                user_id=user.id
            )
            db.session.add(new_meal)

        db.session.commit()

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
    meals_data = []
    for meal in meals:
        meal_data = {
            'id': meal.id,
            'date': meal.date.strftime('%Y-%m-%d'),
            'meal_type': meal.meal_type,
            'name': meal.name,
            'calories': meal.calories,
            'protein': meal.protein,
            'carbs': meal.carbs,
            'fat': meal.fat,
            'fiber': meal.fiber,
            'vitamins': json.loads(meal.vitamins) if meal.vitamins else {},
            'minerals': json.loads(meal.minerals) if meal.minerals else {},
            'ingredients': json.loads(meal.ingredients) if meal.ingredients else [],
            'notes': meal.notes
        }
        meals_data.append(meal_data)

    # Ottieni l'ultima registrazione del peso
    last_weight_entry = WeightEntry.query.filter_by(user_id=user.id).order_by(WeightEntry.date.desc()).first()
    current_weight = last_weight_entry.weight if last_weight_entry else user.weight

    return render_template('dashboard.html', user=user, meals=meals_data, user_needs=user_needs, current_weight=current_weight)

# Rotta per il calendario
@app.route('/calendar')
def calendar_view():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    # Date di inizio e fine settimana
    today = date.today()
    start_week = today - timedelta(days=today.weekday())  # Lunedì
    end_week = start_week + timedelta(days=6)  # Domenica

    # Recupera i pasti per la settimana
    meals = Meal.query.filter(
        Meal.user_id == user.id,
        Meal.date >= start_week,
        Meal.date <= end_week
    ).order_by(Meal.date.asc()).all()

    # Organizza i pasti per giorno
    week_meals = {}
    for i in range(7):
        current_day = start_week + timedelta(days=i)
        current_day_str = current_day.strftime('%Y-%m-%d')
        week_meals[current_day_str] = []

    for meal in meals:
        meal.vitamins = json.loads(meal.vitamins)
        meal.minerals = json.loads(meal.minerals)
        meal.ingredients = json.loads(meal.ingredients) if meal.ingredients else []
        meal_date_str = meal.date.strftime('%Y-%m-%d')
        week_meals[meal_date_str].append(meal)

    return render_template('calendar.html', user=user, week_meals=week_meals, today=today)

# Rotta per il grafico del peso
@app.route('/weight_chart', methods=['GET', 'POST'])
def weight_chart_route():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json()
        date_str = data.get('date')
        weight = data.get('weight')
        if date_str and weight:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                # Controlla se esiste già una registrazione per questa data
                existing_entry = WeightEntry.query.filter_by(user_id=user.id, date=date_obj).first()
                if existing_entry:
                    existing_entry.weight = weight
                else:
                    new_entry = WeightEntry(user_id=user.id, date=date_obj, weight=weight)
                    db.session.add(new_entry)
                db.session.commit()
                return jsonify({'success': True}), 200
            except ValueError:
                return jsonify({'error': 'Formato data non valido.'}), 400
        else:
            return jsonify({'error': 'Dati non validi.'}), 400
    else:
        # Per le richieste GET, rendi il template
        return render_template('weight_chart.html', user=user)

# API Endpoint per Weight Entries
@app.route('/api/weight_entries', methods=['GET', 'POST'])
def manage_weight_entries():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non autorizzato'}), 401

    if request.method == 'POST':
        data = request.get_json()
        date_str = data.get('date')
        weight = data.get('weight')
        if date_str and weight:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                # Controlla se esiste già una registrazione per questa data
                existing_entry = WeightEntry.query.filter_by(user_id=user.id, date=date_obj).first()
                if existing_entry:
                    existing_entry.weight = weight
                else:
                    new_entry = WeightEntry(user_id=user.id, date=date_obj, weight=weight)
                    db.session.add(new_entry)
                db.session.commit()
                return jsonify({'success': True}), 200
            except ValueError:
                return jsonify({'error': 'Formato data non valido.'}), 400
        else:
            return jsonify({'error': 'Dati non validi.'}), 400

    elif request.method == 'GET':
        entries = WeightEntry.query.filter_by(user_id=user.id).order_by(WeightEntry.date.asc()).all()
        data = [{'id': entry.id, 'date': entry.date.strftime('%Y-%m-%d'), 'weight': entry.weight} for entry in entries]
        return jsonify(data), 200

# API Endpoint per singole Weight Entry (PUT e DELETE)
@app.route('/api/weight_entries/<int:entry_id>', methods=['PUT', 'DELETE'])
def single_weight_entry(entry_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non autorizzato'}), 401

    entry = WeightEntry.query.get(entry_id)
    if not entry or entry.user_id != user.id:
        return jsonify({'error': 'Registrazione non trovata o non autorizzato'}), 404

    if request.method == 'PUT':
        data = request.get_json()
        date_str = data.get('date')
        weight = data.get('weight')
        if date_str and weight:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                entry.date = date_obj
                entry.weight = weight
                db.session.commit()
                return jsonify({'success': True}), 200
            except ValueError:
                return jsonify({'error': 'Formato data non valido.'}), 400
        else:
            return jsonify({'error': 'Dati non validi.'}), 400

    elif request.method == 'DELETE':
        db.session.delete(entry)
        db.session.commit()
        return jsonify({'success': True}), 200

# API Endpoint per Meals CRUD
@app.route('/api/meals', methods=['POST', 'DELETE'])
def manage_meals():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non autorizzato'}), 401

    if request.method == 'POST':
        data = request.get_json()
        date_str = data.get('date')
        meal_type = data.get('meal_type')
        name = data.get('name')
        calories = data.get('calories')
        protein = data.get('protein', 0)
        carbs = data.get('carbs', 0)
        fat = data.get('fat', 0)
        fiber = data.get('fiber', 0)
        vitamins = data.get('vitamins', {})
        minerals = data.get('minerals', {})
        notes = data.get('notes', '')
        ingredients = data.get('ingredients', [])

        if date_str and meal_type and name and calories:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                new_meal = Meal(
                    date=date_obj,
                    meal_type=meal_type,
                    name=name,
                    calories=calories,
                    protein=protein,
                    carbs=carbs,
                    fat=fat,
                    fiber=fiber,
                    vitamins=json.dumps(vitamins),
                    minerals=json.dumps(minerals),
                    notes=notes,
                    ingredients=json.dumps(ingredients),
                    user_id=user.id
                )
                db.session.add(new_meal)
                db.session.commit()
                return jsonify({'success': True, 'meal_id': new_meal.id}), 201
            except ValueError:
                return jsonify({'error': 'Formato data non valido.'}), 400
        else:
            return jsonify({'error': 'Dati non validi.'}), 400

    elif request.method == 'DELETE':
        data = request.get_json()
        meal_id = data.get('id')
        if meal_id:
            meal = Meal.query.get(meal_id)
            if meal and meal.user_id == user.id:
                db.session.delete(meal)
                db.session.commit()
                return jsonify({'success': True}), 200
            else:
                return jsonify({'error': 'Pasto non trovato o non autorizzato.'}), 404
        else:
            return jsonify({'error': 'ID del pasto mancante.'}), 400

# API Endpoint per recuperare un singolo pasto (GET /api/meals/<id>)
@app.route('/api/meals/<int:meal_id>', methods=['GET'])
def get_meal(meal_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non autorizzato'}), 401

    meal = Meal.query.get(meal_id)
    if not meal or meal.user_id != user.id:
        return jsonify({'error': 'Pasto non trovato o non autorizzato.'}), 404

    meal_data = {
        'id': meal.id,
        'date': meal.date.strftime('%Y-%m-%d'),
        'meal_type': meal.meal_type,
        'name': meal.name,
        'calories': meal.calories,
        'protein': meal.protein,
        'carbs': meal.carbs,
        'fat': meal.fat,
        'fiber': meal.fiber,
        'vitamins': json.loads(meal.vitamins) if meal.vitamins else {},
        'minerals': json.loads(meal.minerals) if meal.minerals else {},
        'notes': meal.notes,
        'ingredients': json.loads(meal.ingredients) if meal.ingredients else []
    }

    return jsonify(meal_data), 200

# API Endpoint per aggiornare un pasto (PUT /api/meals/<id>)
@app.route('/api/meals/<int:meal_id>', methods=['PUT'])
def update_meal(meal_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Non autorizzato'}), 401

    meal = Meal.query.get(meal_id)
    if not meal or meal.user_id != user.id:
        return jsonify({'error': 'Pasto non trovato o non autorizzato.'}), 404

    data = request.get_json()
    date_str = data.get('date')
    meal_type = data.get('meal_type')
    name = data.get('name')
    calories = data.get('calories')
    protein = data.get('protein', 0)
    carbs = data.get('carbs', 0)
    fat = data.get('fat', 0)
    fiber = data.get('fiber', 0)
    vitamins = data.get('vitamins', {})
    minerals = data.get('minerals', {})
    notes = data.get('notes', '')
    ingredients = data.get('ingredients', [])

    if date_str and meal_type and name and calories:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            meal.date = date_obj
            meal.meal_type = meal_type
            meal.name = name
            meal.calories = calories
            meal.protein = protein
            meal.carbs = carbs
            meal.fat = fat
            meal.fiber = fiber
            meal.vitamins = json.dumps(vitamins)
            meal.minerals = json.dumps(minerals)
            meal.notes = notes
            meal.ingredients = json.dumps(ingredients)
            db.session.commit()
            return jsonify({'success': True}), 200
        except ValueError:
            return jsonify({'error': 'Formato data non valido.'}), 400
    else:
        return jsonify({'error': 'Dati non validi.'}), 400

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

# Funzione per generare il piano alimentare per una settimana con 5 pasti al giorno
def generate_meal_plan(user_needs, food_data, days=7):
    meal_types = ['colazione', 'spuntino_mattina', 'pranzo', 'spuntino_pomeriggio', 'cena']
    meal_plan = []

    for day_offset in range(days):
        meal_date = date.today() + timedelta(days=day_offset)
        for meal_type in meal_types:
            # Mappa il tipo di pasto con i dati alimentari
            meal_key = 'spuntino' if 'spuntino' in meal_type else meal_type
            meals = food_data.get(meal_key, [])
            if not meals:
                print(f"Nessun pasto disponibile per {meal_key}")
                continue

            # Seleziona un pasto casuale tra quelli disponibili
            selected_meal = random.choice(meals)

            meal = {
                'date': meal_date,
                'meal_type': meal_type,
                'name': selected_meal['name'],
                'calories': selected_meal['calories'],
                'protein': selected_meal['protein'],
                'carbs': selected_meal['carbs'],
                'fat': selected_meal['fat'],
                'fiber': selected_meal['fiber'],
                'vitamins': json.dumps(selected_meal.get('vitamins', {})),
                'minerals': json.dumps(selected_meal.get('minerals', {})),
                'notes': '',
                'ingredients': json.dumps(selected_meal.get('ingredients', []))
            }

            meal_plan.append(meal)

    return meal_plan

# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Avvio dell'applicazione
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
