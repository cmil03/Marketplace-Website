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

@database.route('/registerBuyer', methods = ['GET', 'POST'])
def register_buyer():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    conn.close()
    return render_template('registerBuyer.html')

@database.route('/process-buyer-registration', methods = ['POST'])
def process_buyer_registration():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    hashed_password = hash(request.form['password'])
    hashed_password = str(hashed_password)       
 
    hashed_password2 = hash(request.form['confirm-password'])
    hashed_password2 = str(hashed_password2)       
 
    if hashed_password == hashed_password2:
        # Must update Users, Buyers, Address, and ZipCode tables
        # Query Users to find if the provided username already exists
        username = request.form['userid'] 
        cursor.execute(f"SELECT COUNT(*) FROM Users WHERE email = '" + username + "'")
        rows = cursor.fetchall()
        if rows[0][0] >= 1: # username already exists
            conn.close()
            return render_template('register-buyer-with-user-alert.html')

        cursor.execute(f"INSERT INTO Users (email, password) VALUES ('{username}', '{hashed_password}')") # add username into Users and Buyers tables
        conn.commit()

        # Load rest of fields
        business_name = request.form['business-name']
        # street_num = request.form['street-num']
        # street_name = request.form['street-name']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zipcode']

        # Check if the provided zip code already exists
        cursor.execute(f"SELECT COUNT(*) FROM Zipcode_Info WHERE zipcode = '{zip_code}'")
        rows = cursor.fetchall()
        if rows[0][0] == 0: # zipcode doesn't exist
            # Add the new zipcode to Zipcode
            cursor.execute(f"INSERT INTO Zipcode_Info (zipcode, city, state) VALUES ('{zip_code}', '{city}', '{state}')")  # add address to table
            conn.commit()

        # Check if the provided address is already in Address
        cursor.execute(f"SELECT COUNT(*) FROM Address WHERE zipcode = '{zip_code}' AND address = '{address}'")
        rows = cursor.fetchall()
        if rows[0][0] >= 1:  # address already exists
            cursor.execute(f"SELECT address_ID FROM Address WHERE zipcode = '{zip_code}' AND address = '{address}'")
            rows = cursor.fetchall()
            address_id = rows[0][0]
        else: # generate random address id
            # id's must be unique
            address_id = random.randint(0, 100000000)
            # Add the new address to Address if it does not already exist
            cursor.execute(f"INSERT INTO Address (address_ID, zipcode, address) VALUES ('{address_id}', '{zip_code}', '{address}')")  # add address to table
            conn.commit()
        print("New address ID: ", address_id)

        # Add the new user to Buyers
        cursor.execute(f"INSERT INTO Buyers (email, business_name, buyer_address_id) VALUES ('{username}', '{business_name}', '{address_id}')")  # add username into Users and Buyers tables
        conn.commit()

        conn.close()
        return render_template('buyerRegSuccess.html')
    else:
        conn.close()
        return render_template('register-buyer-with-password-alert.html')


@database.route('/buyerRegSuccess', methods = ['Get', 'Post'])
def buyerRegSuccess():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor

    render_template('buyerRegSuccess.html')

if __name__=="__main__":
    #app.run(host='0.0.0.0', port=8080)
    database.run()
    main()
