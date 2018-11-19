
from wtforms import StringField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.validators import InputRequired
from wtforms.validators import Length

from flask_wtf import FlaskForm


class RegisterForm(FlaskForm):
    username = StringField(
        'username',
        validators=[
            InputRequired('Insira um nome de usuário'),
            Length(min=5, max=15,
                   message='Seu nome de usuário deve ter entre 5 e 15 caracteres')])

    password = PasswordField(
        'password',
        validators=[
            InputRequired('Insira uma senha'),
            Length(min=5, max=15,
                   message='Sua senha deve ter entre 5 e 15 caracteres')])

    submit = SubmitField('Registrar')
