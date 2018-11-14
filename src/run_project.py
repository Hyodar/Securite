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


import os
import subprocess
import sqlite3

from flask import Flask
from flask import request
from flask import session
from flask import redirect
from flask import render_template
from flask import url_for

from passlib.hash import sha256_crypt

import db

server = Flask(__name__)
server.secret_key = os.urandom(24)

users = sqlite3.connect(os.path.abspath('database/database.db'))
cursor = users.cursor()

# cursor.execute("""
# BEGIN TRANSACTION;
# """)
# cursor.execute("ALTER TABLE WEBSITE RENAME TO TEMP_WEBSITE;")
#
# cursor.execute("""CREATE TABLE WEBSITE(
#      ID_WEBSITE INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
#      NAME TEXT NOT NULL,
#      URL TEXT NOT NULL,
#      UPDATE_PERIOD INT NOT NULL,
#      DATE_UPDATED TEXT,
#      USER_ID_USER INTEGER NOT NULL,
#      FOREIGN KEY(USER_ID_USER) REFERENCES USER(ID_USER)
#      );
#  """)
# cursor.execute("""
# INSERT INTO WEBSITE
# SELECT
# ID_WEBSITE, NAME, URL, UPDATE_PERIOD, DATE_UPDATED, USER_ID_USER
# FROM
# TEMP_WEBSITE;
# """)
# cursor.execute("DROP TABLE TEMP_WEBSITE;")
#
# cursor.execute("COMMIT;")
# #Inicializa o w3af no shell do servidor - usar só na vm de linux
# start_w3af = '''
#             cd
#             cd /w3af;
#             ./w3af_console'''
# try:
#     process = subprocess.run(start_w3af, check=True) #Inicializa o console do w3af
# except Exception as e:
#     print("/-------------------w3af initialization error-------------------/")
#     print(e)

# cursor.execute('''
# CREATE TABLE USER(
#     ID_USER INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
#     USERNAME TEXT NOT NULL,
#     PASSWORD TEXT NOT NULL
#     );
# ''')
# cursor.execute('''
# CREATE TABLE WEBSITE(
#     ID_WEBSITE INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
#     NAME TEXT NOT NULL,
#     URL TEXT NOT NULL,
#     UPDATE_PERIOD INT NOT NULL,
#     DATE_UPDATED TEXT,
#     USER_ID_USER INTEGER NOT NULL,
#     FOREIGN KEY(USER_ID_USER) REFERENCES USER(ID_USER)
#     );
# ''')

#cursor.execute("""
#CREATE TABLE USERS(
#        username TEXT NOT NULL,
#        password TEXT NOT NULL,
#        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
#);
#""")


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
            selection = db.get_password(username)

            if selection == []:
                return render_template('loginfailed.html')
            else:
                if sha256_crypt.verify(password, selection[0][0]):
                    session['user'] = selection[0][1]

                    websites = db.get_registered_websites(session['user'])

                    return render_template('manage_websites.html', websites=websites)
                else:
                    return render_template('loginfailed.html')
        except Exception as e:
            print(e)
            users.close()
            return render_template('loginfailed.html')

    elif logged_user != None:
        websites = db.get_registered_websites(logged_user)

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
    logged_user = session.get('user') or None
    if logged_user != None:
        return render_template('add_website.html')
    else:
        return redirect(url_for('login'))

@server.route('/added/')
def added():
    logged_user = session.get('user') or None
    if request.method == 'POST' and request.form.get('type') == 'add':
        name = request.form['name']
        url = request.form['url']
        update_period = request.form['update_period']

        try:
            db.insert_website(name, url, update_period, session['user'])
        except Exception as e:
            return redirect(url_for('logged'))

    if logged_user != None:
        return redirect(url_for('/logged/'))
    else:
        return redirect(url_for('/login/'))

@server.route('/deu_boa/', methods=['GET', 'POST'])
def deu_boa():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        insert = (username, password)

        users = sqlite3.connect(os.path.abspath('database/database.db'))
        cursor = users.cursor()

        if len(username.replace(' ', '')) < 6 or len(password.replace(' ', '')) < 6:
            return render_template('error.html')

        password = sha256_crypt.encrypt(password)

        try:
            insert = (username,)
            query = cursor.execute("""
            SELECT * FROM USER
            WHERE USERNAME=?""", insert)
            selection = query.fetchall()
            print(selection)
            users.close()
            if selection != []:
                return render_template('registerunsuccessful.html')
            else:
                users = sqlite3.connect(os.path.abspath('database/database.db'))
                cursor = users.cursor()
                insert = (username, password)
                cursor.execute("""
                INSERT INTO USER(USERNAME, PASSWORD)
                VALUES(?,?)""", insert)
                users.commit()
                users.close()

                return render_template('deu_boa.html')
        except:
            return render_template('error.html')

@server.route('/add_website/')
def add_website():
    return render_template('add_website.html')

if __name__ == '__main__':
    server.run(debug=True, port=8080)
