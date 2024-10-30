# openfoodfacts_products.py

import json
import random

def load_food_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        food_data = json.load(f)
    return food_data

def generate_meal_plan(user_needs, food_data):
    meal_types = ['colazione', 'spuntino', 'pranzo', 'cena']
    meal_plan = []

    for meal_type in meal_types:
        meals = food_data.get(meal_type, [])
        if not meals:
            print(f"Nessun pasto disponibile per {meal_type}")
            continue

        # Seleziona un pasto casuale tra quelli disponibili
        selected_meal = random.choice(meals)

        meal = {
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
            'ingredients': selected_meal.get('ingredients', [])
        }

        meal_plan.append(meal)

    return meal_plan
