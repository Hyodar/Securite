
from wtforms import StringField
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.validators import InputRequired

import re

from flask_wtf import FlaskForm


class UrlHostRequired(object):
    def __init__(self, message=None):
        if not message:
            message = 'The url must contain a valid host'
        self.message = message

    def __call__(self, form, field):
        url = field.data or 0
        url = re.match('^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)*(?P<host>((\w+\.)?\w+\.\w+|))(\/[a-z]*)*?$', url)

        if url is None:
            raise ValidationError(self.message)


class WebsiteForm(FlaskForm):
    url = StringField(
        'Url:',
        validators=[
            InputRequired('Insira uma URL para análise'),
            UrlHostRequired('Insira um domínio válido para análise')])

    submit = SubmitField('Enviar')
