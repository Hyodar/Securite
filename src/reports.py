
from flask import Blueprint, render_template, abort

from jinja2 import TemplateNotFound

reports = Blueprint('reports', __name__, url_prefix='/reports', template_folder='reports', static_folder='static')

@reports.route('/<string:website>/')
def load_report(website):
    try:
        report = website+'.html'
        return render_template(report)
    except TemplateNotFound:
        abort(404)

@reports.errorhandler(404)
def page_not_found(e):
    return render_template('report_not_found.html'), 404
