# db_functions.py
import sqlite3
import pandas as pd
import numpy as np

DB_FILE = "liquor_store.db"

def get_connection():
    return sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)

def execute_query(query, params=(), fetch=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute(query, params)
        conn.commit()
        if fetch == 'one':
            return cursor.fetchone()
        if fetch == 'all':
            return cursor.fetchall()
        return cursor.lastrowid

# --- Product, Customer, Vendor, Tax Functions (No Changes) ---
def add_product(name, p_type, size, purchase_price, selling_price, category, gst_category):
    query = "INSERT INTO products (name, type, size, purchase_price, selling_price, category, gst_category) VALUES (?, ?, ?, ?, ?, ?, ?)"
    try:
        execute_query(query, (name, p_type, size, purchase_price, selling_price, category, gst_category)); return True, "Product added."
    except sqlite3.IntegrityError as e: return False, f"Error: {e}"
def update_product(pid, name, p_type, size, purchase_price, selling_price, category, gst_category):
    query = "UPDATE products SET name=?, type=?, size=?, purchase_price=?, selling_price=?, category=?, gst_category=? WHERE id=?"
    try:
        execute_query(query, (name, p_type, size, purchase_price, selling_price, category, gst_category, pid)); return True, "Product updated."
    except sqlite3.IntegrityError as e: return False, f"Error: {e}"
def delete_entity(table_name, entity_id):
    query = f"DELETE FROM {table_name} WHERE id=?"
    try:
        execute_query(query, (entity_id,)); return True, f"Record deleted."
    except sqlite3.IntegrityError as e: return False, f"Cannot delete. Record is in use."
    except Exception as e: return False, f"Error: {e}"
def get_products(): return pd.read_sql_query("SELECT id, name, type, size, purchase_price, selling_price, category, gst_category, stock FROM products", get_connection(), index_col='id')
def update_product_stock(product_id, quantity_change): execute_query("UPDATE products SET stock = stock + ? WHERE id = ?", (quantity_change, product_id))
def add_customer(name, address, area, city, state, pincode, mobile, email):
    query = "INSERT INTO customers (name, address, area, city, state, pincode, mobile, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    try:
        execute_query(query, (name, address, area, city, state, pincode, mobile, email)); return True, "Customer added."
    except sqlite3.IntegrityError: return False, "Error: Mobile number exists."
def update_customer(cid, name, address, area, city, state, pincode, mobile, email):
    query = "UPDATE customers SET name=?, address=?, area=?, city=?, state=?, pincode=?, mobile=?, email=? WHERE id=?"
    try:
        execute_query(query, (name, address, area, city, state, pincode, mobile, email, cid)); return True, "Customer updated."
    except sqlite3.IntegrityError: return False, "Error: Mobile number may already exist."

def get_customers(): return pd.read_sql_query("SELECT * FROM customers", get_connection(), index_col='id')
def add_vendor(name, address, area, city, state, pincode, mobile, email, gst_number):
    query = "INSERT INTO vendors (name, address, area, city, state, pincode, mobile, email, gst_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    try:
        execute_query(query, (name, address, area, city, state, pincode, mobile, email, gst_number)); return True, "Vendor added."
    except sqlite3.IntegrityError: return False, "Error: Name or GST# exists."
# Add to db_functions.py
def update_vendor(vid, name, address, area, city, state, pincode, mobile, email, gst_number):
    query = "UPDATE vendors SET name=?, address=?, area=?, city=?, state=?, pincode=?, mobile=?, email=?, gst_number=? WHERE id=?"
    try:
        execute_query(query, (name, address, area, city, state, pincode, mobile, email, gst_number, vid))
        return True, "Vendor updated."
    except sqlite3.IntegrityError:
        return False, "Error: Name or GST# exists."
def get_vendors(): return pd.read_sql_query("SELECT * FROM vendors", get_connection(), index_col='id')
def add_tax(name, value, tax_type):
    query = "INSERT INTO tax_config (tax_name, tax_value, tax_type) VALUES (?, ?, ?)"
    try:
        execute_query(query, (name, value, tax_type)); return True, "Tax added."
    except sqlite3.IntegrityError: return False, "Error: Tax name exists."
# Add to db_functions.py
def update_tax(tid, tax_name, tax_value, tax_type):
    query = "UPDATE tax_config SET tax_name=?, tax_value=?, tax_type=? WHERE id=?"
    try:
        execute_query(query, (tax_name, tax_value, tax_type, tid))
        return True, "Tax configuration updated."
    except sqlite3.IntegrityError:
        return False, "Error: Tax name already exists."
def get_taxes(): return pd.read_sql_query("SELECT * FROM tax_config", get_connection(), index_col='id')
def get_tcs_value():
    """Fetches the TCS percentage from the tax config table."""
    query = "SELECT tax_value FROM tax_config WHERE tax_name = 'TCS'"
    result = execute_query(query, fetch='one')
    return result[0] if result else 1.0

# --- Purchase Order Functions (MODIFIED) ---
def create_purchase_order(vendor_id, po_date, inv_num, remarks, items_df, totals):
    po_query = "INSERT INTO purchase_orders (vendor_id, purchase_date, invoice_number, remarks, total_amount, total_gst, total_tcs, grand_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    po_id = execute_query(po_query, (vendor_id, po_date, inv_num, remarks, totals['total_amount'], totals['total_gst'], totals['total_tcs'], totals['grand_total']))
    
    item_query = "INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, rate, gst_percent, gst_amount, amount) VALUES (?, ?, ?, ?, ?, ?, ?)"
    for _, row in items_df.iterrows():
        execute_query(item_query, (po_id, row['product_id'], row['quantity'], row['rate'], row['gst_percent'], row['gst_amount'], row['amount']))
        update_product_stock(row['product_id'], row['quantity'])
    return True, f"Purchase Order {po_id} created successfully!"

def get_purchase_orders_summary(invoice_search=""):
    base_query = "SELECT po.id, v.name as vendor_name, po.purchase_date, po.invoice_number, po.grand_total FROM purchase_orders po JOIN vendors v ON po.vendor_id = v.id"
    params = []
    if invoice_search:
        base_query += " WHERE po.invoice_number LIKE ?"
        params.append(f"%{invoice_search}%")
    base_query += " ORDER BY po.id DESC"
    return pd.read_sql_query(base_query, get_connection(), params=params)

def get_purchase_order_details(po_id):
    po_query = "SELECT * FROM purchase_orders WHERE id = ?"
    po_data = execute_query(po_query, (po_id,), fetch='one')

    # FIX: Join with tax_config to fetch the actual gst_percent value
    items_query = """
    SELECT
        poi.id as po_item_id, poi.product_id, p.name as product_name, p.size, poi.quantity,
        poi.rate, p.selling_price, p.stock, p.gst_category,
        tc.tax_value as gst_percent
    FROM purchase_order_items poi
    JOIN products p ON poi.product_id = p.id
    LEFT JOIN tax_config tc ON p.gst_category = tc.tax_name
    WHERE poi.purchase_order_id = ?
    """
    items_df = pd.read_sql_query(items_query, get_connection(), params=(po_id,))
    # Ensure gst_percent is not null if a tax category is deleted
    items_df['gst_percent'] = items_df['gst_percent'].fillna(0)
    return po_data, items_df

def update_purchase_order(po_id, vendor_id, po_date, inv_num, remarks, items_df, totals):
    po_update_query = "UPDATE purchase_orders SET vendor_id=?, purchase_date=?, invoice_number=?, remarks=?, total_amount=?, total_gst=?, total_tcs=?, grand_total=? WHERE id=?"
    execute_query(po_update_query, (vendor_id, po_date, inv_num, remarks, totals['total_amount'], totals['total_gst'], totals['total_tcs'], totals['grand_total'], po_id))

    execute_query("DELETE FROM purchase_order_items WHERE purchase_order_id=?", (po_id,))
    
    item_insert_query = "INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, rate, gst_percent, gst_amount, amount) VALUES (?, ?, ?, ?, ?, ?, ?)"
    for _, row in items_df.iterrows():
        execute_query(item_insert_query, (po_id, row['product_id'], row['quantity'], row['rate'], row['gst_percent'], row['gst_amount'], row['amount']))
    
    return True, f"Purchase Order {po_id} updated successfully."

# --- Billing & Reporting Functions (No Changes) ---
def create_bill(bill_date, customer_name, pay_mode, remarks, items_df, totals):
    bill_query = "INSERT INTO bills (bill_date, customer_name, pay_mode, remarks, sub_total, total_gst, grand_total) VALUES (?, ?, ?, ?, ?, ?, ?)"
    bill_id = execute_query(bill_query, (bill_date, customer_name, pay_mode, remarks, totals['sub_total'], totals['total_gst'], totals['grand_total']))
    item_query = "INSERT INTO bill_items (bill_id, product_id, quantity, rate, gst_percent, gst_amount, amount) VALUES (?, ?, ?, ?, ?, ?, ?)"
    for _, row in items_df.iterrows():
        execute_query(item_query, (bill_id, row['product_id'], row['quantity'], row['rate'], row['gst_percent'], row['gst_amount'], row['amount']))
        update_product_stock(row['product_id'], -row['quantity'])
    return True, f"Bill {bill_id} created successfully!"
def get_bill_report(start_date, end_date):
    query = "SELECT b.id as 'Bill No', b.bill_date as 'Bill Date', p.name as 'Product Name', p.size as 'Size', bi.quantity as 'Quantity', bi.rate as 'Rate', bi.amount as 'Amount', b.customer_name as 'Customer Name', b.grand_total as 'Bill Total' FROM bills b JOIN bill_items bi ON b.id = bi.bill_id JOIN products p ON bi.product_id = p.id WHERE b.bill_date BETWEEN ? AND ?"
    return pd.read_sql_query(query, get_connection(), params=(start_date, end_date))
def get_purchase_report(start_date, end_date, vendor_id=None):
    base_query = "SELECT po.id as 'PO No', po.purchase_date as 'Purchase Date', v.name as 'Vendor', p.name as 'Product Name', poi.quantity as 'Quantity', poi.rate as 'Rate', poi.amount as 'Total Amount', po.grand_total as 'PO Grand Total' FROM purchase_orders po JOIN vendors v ON po.vendor_id = v.id JOIN purchase_order_items poi ON po.id = poi.purchase_order_id JOIN products p ON poi.product_id = p.id WHERE po.purchase_date BETWEEN ? AND ?"
    params = (start_date, end_date)
    if vendor_id and vendor_id != 'All':
        base_query += " AND po.vendor_id = ?"; params += (vendor_id,)
    return pd.read_sql_query(base_query, get_connection(), params=params)
def get_stock_report(): return pd.read_sql_query("SELECT p.id as 'Product ID', p.name as 'Product Name', p.type as 'Type', p.size as 'Size', p.selling_price as 'Selling Price', p.stock as 'Available Stock' FROM products p ORDER BY p.name", get_connection())

def get_stock_report_with_dates(start_date, end_date):
    """
    Get stock report with opening and closing stock for the specified date range.
    Opening stock = Current stock + Sales during period - Purchases during period
    Closing stock = Current stock
    """
    # Get current stock for all products
    current_stock_query = "SELECT p.id, p.name as 'Product Name', p.type as 'Type', p.size as 'Size', p.stock as 'Current Stock' FROM products p ORDER BY p.name"
    current_stock_df = pd.read_sql_query(current_stock_query, get_connection())
    
    # Get sales during the period
    sales_query = """
    SELECT bi.product_id, SUM(bi.quantity) as 'Sales Qty'
    FROM bill_items bi 
    JOIN bills b ON bi.bill_id = b.id 
    WHERE b.bill_date BETWEEN ? AND ?
    GROUP BY bi.product_id
    """
    sales_df = pd.read_sql_query(sales_query, get_connection(), params=(start_date, end_date))
    
    # Get purchases during the period
    purchases_query = """
    SELECT poi.product_id, SUM(poi.quantity) as 'Purchase Qty'
    FROM purchase_order_items poi 
    JOIN purchase_orders po ON poi.purchase_order_id = po.id 
    WHERE po.purchase_date BETWEEN ? AND ?
    GROUP BY poi.product_id
    """
    purchases_df = pd.read_sql_query(purchases_query, get_connection(), params=(start_date, end_date))
    
    # Merge all data
    result_df = current_stock_df.copy()
    result_df = result_df.merge(sales_df, left_on='id', right_on='product_id', how='left').fillna(0)
    result_df = result_df.merge(purchases_df, left_on='id', right_on='product_id', how='left').fillna(0)
    
    # Calculate opening stock
    result_df['Opening Stock'] = result_df['Current Stock'] + result_df['Sales Qty'] - result_df['Purchase Qty']
    result_df['Closing Stock'] = result_df['Current Stock']
    
    # Select and rename columns for final output
    final_df = result_df[['Product Name', 'Type', 'Size', 'Opening Stock', 'Closing Stock', 'Sales Qty', 'Purchase Qty']].copy()
    final_df.columns = ['Product Name', 'Type', 'Size', 'Opening Stock', 'Closing Stock', 'Sales (Period)', 'Purchases (Period)']
    
    return final_df
def get_product_wise_sales(start_date, end_date):
    query = "SELECT p.name as 'Product Name', p.size as 'Size', SUM(bi.quantity) as 'Total Quantity Sold', SUM(bi.amount) as 'Total Sales Value' FROM bill_items bi JOIN products p ON bi.product_id = p.id JOIN bills b ON bi.bill_id = b.id WHERE b.bill_date BETWEEN ? AND ? GROUP BY p.name, p.size ORDER BY \"Total Quantity Sold\" DESC"
    return pd.read_sql_query(query, get_connection(), params=(start_date, end_date))
def get_product_wise_purchases(start_date, end_date):
    query = "SELECT p.name as 'Product Name', p.size as 'Size', SUM(poi.quantity) as 'Total Quantity Purchased', SUM(poi.amount) as 'Total Purchase Value' FROM purchase_order_items poi JOIN products p ON poi.product_id = p.id JOIN purchase_orders po ON poi.purchase_order_id = po.id WHERE po.purchase_date BETWEEN ? AND ? GROUP BY p.name, p.size ORDER BY \"Total Quantity Purchased\" DESC"
    return pd.read_sql_query(query, get_connection(), params=(start_date, end_date))
def get_bulk_litre_report(start_date, end_date):
    query = "SELECT p.id, p.name, p.size, bi.quantity FROM bills b JOIN bill_items bi ON b.id = bi.bill_id JOIN products p ON bi.product_id = p.id WHERE b.bill_date BETWEEN ? AND ?"
    df = pd.read_sql_query(query, get_connection(), params=(start_date, end_date))
    if df.empty: return pd.DataFrame(columns=['Product Name', 'Total Litres Sold'])
    def convert_to_litres(size_str):
        if not isinstance(size_str, str): return 0
        size_str = size_str.lower().strip()
        if 'ml' in size_str: return float(size_str.replace('ml', '')) / 1000
        elif 'l' in size_str: return float(size_str.replace('l', ''))
        return 0
    df['size_in_litres'] = df['size'].apply(convert_to_litres)
    df['total_litres'] = df['quantity'] * df['size_in_litres']
    report = df.groupby('name')['total_litres'].sum().reset_index()
    report.columns = ['Product Name', 'Total Litres Sold']
    return report.sort_values(by='Total Litres Sold', ascending=False)

def auto_generate_bills_for_month(start_date, end_date, product_id, total_quantity):
    """
    Automatically generate bills for a product, distributing total_quantity randomly across days in the date range.
    Uses 'Cash Customer', 'Cash' payment mode, and 'auto-generated' remarks.
    Strictly prevents over-billing: if total_quantity > available stock, returns an error.
    Returns a summary of generated bills.
    """
    from datetime import timedelta, datetime
    import pandas as pd
    
    # Get product details
    products_df = get_products()
    if product_id not in products_df.index:
        return False, f"Product ID {product_id} not found."
    product = products_df.loc[product_id]
    available_stock = int(product['stock'])
    if total_quantity > available_stock:
        return False, f"Cannot generate bills: Requested quantity ({total_quantity}) exceeds available stock ({available_stock})."
    
    # Get GST percent
    taxes_df = get_taxes()
    tax_info = taxes_df[taxes_df['tax_name'] == product['gst_category']]
    gst_percent = tax_info['tax_value'].iloc[0] if not tax_info.empty else 0
    
    # Generate date range
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    days = (end_dt - start_dt).days + 1
    if days <= 0:
        return False, "Invalid date range."
    
    # Randomly distribute total_quantity across days
    import numpy as np
    if total_quantity < days:
        # Not enough quantity for each day, assign 1 to total_quantity days
        daily_quantities = [1]*total_quantity + [0]*(days-total_quantity)
        np.random.shuffle(daily_quantities)
    else:
        # Use multinomial distribution for random split
        daily_quantities = np.random.multinomial(total_quantity, [1/days]*days)
    
    # Prepare summary
    summary = []
    for i, qty in enumerate(daily_quantities):
        if qty == 0:
            continue
        bill_date = (start_dt + timedelta(days=i)).date().isoformat()
        # Prepare items_df for create_bill
        items_df = pd.DataFrame([{
            'product_id': product_id,
            'name': f"{product['name']} ({product['size']})",
            'quantity': qty,
            'rate': product['selling_price'],
            'gst_percent': gst_percent,
            'gst_category': product['gst_category']
        }])
        # Calculate totals as in render_billing
        items_df['base_price'] = items_df['rate'] / (1 + items_df['gst_percent'] / 100)
        items_df['sub_total_line'] = items_df['base_price'] * items_df['quantity']
        items_df['amount'] = items_df['rate'] * items_df['quantity']
        items_df['gst_amount'] = items_df['amount'] - items_df['sub_total_line']
        sub_total = items_df['sub_total_line'].sum()
        total_gst = items_df['gst_amount'].sum()
        grand_total = items_df['amount'].sum()
        totals = {'sub_total': sub_total, 'total_gst': total_gst, 'grand_total': grand_total}
        # Create bill
        success, message = create_bill(bill_date, 'Cash Customer', 'Cash', 'auto-generated', items_df, totals)
        summary.append({'date': bill_date, 'quantity': qty, 'success': success, 'message': message})
    return True, summary

def get_bill_by_id(bill_id):
    """Fetch a single bill and its items by bill_id."""
    bill_query = "SELECT * FROM bills WHERE id = ?"
    bill = execute_query(bill_query, (bill_id,), fetch='one')
    items_query = "SELECT * FROM bill_items WHERE bill_id = ?"
    items = pd.read_sql_query(items_query, get_connection(), params=(bill_id,))
    return bill, items

def update_bill(bill_id, bill_date, customer_name, pay_mode, remarks, items_df, totals):
    """Update a bill and its items. Stock is adjusted accordingly."""
    # Get original items to revert stock
    _, original_items = get_bill_by_id(bill_id)
    for _, row in original_items.iterrows():
        update_product_stock(row['product_id'], row['quantity'])  # revert stock
    # Update bill
    bill_update_query = "UPDATE bills SET bill_date=?, customer_name=?, pay_mode=?, remarks=?, sub_total=?, total_gst=?, grand_total=? WHERE id=?"
    execute_query(bill_update_query, (bill_date, customer_name, pay_mode, remarks, totals['sub_total'], totals['total_gst'], totals['grand_total'], bill_id))
    # Delete old items
    execute_query("DELETE FROM bill_items WHERE bill_id=?", (bill_id,))
    # Insert new items and update stock
    item_query = "INSERT INTO bill_items (bill_id, product_id, quantity, rate, gst_percent, gst_amount, amount) VALUES (?, ?, ?, ?, ?, ?, ?)"
    for _, row in items_df.iterrows():
        execute_query(item_query, (bill_id, row['product_id'], row['quantity'], row['rate'], row['gst_percent'], row['gst_amount'], row['amount']))
        update_product_stock(row['product_id'], -row['quantity'])
    return True, f"Bill {bill_id} updated successfully!"

def delete_bill(bill_id):
    """Delete a bill and its items. Stock is adjusted accordingly."""
    _, items = get_bill_by_id(bill_id)
    for _, row in items.iterrows():
        update_product_stock(row['product_id'], row['quantity'])  # revert stock
    execute_query("DELETE FROM bill_items WHERE bill_id=?", (bill_id,))
    execute_query("DELETE FROM bills WHERE id=?", (bill_id,))
    return True, f"Bill {bill_id} deleted successfully!"

def get_store_info():
    query = "SELECT name, address, vat_number FROM store_info WHERE id = 1"
    result = execute_query(query, fetch='one')
    if result:
        return {'name': result[0], 'address': result[1], 'vat_number': result[2]}
    else:
        return {'name': '', 'address': '', 'vat_number': ''}

def update_store_info(name, address, vat_number):
    # Upsert logic: insert or update row with id=1
    query = "INSERT INTO store_info (id, name, address, vat_number) VALUES (1, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, address=excluded.address, vat_number=excluded.vat_number"
    execute_query(query, (name, address, vat_number))
    return True, "Store info updated."
