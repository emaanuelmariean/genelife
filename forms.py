
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    IntegerField,
    FloatField,
    SelectField,
    DateField,
    TextAreaField,
    SubmitField
)
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Nome Utente', validators=[DataRequired(), Length(min=2, max=100)])
    age = IntegerField('Età', validators=[DataRequired(), NumberRange(min=1)])
    gender = SelectField('Genere', choices=[('male', 'Maschio'), ('female', 'Femmina')], validators=[DataRequired()])
    weight = FloatField('Peso (kg)', validators=[DataRequired(), NumberRange(min=1)])
    height = FloatField('Altezza (cm)', validators=[DataRequired(), NumberRange(min=1)])
    activity_level = SelectField('Livello di attività', choices=[
        ('sedentary', 'Sedentario'),
        ('lightlyActive', 'Leggermente attivo'),
        ('moderatelyActive', 'Moderatamente attivo'),
        ('veryActive', 'Molto attivo')
    ], validators=[DataRequired()])
    goal = SelectField('Obiettivo della dieta', choices=[
        ('weightLoss', 'Perdita di peso'),
        ('maintenance', 'Mantenimento'),
        ('muscleGain', 'Aumento della massa muscolare')
    ], validators=[DataRequired()])
    submit = SubmitField('Registra e Genera Piano')

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError('Il nome utente è già in uso. Scegli un altro nome utente.')

class MealForm(FlaskForm):
    date = DateField('Data', validators=[DataRequired()])
    meal_type = SelectField('Tipo di Pasto', choices=[
        ('colazione', 'Colazione'),
        ('pranzo', 'Pranzo'),
        ('cena', 'Cena'),
        ('spuntino', 'Spuntino')
    ], validators=[DataRequired()])
    name = StringField('Nome del Pasto', validators=[DataRequired()])
    calories = FloatField('Calorie', validators=[DataRequired()])
    protein = FloatField('Proteine (g)', validators=[DataRequired()])
    carbs = FloatField('Carboidrati (g)', validators=[DataRequired()])
    fat = FloatField('Grassi (g)', validators=[DataRequired()])
    fiber = FloatField('Fibre (g)', validators=[DataRequired()])
    notes = TextAreaField('Note')
    submit = SubmitField('Salva Pasto')
    delete = SubmitField('Elimina Pasto')

class WeightForm(FlaskForm):
    date = DateField('Data', validators=[DataRequired()])
    weight = FloatField('Peso (kg)', validators=[DataRequired()])
    submit = SubmitField('Salva Peso')
