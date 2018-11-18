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

#http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#broker-redis

# CONFIG SET dir /mnt/d/Users/Franco/Documents/PI_2/redis
# CONFIG SET dbfilename redis_db.rdb

#Redis:
#   cd pro diretorio do projeto/redis
#   redis-server
#RQ:
#   cd pro diretorio do projeto/src
#   rq worker
#RQ-Scheduler:
#   cd pro diretorio do projeto/src
#   rqscheduler
#Flask:
#   cd pro diretorio do projeto/src
#   python3 run_project.py

import os
import json
import re
import subprocess
import requests
from datetime import datetime

from flask import Flask
from flask import request
from flask import session
from flask import redirect
from flask import render_template
from flask import url_for
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy #banco de dados

from passlib.hash import sha256_crypt #hashing de senhas

from reports import reports #Blueprint pra acessar os reports como templates

from rq import Queue, Connection #task queueing
from redis import Redis #comunicação com rq
from rq_scheduler import scheduler #scheduler com cron pro rq

import tasks #.py de tasks pra mandar pro rq

#-------------------------------------------------------------------------------------------------------------------------
#TODO: Colocar restrições para os inputs de registro de usuário e para atualização de username e senha
#TODO: Mudar os campos de registro de sites no add_website.html
#TODO: Diminuir a altura das barras da lista de sites adicionados
#TODO: Ajustar a página da lista de sites pra nova db e os atributos
#TODO: Ajustar o datetime de scan pro Brasil
#TODO: Traduzir as mensagens e conteúdos do site para português
#-------------------------------------------------------------------------------------------------------------------------

redis_conn = Redis()
q = Queue(connection=redis_conn)

server = Flask(__name__)
server.secret_key = os.urandom(24)
server.register_blueprint(reports) #Adiciona o blueprint de exibição dos reports no projeto

server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

#path dos json
json_users = './database/users.json'
json_websites = './database/websites.json'

db = SQLAlchemy(server)

#Tabelas do SQL
class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(40))
    password = db.Column('password', db.String(30))
    joined_at = db.Column('joined_at', db.String(30))
    registered_websites_path = db.Column('registered_websites_path', db.String(50))

