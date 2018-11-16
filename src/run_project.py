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

#http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html#broker-redis

# CONFIG SET dir /mnt/d/Users/Franco/Documents/PI_2/redis
# CONFIG SET dbfilename redis_db.rdb


# Passos pra rodar o sistema do celery:
#   Console debian:
#       cd /mnt/d/Users/Franco/Documents/PI_2
#       sudo redis-server

#   Console windows:
#       d:
#       cd Users\Franco\Documents\PI_2\src
#       celery -A run_project.celery worker --loglevel=info
#

import os
import json

from flask import Flask
from flask import request
from flask import session
from flask import redirect
from flask import render_template
from flask import url_for

from celery import task

from flask_celery import make_celery

from flask_sqlalchemy import SQLAlchemy

from passlib.hash import sha256_crypt


server = Flask(__name__)
server.secret_key = os.urandom(24)

os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1') #Pra rodar no windows

server.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
server.config['CELERY_BACKEND'] = 'db+sqlite:///database/database.db'
server.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.db'
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
#server.config['CELERY_TRACK_STARTED'] = True
server.config['CELERY_TASK_EVENTS'] = True

json_users = './database/users.json'
json_websites = './database/websites.json'

celery = make_celery(server)
db = SQLAlchemy(server)

#TODO: Ajustar a página da lista de sites pra nova db e os atributos

class Result(db.Model):
    id = db.Column('id_result', db.Integer, primary_key=True)
    result_path = db.Column('result_path', db.String(100))

class User(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(40))
    password = db.Column('password', db.String(30))
    registered_websites_path = db.Column('registered_websites_path', db.String(50))

class Website(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    url = db.Column('url', db.String(400))
    updated_at = db.Column('updated_at', db.String(10))
    report_path = db.Column('report_path', db.String(500))

db.create_all()


#huey = SqliteHuey('securite', filename='/database/database.db')


# @huey.task(name='run_scan')
# def run_scan():
#     subprocess.run("")
#     #rodar o scan do wapiti aqui
#     #pra rodar o scan é só chamar a função res = add.apply_async((x, y)), por exemplo
#     #depois coleta o resultado retval = add.AsyncResult(task_id).get(timeout=1.0)
#     time.sleep(600)
#     return None #

@celery.task(name='run_scan')
def run_scan(url):
    from celery import current_task
    with server.app_context():
        print(url)
        return "Scanned!"
    return "aaaaa"

@server.route('/')
def index():
    return render_template('index.html')

@server.route('/login/')
def login():
    session['user'] = None
    return render_template('login.html')

@server.route('/logged/', methods=['GET', 'POST'])
def logged():
    logged_user = session.get('user') or None
    websites = []
    print("aaaaaaaaaa")
    print(logged_user)

    if request.method == 'POST' and request.form.get('type') == None and logged_user == None:

        session['user'] = None
        username = request.form['username']
        password = request.form['password']

        try:
            user = User.query.filter_by(username=username).first()

            if user == []:
                return render_template('loginfailed.html')
            else:
                if sha256_crypt.verify(password, user.password):
                    session['user'] = user.id
                    print('bbbbbbbbbb')

                    websites = get_registered_websites(session['user'])

                    return render_template('manage_websites.html', websites=websites)
                else:
                    return render_template('loginfailed.html')
        except Exception as e:
            print(e)
            return render_template('loginfailed.html')

    elif logged_user != None:
        websites = get_registered_websites(logged_user)

        return render_template('manage_websites.html', websites=websites)

    elif request.method == 'GET':
        return redirect(url_for('login'))
    else:
        return render_template('loginfailed.html')

@server.route('/register/')
def register():
    return render_template('register.html')

@server.route('/logout')
def logout():
    session['user'] = None
    return redirect(url_for('login'))

@server.route('/add/')
def add():
    run_scan.delay('a') ########################
    logged_user = session.get('user')
    if logged_user != None:
        return render_template('add_website.html')
    else:
        return redirect(url_for('login'))

@server.route('/added/', methods=['GET','POST'])
def added():
    logged_user = session.get('user')
    print(request.method)
    print(request.form.get('type'))
    print(logged_user)
    if request.method == 'POST' and request.form.get('type') == 'add' and logged_user != None:
        if request.form['url'].count('//') == 0:
            url = request.form['url'].split('/')[0]
        else:
            try:
                url = request.form['url'].split('/')[3]
            except:
                url = request.form['url'].split('/')[2]

        try:
            print('cccccccccccc')
            website = Website(url=url)
            user_add_website(website, url, session['user'])

            #TODO: colocar flash
            print('dddddddddddd')

        except Exception as e:
            print(e)
            return redirect(url_for('logged'))



    if logged_user != None:
        return redirect(url_for('logged'))
    else:
        return redirect(url_for('login'))

@server.route('/deu_boa/', methods=['GET', 'POST'])
def deu_boa():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username.replace(' ', '')) < 6 or len(password.replace(' ', '')) < 6:
            return render_template('error.html')
        #TODO: colocar flash

        password = sha256_crypt.encrypt(password)
        try:
            query = User.query.filter_by(username=username).all()
            print(query)

            if query != []:
                return render_template('registerunsuccessful.html')
            else:
                user = User(username=username,password=password)
                db.session.add(user)
                db.session.commit()
                register_user_json(user, json_users)

                return render_template('deu_boa.html')
        except Exception as e:
            print(e)
            return render_template('error.html')
    else:
        return redirect(url_for('/login/'))

@server.route('/add_website/')
def add_website():
    return render_template('add_website.html')


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
    get_websites = [[website.id, website.url, website.updated_at] for website in websites if website.url in list]

    return get_websites

def user_add_website(website, url, logged_user):
    if Website.query.filter_by(url=url).all() == []:
        db.session.add(website)
        db.session.commit()
        #register_user_json(website, json_websites)
    user = User.query.get(logged_user)
    add_website_json(user.id, website)


def register_user_json(user, path):
    with open(json_users, 'r') as f:
        data = json.load(f)
        data.update({str(user.id):{'0':'default'}})
    with open(json_users, 'w') as f:
        json.dump(data, f, indent=4)

def add_website_json(id, website):
    with open(json_users, 'r') as f:
        data = json.load(f)
        size = len(data[str(id)])
    with open(json_users, 'w') as f:
        data[str(id)].update({str(size): website.url})
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    server.run(debug=True, port=8080)
