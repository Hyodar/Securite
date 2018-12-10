# Flask -> python pra executar

# Estrutura básica:
#   Flask pra fazer os subdiretorios normais
#   Flask pra fazer os {for}, {block}, etc. nos html
#   Flask pra fazer o subdiretorio de execucao com request POST do site a ser escaneado
#   -----------------------------------------------------------------------------------
#   Quando entrar no subdiretorio de execucao, usar python pra executar o wapiti do console
#   exemplo: "python wapiti http://mysite.com -n 10 -b folder -u -v 1 -f html -o /tmp/scan_report"
#   cor dos icones: #a4a4a4
#   icones escuros: #8b8b8b
#   creditos dos icones:
#   https://loading.io/icon/9fjrdd - jornal
#   https://loading.io/icon/o6fx3j - +
#   https://loading.io/icon/ftmwrw - seta
#   https://loading.io/icon/vfw3jt - globo
#   https://loading.io/icon/ftmwrw - flecha
#   https://loading.io/icon/npoqjc - icone report da lista
#   https://loading.io/icon/37uyl2 - icone logout

# http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#broker-redis

# CONFIG SET dir /mnt/d/Users/Franco/Documents/PI_2/redis
# CONFIG SET dbfilename redis_db.rdb

# Redis:
#   cd pro diretorio do projeto/redis
#   redis-server
# RQ:
#   cd pro diretorio do projeto/src
#   rq worker
# RQ-Scheduler:
#   cd pro diretorio do projeto/src
#   rqscheduler
# Flask:
#   cd pro diretorio do projeto/src
#   python3 run_project.py
# Adicionar environment variable no subsystem de linux:
#   cmd: C:\Windows\System32\bash.exe ~ --login
#   sudo vi .bashrc ou .profile


import os
import json
import re
import subprocess
import requests
from datetime import datetime
import pytz

from flask import Flask
from flask import request
from flask import session
from flask import redirect
from flask import render_template
from flask import url_for
from flask import Blueprint
from flask import current_app
from flask_sqlalchemy import SQLAlchemy  # banco de dados
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from passlib.hash import sha256_crypt  # hashing de senhas

from reports import reports  # Blueprint pra acessar os reports como templates

from rq import Queue, Connection  # task queueing
from redis import Redis  # comunicação com rq
from rq_scheduler import scheduler  # scheduler com cron pro rq

from resources import tasks  # .py de tasks pra mandar pro rq[
from resources.forms import login_form
from resources.forms import register_form
from resources.forms import website_form


#Conexões redis e rq
redis_conn = Redis()
q = Queue(connection=redis_conn)

#Criação do app Flask
server = Flask(__name__)
server.secret_key = os.urandom(24)
server.register_blueprint(reports)  # Adiciona o blueprint de exibição dos reports no projeto

#Configurações do SQLAlchemy
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

#Criação da classe de db do SQLAlchemy
db = SQLAlchemy(server)

# Tabelas do SQL -------------------------------------------------------------------------------------------------------
class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(40))
    password = db.Column('password', db.String(30))
    joined_at = db.Column('joined_at', db.String(30))


class Website(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    url = db.Column('url', db.String(400))
    updated_at = db.Column('updated_at', db.String(10))

# Cria as tabelas
db.create_all()
#-----------------------------------------------------------------------------------------------------------------------

#Criação do app de admin
server.config['FLASK_ADMIN_SWATCH'] = 'readable'
admin = Admin(server)

class MyModelView(ModelView):
    page_size = 50

admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Website, db.session))

# path dos json
json_users = './database/users.json'
json_server = './database/server.json'

#Configuração do Recaptcha
server.config['RECAPTCHA_PUBLIC_KEY'] = '6Leiwn4UAAAAAPnBc65KlDZnnXJ719Pp_fgdqIRp'
server.config['RECAPTCHA_PRIVATE_KEY'] = os.environ.get('recaptcha_securite') # environment variable para segurança

#Timezone do Brasil:
local_tz = pytz.timezone('Brazil/East')

#Indicador que o server ta ligado
server_state = True

@server.route('/')
def index():
    return render_template('index.html')


