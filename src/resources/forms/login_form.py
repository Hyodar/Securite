
from wtforms import StringField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.validators import InputRequired

from flask_wtf import FlaskForm


class LoginForm(FlaskForm):
    username = StringField(
        'username',
        validators=[
            InputRequired('Insira um nome de usuário')])

    password = PasswordField(
        'password',
        validators=[
            InputRequired('Insira uma senha')])

    submit = SubmitField('Entrar')
