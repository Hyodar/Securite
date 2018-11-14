import sqlite3
import os


def get_registered_websites(user):
    users = sqlite3.connect(os.path.abspath('database/database.db'))
    cursor = users.cursor()
    insert = (user,)
    query = cursor.execute("""
            SELECT NAME, URL, UPDATE_PERIOD, CAST(JULIANDAY()-JULIANDAY(DATE_UPDATED) AS INTEGER), ID_WEBSITE
            FROM WEBSITE
            WHERE USER_ID_USER=?;""", insert)
    websites = query.fetchall()
    users.close()

    return websites

def insert_website(name, url, update_period, user):
    users = sqlite3.connect(os.path.abspath('database/database.db'))
    cursor = users.cursor()

    insert = (name, url, update_period, user)
    query = cursor.execute("""
            INSERT INTO WEBSITE
            (NAME,URL,UPDATE_PERIOD,USER_ID_USER)
            VALUES(?,?,?,?);
            """, insert)

    users.commit()
    users.close()

def get_password(username):
    users = sqlite3.connect(os.path.abspath('database/database.db'))
    cursor = users.cursor()

    insert = (username,)

    query = cursor.execute("""
                SELECT PASSWORD, ID_USER FROM USER
                WHERE USERNAME=?;""", insert)
    selection = query.fetchall()
    users.close()
    return selection