class Website(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    url = db.Column('url', db.String(400))
    updated_at = db.Column('updated_at', db.String(10))

db.create_all() #Cria as tabelas

@server.route('/')
def index():
    return render_template('index.html')

@server.route('/login/')
def login():
    not_logged = request.args.get('not_logged')
    login_error = request.args.get('login_error')
    login_exception = request.args.get('login_exception')
    register_successful = request.args.get('register_successful')
    delete_success = request.args.get('delete_success')
    delete_exception = request.args.get('delete_exception')
    account_deleted = request.args.get('account_deleted')

    return render_template('login.html',
                           not_logged=not_logged,
                           login_error=login_error,
                           login_exception=login_exception,
                           register_successful=register_successful,
                           delete_success=delete_success,
                           delete_exception=delete_exception,
                           account_deleted=account_deleted)

@server.route('/logged/', methods=['GET', 'POST'])
def logged():
    logged_user = session.get('user')
    websites = []

    print(logged_user)

    if request.method == 'POST' and request.form.get('type') == None and logged_user == None:

        session['user'] = None
        username = request.form['username']
        password = request.form['password']

        try:
            user = User.query.filter_by(username=username).first()
            print(user.id)
            if user == []:
                return redirect(url_for('login', login_error=True))
            else:
                if sha256_crypt.verify(password, user.password):
                    session['user'] = user.id

                    return redirect(url_for('manage'))
                else:
                    return redirect(url_for('login', login_error=True))
        except Exception as e:
            print(e)
            return redirect(url_for('login', login_error=True))

    elif logged_user != None:
        return redirect(url_for('manage'))

    elif request.method == 'GET':
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login', login_error=True))

@server.route('/manage/', methods=['GET', 'POST'])
def manage():
    logged_user = session.get('user')

    already_registered = request.args.get('already_registered')
    add_error = request.args.get('add_error')
    ip = request.args.get('ip')
    if logged_user != None:
        websites = get_registered_websites(logged_user)
        return render_template('manage_websites.html',
                               websites=websites,
                               already_registered=already_registered,
                               add_error=add_error,
                               ip=ip)
    return redirect(url_for('login', login_error=True))


@server.route('/register/')
def register():
    register_error = request.args.get('register_error')
    register_exception = request.args.get('register_exception')
    return render_template('register.html',
                           register_error=register_error,
                           register_exception=register_exception)

@server.route('/logout')
def logout():
    session['user'] = None
    return redirect(url_for('login'))

@server.route('/add/')
def add():
    logged_user = session.get('user')
    print(logged_user)

    ip_error = request.args.get('ip_error')
    if logged_user != None:
        return render_template('add_website.html', ip_error=ip_error)
    else:
        return redirect(url_for('login', not_logged=True))

@server.route('/added/', methods=['GET','POST'])
def added():
    logged_user = session.get('user')
    print(logged_user)
    if request.method == 'POST' and request.form.get('type') == 'add' and logged_user != None:

        #regex = '^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)*(?P<host>((\w+\.)?\w+\.\w+|))(\/[a-z]*)*?$'############################################
        #url = re.match(regex, request.form.get('url')) ################################################################
        url = request.form.get('url') #######################################
        #if url != None:
        #    url = url.group('host')
        #else:
        #    return redirect(url_for('add', ip_error=True))

        try:
            website = Website(url=url)
            add = user_add_website(website, url, session['user'])

            if add == 0:
                # se user_add_website() retornar 0, é pq o site já foi adicionado, entao n precisa colocar pra escanear dnv
                return redirect(url_for('manage', already_registered=True))

            q.enqueue(tasks.run_scan, website.url, timeout=900)
            scheduler.cron(
                cron_string='0 0 0 ? * * *',  # Repete o scan a cada dia
                func=tasks.run_scan,
                args=['http://' + url],
                repeat=None,
                queue_name='default')

            website.updated_at = datetime.now().strftime('%d-%m-%Y %H:%M')

        except Exception as e:
            print(e)
            return redirect(url_for('manage', add_error=True))

    if logged_user != None:
        return redirect(url_for('manage', add_error='False'))
    else:
        return redirect(url_for('login', not_logged=True))

@server.route('/deu_boa/', methods=['GET', 'POST'])
def deu_boa():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username.replace(' ', '')) < 6 or len(password.replace(' ', '')) < 6:
            return render_template('error.html')

        password = sha256_crypt.encrypt(password)
        try:
            query = User.query.filter_by(username=username).all()

            if query != []:
                return redirect(url_for('register', register_error=True))
            else:
                user = User(username=username,password=password, joined_at=datetime.now().strftime('%d-%m-%Y %H:%M'))
                db.session.add(user)
                db.session.commit()
                register_user_json(user.id)

                return redirect(url_for('login', register_successful=True))
        except Exception as e:
            print(e)
            return redirect(url_for('register', register_exception=True))
    else:
        return redirect(url_for('login'))

@server.route('/add_website/')
def add_website():
    if session.get('user') != None:
        return render_template('add_website.html')
    return redirect(url_for('login', not_logged=True))

@server.route('/view_reports/')
def view_reports():
    if session.get('user') != None:
        reports = get_reports()
        return render_template('view_reports.html', reports=reports)
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

        return render_template('account_details.html', username=user.username,
                               joined_at=user.joined_at,
                               n_registered_websites=size-1,
                               update_success=update_success,
                               update_error=update_error,
                               update_exception=update_exception)
    return redirect(url_for('login', not_logged=True))

@server.route('/update_account/', methods=['POST'])
def update_account():
    if session.get('user') != None and request.method == 'POST':
        password = request.form.get('password')
        username = request.form.get('username')

        try:
            user = User.query.filter_by(id=session.get('user')).first()
            if password:
                user.password = sha256_crypt.encrypt(password)
                db.session.commit()
                return redirect(url_for('account_details', update_success=True))
            elif username:
                user.username = username
                db.session.commit()
                return redirect(url_for('account_details', update_success=True))

            return redirect(url_for('account_details', update_error=True))
        except Exception as e:
            print(e)
            return redirect(url_for('account_details', update_exception=True))

    return redirect(url_for('login', not_logged=True))

@server.route('/delete_account/')
def delete_account():
    if session.get('user') != None:
        try:
            User.query.filter_by(id=session.get('user')).delete()
            db.session.commit()
            delete_user_json(session.get('user'))
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
    get_websites = [[website.id, website.url, website.updated_at, 'http'+website.url.replace('.','').replace(':','')] for website in websites if website.url in list]

    return get_websites

def get_reports():
    websites = Website.query.all()
    return [[website.id, website.url, website.updated_at, website.url.replace('.','')] for website in websites]

def user_add_website(website, url, logged_user):
    if Website.query.filter_by(url=url).all() == []:
        db.session.add(website)
        db.session.commit()
        #register_user_json(website, json_websites)
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
        data.update({str(id):{'0':'default'}})
    with open(json_users, 'w') as f:
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

if __name__ == '__main__':
    server.run(debug=True, port=8080)
