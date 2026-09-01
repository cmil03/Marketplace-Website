from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import pandas as pd
import os
import hashlib
# import app
import database
import random
import sys
import datetime

database = Flask(__name__, template_folder='templates')

global current_user
current_user = None # stores the userID of the current logged-in user

global category
category = 'Root' # stores current category name

global logged_in
logged_in = False # tracks whether the user has logged in

global user_type
user_type = None # tracks role of logged in user

def hash(password):
    encrypted = hashlib.sha256(password.encode()).hexdigest()
    return encrypted

def main():
    pass

@database.route('/', methods = ['GET', 'POST'])
def index():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    print(logged_in)
    print(user_type)

    # Allows already authenticated users to return to the homepage
    if logged_in:
        if user_type == "Buyer":
            return render_template('buyer.html')
        elif user_type == "Seller":
            return render_template('seller.html')
        else:
            return render_template('helpdesk.html')

    conn.close()
    return render_template('login.html')

@database.route('/login', methods = ['GET', 'POST'])
def login():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    global current_user
    global logged_in
    global user_type

    username = request.form['userid']
    hashed_password = hash(request.form['password'])
    hashed_password = str(hashed_password)

    cursor.execute(f"SELECT COUNT(*) FROM Users WHERE email = '" + username + "' AND password = '" + hashed_password + "'")
    rows = cursor.fetchall()
    if rows[0][0] >= 1: # username and password are right
        current_user = username
        logged_in = True
        cursor.execute(f"SELECT COUNT(*) FROM Buyers WHERE email = '" + username + "'")
        rows = cursor.fetchall()
        if rows[0][0] >= 1: # User is a Buyer
            user_type = "Buyer"
            conn.close()
            return render_template("buyer.html") 
        cursor.execute(f"SELECT COUNT(*) FROM Sellers WHERE email = '" + username + "'")
        rows = cursor.fetchall()
        if rows[0][0] >= 1: # User is a Seller
            user_type = "Seller"
            conn.close()
            return render_template("seller.html") 
        cursor.execute(f"SELECT COUNT(*) FROM HelpDesk WHERE email = '" + username + "'")
        rows = cursor.fetchall()
        if rows[0][0] >= 1: # User is a HelpDesk
            user_type = "HelpDesk"
            cursor.execute(f"SELECT * FROM Requests LIMIT 30")
            rows = cursor.fetchall()
            conn.close()
            rows = pd.DataFrame(rows, columns=['Request ID', 'Sender Email', 'Helpdesk Staff Email', 'Request Type', 'Request Description', 'Request Status'])
            return render_template("helpdesk.html", query=rows.to_html())
    else: # username or password were wrong
        current_user = None
        conn.close()
        return render_template("failedindex.html")


@database.route('/registration', methods = ['GET', 'POST'])
def registration():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    return render_template('registration.html')










if __name__=="__main__":
    #app.run(host='0.0.0.0', port=8080)
    database.run()
    main()