@server.route('/login/', methods=['GET', 'POST'])
def login():
    form = login_form.LoginForm()
    logged_user = session.get('user')

    not_logged = request.args.get('not_logged')
    login_error = request.args.get('login_error')
    login_exception = request.args.get('login_exception')
    register_successful = request.args.get('register_successful')
    delete_success = request.args.get('delete_success')
    delete_exception = request.args.get('delete_exception')
    account_deleted = request.args.get('account_deleted')

    if request.method == 'POST' and request.form.get('type') == None and logged_user == None:

        session['user'] = None
        username = request.form['username']
        password = request.form['password']

        if not form.validate():
            return render_template('login.html', form=form)

        try:
            user = User.query.filter_by(username=username).first()

            if user == []:
                return redirect(url_for('login', login_error=True))
            else:
                if sha256_crypt.verify(password, user.password):
                    session['user'] = user.id

                    return redirect(url_for('manage',server_state=server_state,
                               recent_security_check=get_recent_security_check()))
                else:
                    return redirect(url_for('login', login_error=True))
        except Exception as e:
            print(e)
            return redirect(url_for('login', login_error=True))

    elif request.args.get('log_out'):
        session['user'] = None
        return redirect(url_for('login'))

    elif logged_user != None:
        return redirect(url_for('manage',server_state=server_state,
                               recent_security_check=get_recent_security_check()))

    elif request.method == 'GET':
        return render_template('login.html',
                               not_logged=not_logged,
                               login_error=login_error,
                               login_exception=login_exception,
                               register_successful=register_successful,
                               delete_success=delete_success,
                               delete_exception=delete_exception,
                               account_deleted=account_deleted,
                               form=form)
    else:
        return render_template('login.html', login_error=True, form=form)


@server.route('/manage/', methods=['GET', 'POST'])
def manage():
    logged_user = session.get('user')

    already_registered = request.args.get('already_registered')
    add_error = request.args.get('add_error')
    add_success = request.args.get('add_success')
    if logged_user != None:
        websites = get_registered_websites(logged_user)
        return render_template('manage_websites.html',
                               websites=websites,
                               already_registered=already_registered,
                               add_error=add_error,
                               add_success=add_success,
                               server_state=server_state,
                               recent_security_check=get_recent_security_check())
    return redirect(url_for('login', login_error=True))


@server.route('/register/', methods=['GET', 'POST'])
def register():
    form = register_form.RegisterForm()

    if request.method == 'POST':

        if not form.validate():
            return render_template('register.html', form=form)

        username = request.form['username']
        password = request.form['password']

        password = sha256_crypt.encrypt(password)
        try:
            query = User.query.filter_by(username=username).all()

            if query != []:
                return render_template('register.html',
                                        register_error=True,
                                       form=form)
            else:
                date = datetime.now()

                user = User(username=username, password=password, joined_at=local_dt_string(date))
                db.session.add(user)
                db.session.commit()
                register_user_json(user.id)

                return redirect(url_for('login',
                                        register_successful=True))
        except Exception as e:
            print(e)
            return render_template('register.html',
                                   register_exception=True,
                                   form=form)
    else:
        return render_template('register.html', form=form)


@server.route('/logout')
def logout():
    session['user'] = None
    return redirect(url_for('login'))


@server.route('/add_website/', methods=['GET', 'POST'])
def add_website():
    logged_user = session.get('user')
    form = website_form.WebsiteForm()

    if request.method == 'POST' and logged_user != None:

        if not form.validate():
            return render_template('add_website.html', form=form, server_state=server_state)

        url = request.form.get('url')
        url = re.match(
            '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)*(?P<host>((\w+\.)?\w+\.\w+|))(\/[a-z]*)*?$',
            url).group('host')

        try:
            website = Website(url=url)
            add = user_add_website(website, url, session['user'])

            if add == 0:
                # se user_add_website() retornar 0, é pq o site já foi adicionado, entao n precisa colocar no queue de novo
                return redirect(url_for('manage', already_registered=True))

            q.enqueue(tasks.run_scan, website.url, timeout=900)
            scheduler.cron(
                cron_string='0 0 0 ? * * *',  # Repete o scan a cada dia
                func=tasks.run_scan,
                args=['http://' + url],
                repeat=None,
                queue_name='default')

            date = datetime.now()
            website.updated_at = local_dt_string(date)
            set_recent_security_check(local_dt_string(date))


            return redirect(url_for('manage', add_success=True))

        except Exception as e:
            print(e)
            return redirect(url_for('manage', add_error=True))

    if logged_user != None:
        return render_template('add_website.html',
                               form=form,
                               server_state=server_state,
                               recent_security_check=get_recent_security_check())
    else:
        return redirect(url_for('login', not_logged=True))


@server.route('/view_reports/')
def view_reports():
    if session.get('user') != None:
        reports = get_reports()
        return render_template('view_reports.html',
                               reports=reports,
                               server_state=server_state,
                               recent_security_check=get_recent_security_check())
    return redirect(url_for('login', not_logged=True))


