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

def get_or_create_address(conn, zip_code, address):
    cursor = conn.cursor()
    conn.execute("BEGIN IMMEDIATE")
    cursor.execute(
        "SELECT address_id FROM Address WHERE zipcode = ? AND address = ?",
        (zip_code, address),
    )
    existing_address = cursor.fetchone()
    if existing_address is not None:
        conn.commit()
        return existing_address[0]

    cursor.execute("SELECT COALESCE(MAX(CAST(address_id AS INTEGER)), 0) + 1 FROM Address")
    address_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO Address (address_id, zipcode, address) VALUES (?, ?, ?)",
        (address_id, zip_code, address),
    )
    conn.commit()
    return address_id

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
            result = "Registration Failed! Username already exist."
            return render_template('registerBuyer.html', result = result)
            # return render_template('register-buyer-with-user-alert.html')

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

        address_id = get_or_create_address(conn, zip_code, address)
        print("New address ID: ", address_id)

        # Add the new user to Buyers
        cursor.execute(f"INSERT INTO Buyers (email, business_name, buyer_address_id) VALUES ('{username}', '{business_name}', '{address_id}')")  # add username into Users and Buyers tables
        conn.commit()

        conn.close()
        return render_template('buyerRegSuccess.html')
    else:
        conn.close()
        result = "Registration Failed! Passwords not match."
        return render_template('registerBuyer.html', result)


@database.route('/buyerRegSuccess', methods = ['Get', 'Post'])
def buyerRegSuccess():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor

    render_template('buyerRegSuccess.html')





# @database.route('/register-seller', methods = ['GET', 'POST'])
# def register_seller():
#     db_file = 'nittanybusiness.db'
#     conn = sqlite3.connect(db_file)
#     cursor = conn.cursor()

#     conn.close()
#     return render_template('register-seller.html')


@database.route('/registerSeller', methods = ['GET', 'POST'])
def registerSeller():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    conn.close()
    return render_template('registerSeller.html')

@database.route('/process-seller-registration', methods = ['POST'])
def process_seller_registration():
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
            result = "Registration Failed! Username already exist."
            return render_template('registerSeller.html', result = result)
            # return render_template('register-buyer-with-user-alert.html')

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
        bankroutingnumber = request.form['bank-routing-number']
        bankaccountnumber = request.form['bank-account-number']

        # Check if the provided zip code already exists
        cursor.execute(f"SELECT COUNT(*) FROM Zipcode_Info WHERE zipcode = '{zip_code}'")
        rows = cursor.fetchall()
        if rows[0][0] == 0: # zipcode doesn't exist
            # Add the new zipcode to Zipcode
            cursor.execute(f"INSERT INTO Zipcode_Info (zipcode, city, state) VALUES ('{zip_code}', '{city}', '{state}')")  # add address to table
            conn.commit()

        address_id = get_or_create_address(conn, zip_code, address)
        print("New address ID: ", address_id)

        # Add the new user to Buyers
        cursor.execute(f"INSERT INTO Sellers (email, business_name, Business_Address_ID, bank_routing_number, bank_account_number) VALUES ('{username}', '{business_name}', '{address_id}','{bankroutingnumber}','{bankaccountnumber}')")  # add username into Users and Buyers tables
        conn.commit()

        conn.close()
        return render_template('sellerRegSuccess.html')
    else:
        conn.close()
        result = "Registration Failed! Passwords not match."
        return render_template('registerSeller.html', result = result)

@database.route('/SellerRegSuccess', methods = ['Get', 'Post'])
def SellerRegSuccess():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    render_template('SellerRegSuccess.html')

@database.route('/seller', methods = ['Get', 'Post'])
def renderseller():
    return render_template('seller.html')

# The above section is user registration
# From here on, the code focuses on app functionality
# Creating the main functionality of the website and so on
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# --------------------------------------------------------------- 
# --------------------------------------------------------------- 
# ---------------------------------------------------------------
# --------------------------------------------------------------- 
# We will first focus on the buyers

