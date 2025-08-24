# database.py
import sqlite3

def create_connection(db_file="liquor_store.db"):
    """ Create a database connection to the SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables():
    """ Create the tables needed for the application """
    conn = create_connection()
    if conn is not None:
        try:
            c = conn.cursor()

            # Product Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                size TEXT,
                purchase_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                category TEXT,
                gst_category TEXT NOT NULL,
                barcode1 TEXT UNIQUE,
                barcode2 TEXT,
                barcode3 TEXT,
                stock INTEGER DEFAULT 0,
                CONSTRAINT unique_product UNIQUE (name, size)
            )''')

            # Customer Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                area TEXT,
                city TEXT,
                state TEXT,
                pincode TEXT,
                mobile TEXT UNIQUE NOT NULL,
                email TEXT
            )''')

            # Vendor Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                address TEXT,
                area TEXT,
                city TEXT,
                state TEXT,
                pincode TEXT,
                mobile TEXT,
                email TEXT,
                gst_number TEXT UNIQUE
            )''')
            
            # Tax Config Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS tax_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_name TEXT NOT NULL UNIQUE,
                tax_value REAL NOT NULL,
                tax_type TEXT
            )''')

            # Purchase Order Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id INTEGER,
                purchase_date TEXT NOT NULL,
                invoice_number TEXT,
                bill_reference TEXT,
                total_amount REAL,
                total_gst REAL,
                total_tcs REAL DEFAULT 0,
                grand_total REAL,
                remarks TEXT,
                FOREIGN KEY (vendor_id) REFERENCES vendors (id)
            )''')

            # Purchase Order Items Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                rate REAL,
                gst_percent REAL,
                gst_amount REAL,
                amount REAL,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )''')

            # Bills Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_date TEXT NOT NULL,
                customer_name TEXT,
                pay_mode TEXT,
                remarks TEXT,
                sub_total REAL,
                total_gst REAL,
                total_tcs REAL,
                grand_total REAL
            )''')

            # Bill Items Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS bill_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                rate REAL,
                gst_percent REAL,
                gst_amount REAL,
                amount REAL,
                FOREIGN KEY (bill_id) REFERENCES bills (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )''')

            # Store Info Table
            c.execute('''
            CREATE TABLE IF NOT EXISTS store_info (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                vat_number TEXT NOT NULL
            )''')

            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    create_tables()
    print("Database and tables created successfully.")