@server.route('/account_details/')
def account_details():
    if session.get('user') != None:
        user = User.query.filter_by(id=session.get('user')).first()

        update_success = request.args.get('update_success')
        update_error = request.args.get('update_error')
        update_exception = request.args.get('update_exception')

        with open(json_users, 'r') as f:
            data = json.load(f)
            size = len(data[str(user.id)])

        return render_template('account_details.html',
                               username=user.username,
                               joined_at=user.joined_at,
                               n_registered_websites=size - 1,
                               update_success=update_success,
                               update_error=update_error,
                               update_exception=update_exception,
                               server_state=server_state,
                               recent_security_check=get_recent_security_check())
    return redirect(url_for('login', not_logged=True))


@server.route('/update_account/', methods=['POST'])
def update_account():
    if session.get('user') != None and request.method == 'POST':
        password = request.form.get('password')
        username = request.form.get('username')

        if password is None and username is None:
            return redirect(url_for('account_details',
                                    update_error=True,
                                    server_state=server_state,
                                    recent_security_check=get_recent_security_check()))

        try:
            user = User.query.filter_by(id=session.get('user')).first()
            if password:
                if len(password)>15 or len(password)<5:
                    return redirect(url_for('account_details', update_error=True,server_state=server_state,
                               recent_security_check=get_recent_security_check()))
                user.password = sha256_crypt.encrypt(password)
                db.session.commit()
                return redirect(url_for('account_details', update_success=True,server_state=server_state,
                               recent_security_check=get_recent_security_check()))
            elif username:
                if len(username)>15 or len(username)<5:
                    return redirect(url_for('account_details', update_error=True,server_state=server_state,
                               recent_security_check=get_recent_security_check()))
                user.username = username
                db.session.commit()
                return redirect(url_for('account_details', update_success=True,server_state=server_state,
                               recent_security_check=get_recent_security_check()))

            return redirect(url_for('account_details', update_error=True,server_state=server_state,
                               recent_security_check=get_recent_security_check()))
        except Exception as e:
            print(e)
            return redirect(url_for('account_details', update_exception=True,server_state=server_state,
                               recent_security_check=get_recent_security_check()))

    return redirect(url_for('login', not_logged=True))


@server.route('/delete_account/')
def delete_account():
    if session.get('user') != None:
        try:
            User.query.filter_by(id=session.get('user')).delete()
            db.session.commit()
            delete_user_json(session.get('user'))
            session['user'] = None
        except Exception as e:
            print('Exception: ')
            print(e)
            return redirect(url_for('login', delete_exception=True))
        return redirect(url_for('login', account_deleted=True))
    return redirect(url_for('login', not_logged=True))


def get_registered_websites(id):
    user = User.query.get(id)
    json_data = open(json_users, 'r+')
    registered_websites = json.load(json_data)
    registered_websites = registered_websites[str(user.id)]
    size = len(registered_websites)
    list = [registered_websites.get(str(i)) for i in range(size)]

    print(registered_websites)
    json_data.close()

    websites = Website.query.all()
    get_websites = [
        [website.id, website.url, website.updated_at, 'http' + website.url.replace('.', '').replace(':', '')] for
        website in websites if website.url in list]

    return get_websites


def get_reports():
    websites = Website.query.all()
    return [[website.id, website.url, website.updated_at, website.url.replace('.', '')] for website in websites]


def user_add_website(website, url, logged_user):
    if Website.query.filter_by(url=url).all() == []:
        db.session.add(website)
        db.session.commit()
        # register_user_json(website, json_websites)
    else:
        return 0
    user = User.query.get(logged_user)
    return add_website_json(user.id, website)


def delete_user_json(id):
    with open(json_users, 'r') as f:
        data = json.load(f)
        data.pop(str(id))
    with open(json_users, 'w') as f:
        json.dump(data, f, indent=4)


def register_user_json(id):
    with open(json_users, 'r') as f:
        data = json.load(f)
        data.update({str(id): {'0': 'default'}})
    with open(json_users, 'w') as f:
        json.dump(data, f, indent=4)

def get_recent_security_check():
    with open(json_server, 'r') as f:
        data = json.load(f)
    return data['recent_security_check']

def set_recent_security_check(str_date):
    with open(json_server, 'r') as f:
        data = json.load(f)
        data.update({'recent_security_check': str_date})
    with open(json_server, 'w') as f:
        json.dump(data, f, indent=4)

def add_website_json(id, website):
    with open(json_users, 'r') as f:
        data = json.load(f)
        size = len(data[str(id)])
    with open(json_users, 'w') as f:
        registered_urls = [data[str(id)][str(i)] for i in range(size)]
        if website.url not in registered_urls:
            data[str(id)].update({str(size): website.url})
            json.dump(data, f, indent=4)
            return 1
        json.dump(data, f, indent=4)
        return 0

def local_dt_string(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt).strftime('%d-%m-%Y %H:%M')


if __name__ == '__main__':
    server.run(debug=True, port=8080)