@database.route('/edit-buyer-info', methods = ['Get', 'Post'])
def edit_buyer_information():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    result = False
    address_id = False
    bus_name = False
    address = False
    city = False
    state = False
    zipcode = False
    cursor.execute("SELECT * FROM Buyer WHERE email = ?", (current_user,))
    rows = cursor.fetchone()
    if rows:
        address_id = rows[2]
        bus_name = rows[1]

        cursor.execute("SELECT * FROM Address WHERE address_id = ?", (address_id,) )
        addy_row = cursor.fetchone()

        if addy_row:
            address = addy_row[2]
            city = addy_row[3]
            state = addy_row[4]
            zipcode = addy_row[1]

            result = [bus_name, address, city, state, zipcode]

    # Add in preview of information prior to change
    # Only display the relevant info -- the business name and address


    return render_template('edit-buyer-info.html', result = result)

@database.route('/Update-Buyer-Information', methods = ["Get", "Post"])
def Update_Buyer_Information():
    # The only information that users will be able to edit here will be:
    # Business Name, Address, City, State, 
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    user = current_user
    business_name = False
    Address = False
    City = False
    State = False
    Zipcode = False

    if request.form.get("business-name"):
        business_name = request.form.get("business-name")

    if request.form.get("address"):
        Address = request.form.get("address")

    if request.form.get("city"):
        City = request.form.get("city")
    
    if request.form.get("state"):
        State = request.form.get("state")
    
    if request.form.get("zipcode"):
        Zipcode = request.form.get("zipcode")

    # cursor.execute(f"INSERT INTO Buyer (email, password) VALUES ('{username}', '{hashed_password}')") # add username into Users and Buyers tables
    cursor.execute("SELECT * FROM Buyers WHERE email = ?", (user,))
    rows = cursor.fetchall()
    row = rows[0]
    Address_id = row[2]

    
    # Consider making two forms 
    # so we know whether we are updating the
    # address or business name 
    if business_name:
        cursor.execute("UPDATE Buyers SET business_name = ? WHERE email = ?", (business_name, current_user,))
        conn.commit()
    if Address:

        # Update the address
        # CONSIDER ALL EDGE CASES
        if City:
            if State:
                if Zipcode:
                    cursor.execute("UPDATE Address SET zipcode = ?,address = ?,city = ?,state = ?",(Zipcode,Address,City,State,))
                    conn.commit()
                else:
                    cursor.execute("UPDATE Address SET address = ?,city = ?,state = ?",(Address,City,State,))
                    conn.commit()
            else:
                cursor.execute("UPDATE Address SET zipcode = ?,address = ?,city = ?",(Zipcode,Address,City,))
                conn.commit()
        else:
            cursor.execute("UPDATE Address SET zipcode = ?,address = ?,city = ?,state = ?",(Zipcode,Address,City,State,))
            conn.commit()

    return render_template("buyerinfoupdated.html")


@database.route('/create-product', methods = ['Get', 'Post'])
def product_creation():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()


    return render_template('product_creation.html')

@database.route('/list-product', methods = ['Get', 'Post'])
def listproduct():

    db_file = 'database.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    Seller_email = current_user
    category = request.form["Category"]
    company_name = request.form["Lister/Company"]
    product_name = request.form['Product Name']
    product_Description = request.form['Product Description']
    quantity = request.form['Quantity']
    price = request.form['Price']
    status = True

    # Create listing ID
    listing_ID = str(random.randint(100000,999999))
    cursor.execute("SELECT COUNT(*) FROM Products WHERE Listing_ID = ?", (listing_ID,))
    rows = cursor.fetchall()
    # print(rows)
    cursor.execute("INSERT INTO Products values (?,?,?,?,?,?,?,?,?)",
                    (Seller_email, listing_ID, category, company_name, product_name, product_Description, quantity, price, status))
    conn.commit()

    return render_template('product_created_successfully.html')

if __name__=="__main__":
    #app.run(host='0.0.0.0', port=8080)
    database.run()
    main()
