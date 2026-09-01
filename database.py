import sqlite3
import pandas as pd
import os
import hashlib


def create_tables(conn):
    # cursor = conn.cursor()

    conn.commit()

def hash(password):
    encrypted = hashlib.sha256(password.encode()).hexdigest()
    return encrypted

def truncate_dollar(value):
    value = value.replace(",", "")
    return value.replace("$", "")

def clean_string(value):
    return value.strip()

def cast_to_int(value):
    return int(value)

def populate_table_from_csv(conn, table_name, csv_file):
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        # Append the data into the table
        if table_name == 'Users':
            df['password'] = df['password'].apply(lambda x: hash(x))
        elif table_name == 'Product_Listings':
            df['Product_Price'] = df['Product_Price'].apply(lambda x: truncate_dollar(x))
            df['Product_Price'] = df['Product_Price'].apply(lambda x: clean_string(x))
            df['Product_Price'] = df['Product_Price'].apply(lambda x: cast_to_int(x))
        elif table_name == 'Categories':
            df['parent_category'] = df['parent_category'].apply(lambda x: clean_string(x))
            df['category_name'] = df['category_name'].apply(lambda x: clean_string(x))
        df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"Populated table {table_name} from {csv_file}.")
    else:
        print(f"CSV file {csv_file} for table {table_name} not found.")


def main():
    db_file = 'database.db'
    conn = sqlite3.connect(db_file)

    # Create all tables in the correct order
    create_tables(conn)
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Map of table names to expected CSV file names
    csv_files = {
        'Zipcode_Info': os.path.join(script_dir, 'Zipcode_Info.csv'),
        'Address': os.path.join(script_dir, 'Address.csv'),
        'Users': os.path.join(script_dir, 'Users.csv'),
        'Buyers': os.path.join(script_dir, 'Buyers.csv'),
        'Sellers': os.path.join(script_dir, 'Sellers.csv'),
        'Helpdesk': os.path.join(script_dir, 'Helpdesk.csv'),
        'Requests': os.path.join(script_dir, 'Requests.csv'),
        'Categories': os.path.join(script_dir, 'Categories.csv'),
        'Products': os.path.join(script_dir, 'Products.csv'),
        'Orders': os.path.join(script_dir, 'Orders.csv'),
        'Credit_Cards': os.path.join(script_dir, 'Credit_Cards.csv'),
        'Reviews': os.path.join(script_dir, 'Reviews.csv')
    } 
    # # Map of table names to expected CSV file names
    # csv_files = {
    #     'Zipcode_Info': 'Zipcode_Info.csv',
    #     'Address': 'Address.csv',
    #     'Users': 'Users.csv',
    #     'Buyers': 'Buyers.csv',
    #     'Sellers': 'Sellers.csv',
    #     'Helpdesk': 'Helpdesk.csv',
    #     'Requests': 'Requests.csv',
    #     'Categories': 'Categories.csv',
    #     'Products': 'Products.csv',
    #     'Orders': 'Orders.csv',
    #     'Credit_Cards': 'Credit_Cards.csv',
    #     'Reviews': 'Reviews.csv'
    # }

    # Populate tables respecting the foreign key dependencies
    for table in ['Zipcode_Info', 'Address', 'Users', 'Buyers', 'Sellers', 'Helpdesk', 'Requests', 'Credit_Cards', 'Categories', 'Products', 'Orders', 'Reviews']:
        populate_table_from_csv(conn, table, csv_files[table])

    # Verify population: display first ten rows of each table
    cursor = conn.cursor()
    for table in csv_files.keys():
        print(f"\nContents of table {table}:")
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        for i in range(len(rows)):
            print(rows[i])
            if i > 10:
                break

    conn.close()

if __name__ == '__main__':
    main()