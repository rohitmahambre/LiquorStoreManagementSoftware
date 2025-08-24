# app1.py - Modern Button-Based UI
import streamlit as st
import pandas as pd
from datetime import date, datetime

from database import create_tables
import db_functions as db

st.set_page_config(page_title="Liquor Store POS", layout="wide")
create_tables()

# --- Initialize Session State ---
if 'app_mode' not in st.session_state: st.session_state.app_mode = "main" # main, po_create, po_edit
if 'cart' not in st.session_state: st.session_state.cart = []
if 'selected_po_id' not in st.session_state: st.session_state.selected_po_id = None
if 'po_edit_id' not in st.session_state: st.session_state.po_edit_id = None
if 'po_items' not in st.session_state: st.session_state.po_items = []
if 'original_po_items' not in st.session_state: st.session_state.original_po_items = pd.DataFrame()


def refresh_data(force=False):
    """Refreshes dataframes in the session state."""
    st.session_state.products_df = db.get_products()
    st.session_state.vendors_df = db.get_vendors()
    st.session_state.taxes_df = db.get_taxes()
    st.session_state.customers_df = db.get_customers()

def change_app_mode(mode, po_id=None):
    st.session_state.app_mode = mode
    st.session_state.po_edit_id = po_id
    if mode == "po_create":
        # Start a new PO with one empty line
        st.session_state.po_items = [{"product_id": None}]
    elif mode == "po_edit":
        # Load existing PO data
        _, items_df = db.get_purchase_order_details(po_id)
        st.session_state.po_items = items_df.to_dict('records')
        st.session_state.original_po_items = items_df.copy()
    else:
        st.session_state.po_items = []
        st.session_state.original_po_items = pd.DataFrame()
        
# --- Main App ---
def main():
    # Fetch store info from the database
    store_info = db.get_store_info()
    st.title(f"🍾 {store_info['name']}")
    refresh_data()
    
    # Sidebar refresh button
    st.sidebar.button("🔄 Refresh Data", on_click=refresh_data, args=(True,), use_container_width=True)
    
    # Check if we're in PO mode first
    if st.session_state.app_mode.startswith("po_"):
        render_purchases()
        return
    
    # Main menu with square buttons
    st.markdown("---")
    st.subheader("Main Menu")
    
    # Create a 3-column grid for better alignment
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🛒 **Billing**", use_container_width=True, type="secondary"):
            st.session_state.current_page = "Billing"
            st.rerun()
        
        if st.button("📦 **Purchases**", use_container_width=True, type="secondary"):
            st.session_state.current_page = "Purchases"
            st.rerun()
            
    with col2:
        if st.button("⚙️ **Master Data**", use_container_width=True, type="secondary"):
            st.session_state.current_page = "Master Data"
            st.rerun()
        if st.button("📈 **Reports**", use_container_width=True, type="secondary"):
            st.session_state.current_page = "Reports"
            st.rerun()
    
    with col3:
        if st.button("🧾 **Bills Management**", use_container_width=True, type="secondary"):
            st.session_state.current_page = "Bills Management"
            st.rerun()
    
    # Initialize current_page if not set
    if 'current_page' not in st.session_state:
        st.session_state.current_page = None
    
    # Render the selected page
    if st.session_state.current_page == "Billing":
        render_billing()
    elif st.session_state.current_page == "Purchases":
        render_po_form()
    elif st.session_state.current_page == "Master Data":
        render_master_data()
    elif st.session_state.current_page == "Reports":
        render_reports()
    elif st.session_state.current_page == "Bills Management":
        render_bills_management()
    else:
        # Show welcome message when no page is selected
        st.markdown("---")
        st.markdown("### Sales Overview")
        
        # Quick stats
        from datetime import timedelta
        today = date.today()
        periods = [
            ("1 Month", today - timedelta(days=30)),
            ("3 Months", today - timedelta(days=90)),
            ("6 Months", today - timedelta(days=180)),
        ]
        sales_stats = []
        for label, start in periods:
            report_df = db.get_bill_report(start.isoformat(), today.isoformat())
            total_sales = report_df['Bill Total'].sum() if not report_df.empty and 'Bill Total' in report_df else 0
            sales_stats.append((label, total_sales))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sales (1 Month)", f"₹ {sales_stats[0][1]:,.2f}")
        with col2:
            st.metric("Sales (3 Months)", f"₹ {sales_stats[1][1]:,.2f}")
        with col3:
            st.metric("Sales (6 Months)", f"₹ {sales_stats[2][1]:,.2f}")

        # Products sold this month and their current stock
        st.markdown("#### Products Sold This Month (with Current Stock)")
        month_start = today.replace(day=1)
        sales_df = db.get_product_wise_sales(month_start.isoformat(), today.isoformat())
        if not sales_df.empty:
            # Merge with current stock
            stock_df = db.get_stock_report()
            merged = pd.merge(sales_df, stock_df, left_on=['Product Name', 'Size'], right_on=['Product Name', 'Size'], how='left')
            merged = merged[['Product Name', 'Size', 'Total Quantity Sold', 'Available Stock']]
            st.dataframe(merged, use_container_width=True)
        else:
            st.info("No products sold this month.")

# --- Page Rendering Functions ---
def render_billing():
    # Back to main menu button
    if st.button("← Back to Main Menu", type="secondary"):
        st.session_state.current_page = None
        st.rerun()
    
    st.header("Retail Billing")
    bill_date = st.date_input("Bill Date", value=date.today())
    
    products_df = st.session_state.products_df
    taxes_df = st.session_state.taxes_df

    product_list = []
    for idx, row in products_df.iterrows():
        quantity_in_cart = sum(item['quantity'] for item in st.session_state.cart if item['product_id'] == idx)
        effective_stock = int(row['stock']) - quantity_in_cart
        product_list.append(f"{row['name']} - {row['size']} ({effective_stock} left)")

    col1, col2 = st.columns([2, 3])
    with col1:
        st.subheader("Add Product to Bill")
        selected_product_str = st.selectbox("Select Product", options=product_list, index=None, placeholder="Choose a product...")

        if selected_product_str:
            product_name_size = selected_product_str.split(' (')[0]
            selected_product_row = products_df[products_df.apply(lambda row: f"{row['name']} - {row['size']}" == product_name_size, axis=1)]
            selected_product = selected_product_row.iloc[0] if not selected_product_row.empty else None

            if selected_product is not None:
                quantity_in_cart = sum(item['quantity'] for item in st.session_state.cart if item['product_id'] == selected_product.name)
                effective_stock = int(selected_product['stock']) - quantity_in_cart
                
                if effective_stock > 0:
                    quantity = st.number_input(f"Quantity for {selected_product['name']}", min_value=1, value=1, step=1, max_value=effective_stock)
                    if st.button("Add to Cart"):
                        tax_info = taxes_df[taxes_df['tax_name'] == selected_product['gst_category']]
                        gst_percent = tax_info['tax_value'].iloc[0] if not tax_info.empty else 0
                        # Check if product already exists in cart
                        existing_item = next((item for item in st.session_state.cart if item['product_id'] == selected_product.name), None)

                        if existing_item:
                            # Update existing item quantity
                            if existing_item['quantity'] + quantity <= effective_stock:
                                existing_item['quantity'] += quantity
                            else:
                                st.error("Cannot add more units than available stock")
                        else:
                            # Add new item to cart
                            st.session_state.cart.append({
                                "product_id": selected_product.name,
                                "name": f"{selected_product['name']} ({selected_product['size']})",
                                "quantity": quantity,
                                "rate": selected_product['selling_price'],
                                "gst_percent": gst_percent,
                                "gst_category": selected_product['gst_category']
                            })
                        st.rerun()
                else:
                    st.warning(f"No more stock available for {selected_product['name']}. All available units are in the cart.")

    with col2:
        st.subheader("Current Bill")
        if st.session_state.cart:
            # Create a DataFrame for better display and editing
            cart_df = pd.DataFrame(st.session_state.cart)

            # Display each item with edit/delete buttons
            for idx, item in enumerate(st.session_state.cart):
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                col1.write(item['name'])

                # Quantity modifier
                current_qty = item['quantity']
                new_qty = col2.number_input(
                    "Qty",
                    min_value=1,
                    max_value=int(products_df.loc[item['product_id']]['stock']),
                    value=current_qty,
                    key=f"qty_{idx}"
                )
                if new_qty != current_qty:
                    item['quantity'] = new_qty
                    st.rerun()

                # Display rate and amount
                col3.write(f"₹ {item['rate']:.2f}")
                col4.write(f"₹ {item['rate'] * item['quantity']:.2f}")

                # Delete button
                if col5.button("🗑️", key=f"del_{idx}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()

            # Calculate totals
            cart_df = pd.DataFrame(st.session_state.cart)
            cart_df['base_price'] = cart_df['rate'] / (1 + cart_df['gst_percent'] / 100)
            cart_df['sub_total_line'] = cart_df['base_price'] * cart_df['quantity']
            cart_df['amount'] = cart_df['rate'] * cart_df['quantity']
            cart_df['gst_amount'] = cart_df['amount'] - cart_df['sub_total_line']

            sub_total = cart_df['sub_total_line'].sum()
            total_gst = cart_df['gst_amount'].sum()
            grand_total = cart_df['amount'].sum()

            st.metric("Sub-Total", f"₹ {sub_total:,.2f}")
            st.metric("Total GST", f"₹ {total_gst:,.2f}")
            st.metric("Grand Total", f"₹ {grand_total:,.2f}")

            form_col, cancel_col = st.columns([4,1])
            with form_col:
                with st.form("bill_details"):
                    # Create customer dropdown with Cash Customer as default
                    customers_df = st.session_state.customers_df
                    customer_options = ["Cash Customer"] + customers_df['name'].tolist()
                    customer_name = st.selectbox("Customer Name", options=customer_options, index=0)
                    pay_mode = st.selectbox("Payment Mode", ["Cash", "Card", "UPI"])
                    if st.form_submit_button("Generate Bill", use_container_width=True):
                        totals = {'sub_total': sub_total, 'total_gst': total_gst, 'grand_total': grand_total}
                        success, message = db.create_bill(bill_date.isoformat(), customer_name, pay_mode, "", cart_df, totals)
                        if success:
                            st.success(message); st.balloons()
                            st.session_state.cart = []; refresh_data(force=True); st.rerun()
                        else: st.error(message)
            
            with cancel_col:
                st.write(""); st.write("")
                if st.button("❌ Cancel", type="secondary", use_container_width=True):
                    st.session_state.cart = []; st.rerun()
        else:
            st.info("Your cart is empty.")

def render_po_form():
    """Displays the list of POs and the 'Create New' button."""
    # Back to main menu button
    if st.button("← Back to Main Menu", type="secondary"):
        st.session_state.current_page = None
        st.rerun()
    
    st.header("Purchases")
    if st.button("Create New Purchase Order"):
        change_app_mode("po_create")
        st.rerun()

    st.markdown("---")
    st.subheader("Existing Purchase Orders")
    invoice_search = st.text_input("Search by Invoice Number")
    po_summary_df = db.get_purchase_orders_summary(invoice_search)

    if po_summary_df.empty:
        st.info("No purchase orders found.")
    else:
        for _, row in po_summary_df.iterrows():
            cols = st.columns([1, 2, 2, 2, 1])
            cols[0].metric("PO #", row.id)
            cols[1].metric("Vendor", row.vendor_name)
            cols[2].metric("Invoice #", row.invoice_number)
            cols[3].metric("Grand Total", f"₹{row.grand_total:,.2f}")
            if cols[4].button("View/Edit", key=f"edit_{row.id}"):
                change_app_mode("po_edit", po_id=row.id)
                st.rerun()

def render_purchases():
    """Renders the unified form for creating and editing a PO."""
    products_df = st.session_state.products_df
    vendors_df = st.session_state.vendors_df
    taxes_df = st.session_state.taxes_df
    
    product_options = {idx: f"{row['name']} - {row['size']}" for idx, row in products_df.iterrows()}
    vendor_options = {idx: name for idx, name in vendors_df['name'].items()}

    header_text = "Create New Purchase Order" if st.session_state.app_mode == "po_create" else f"Editing PO #{st.session_state.po_edit_id}"
    st.header(header_text)

    # --- Section 1: Item Management (OUTSIDE the form) ---
    st.subheader("Items")
    for i, item in enumerate(st.session_state.po_items):
        # Auto-populate details when a product is selected for the first time
        if item.get("product_id") and "product_name" not in item:
            product_details = products_df.loc[item["product_id"]]
            tax_info = taxes_df[taxes_df['tax_name'] == product_details['gst_category']]
            item.update({
                "product_name": f"{product_details['name']} - {product_details['size']}",
                "rate": product_details['purchase_price'],
                "selling_price": product_details['selling_price'],
                "stock": product_details['stock'],
                "gst_percent": tax_info['tax_value'].iloc[0] if not tax_info.empty else 0
            })

        cols = st.columns([3, 1, 1, 1, 1, 1])
        # Add a placeholder for the selectbox to show "Select..."
        all_product_options = {None: "Select..."}
        all_product_options.update(product_options)
        
        selected_product_id = cols[0].selectbox("Product", options=all_product_options.keys(), format_func=lambda x: all_product_options.get(x), key=f"prod_{i}", index=list(all_product_options.keys()).index(item.get("product_id")) if item.get("product_id") in all_product_options else 0)
        
        if selected_product_id != item.get("product_id"):
            st.session_state.po_items[i] = {"product_id": selected_product_id, "rate": 0.01, "quantity": 1}
            st.rerun()

        item['quantity'] = cols[1].number_input("Quantity", min_value=1, value=item.get("quantity", 1), key=f"qty_{i}")
        item['rate'] = cols[2].number_input("Purchase Rate", min_value=0.01, value=item.get("rate", 0.01),  format="%.2f", disabled=True, key=f"rate_{i}")
        cols[3].text_input("Stock", value=item.get("stock", "-"), disabled=True, key=f"stock_{i}")
        cols[4].text_input("VAT %", value=f"{item.get('gst_percent', 0):.2f}%", disabled=True, key=f"gst%_{i}")
        item['selling_price'] = cols[5].number_input("Selling Rate", min_value=0.01, value=item.get('selling_price', 0.01), format="%.2f", disabled=True, key=f"sell_{i}")

    c1, c2, _ = st.columns([1, 1, 8])
    if c1.button("Add Item"):
        st.session_state.po_items.append({"product_id": None, "rate": 0.01, "quantity": 1})
        st.rerun()
    if c2.button("Remove Last Item") and st.session_state.po_items:
        st.session_state.po_items.pop()
        st.rerun()
    st.markdown("---")

    # --- Section 2: Details and Submission (INSIDE the form) ---
    with st.form("po_details_form"):
        st.subheader("Details & Submission")
        po_data = {}
        if st.session_state.app_mode == "po_edit":
            po_header_data, _ = db.get_purchase_order_details(st.session_state.po_edit_id)
            po_data = {
                "vendor_id": po_header_data[1],
                "purchase_date": datetime.strptime(po_header_data[2], '%Y-%m-%d').date(),
                "invoice_number": po_header_data[3],
                "remarks": po_header_data[9]
            }

        c1, c2, c3 = st.columns(3)
        vendor_id = c1.selectbox("Vendor", options=vendor_options.keys(), format_func=lambda x: vendor_options.get(x, ''), index=list(vendor_options.keys()).index(po_data.get("vendor_id")) if po_data.get("vendor_id") in vendor_options else 0)
        purchase_date = c2.date_input("Date", value=po_data.get("purchase_date", date.today()))
        invoice_number = c3.text_input("Invoice/DC Number", value=po_data.get("invoice_number", ""))
        remarks = st.text_area("Remarks", value=po_data.get("remarks", ""))
        
        items_df = pd.DataFrame([item for item in st.session_state.po_items if item.get('product_id')])
        if not items_df.empty:
            items_df['amount'] = items_df['quantity'] * items_df['rate']
            items_df['gst_amount'] = items_df['amount'] * items_df['gst_percent'] / 100
            total_amount, total_gst = items_df['amount'].sum(), items_df['gst_amount'].sum()
            tcs_rate = db.get_tcs_value()
            total_tcs = (total_amount + total_gst) * (tcs_rate / 100)
            grand_total = total_amount + total_gst + total_tcs

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Amount", f"₹{total_amount:,.2f}")
            c2.metric("Total GST", f"₹{total_gst:,.2f}")
            c3.metric(f"Total TCS ({tcs_rate}%)", f"₹{total_tcs:,.2f}")
            c4.metric("Grand Total", f"₹{grand_total:,.2f}")

        st.markdown("---")
        c1, c2 = st.columns(2)
        submitted = c1.form_submit_button("✅ Save Purchase Order", use_container_width=True)
        if c2.form_submit_button("❌ Cancel", use_container_width=True, type="secondary"):
            change_app_mode("main")
            st.rerun()
            
        if submitted:
            if items_df.empty:
                st.error("Please add at least one product to the purchase order.")
            else:
                totals = {'total_amount': total_amount, 'total_gst': total_gst, 'total_tcs': total_tcs, 'grand_total': grand_total}
                if st.session_state.app_mode == "po_create":
                    success, msg = db.create_purchase_order(vendor_id, purchase_date.isoformat(), invoice_number, remarks, items_df, totals)
                else:
                    original_df = st.session_state.original_po_items
                    for _, row in original_df.iterrows(): db.update_product_stock(row['product_id'], -row['quantity'])
                    for _, row in items_df.iterrows(): db.update_product_stock(row['product_id'], row['quantity'])
                    success, msg = db.update_purchase_order(st.session_state.po_edit_id, vendor_id, purchase_date.isoformat(), invoice_number, remarks, items_df, totals)
                
                if success:
                    st.success(msg)
                    change_app_mode("main")
                    refresh_data(force=True)
                    st.rerun()
                else:
                    st.error(msg)
                            
def render_master_data():
    # Back to main menu button
    if st.button("← Back to Main Menu", type="secondary"):
        st.session_state.current_page = None
        st.rerun()
    st.header("Master Data Management")
    # Initialize master data section if not set
    if 'master_data_section' not in st.session_state:
        st.session_state.master_data_section = None
    # Master data section selection with buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📦 Products", use_container_width=True):
            st.session_state.master_data_section = "Products"
            st.rerun()
        if st.button("👥 Customers", use_container_width=True):
            st.session_state.master_data_section = "Customers"
            st.rerun()
    with col2:
        if st.button("🏢 Vendors", use_container_width=True):
            st.session_state.master_data_section = "Vendors"
            st.rerun()
        if st.button("💰 Tax Config", use_container_width=True):
            st.session_state.master_data_section = "Tax Config"
            st.rerun()
    with col3:
        if st.button("🏪 Store Info", use_container_width=True):
            st.session_state.master_data_section = "Store Info"
            st.rerun()
    # Render the selected section
    if st.session_state.master_data_section == "Products":
        render_products_section()
    elif st.session_state.master_data_section == "Customers":
        render_customers_section()
    elif st.session_state.master_data_section == "Vendors":
        render_vendors_section()
    elif st.session_state.master_data_section == "Tax Config":
        render_tax_section()
    elif st.session_state.master_data_section == "Store Info":
        render_store_info_section()
    else:
        st.info("Select a data type from the buttons above to manage master data.")

def render_products_section():
    st.subheader("📦 Products Management")
    
    with st.expander("Add New Product", expanded=False):
        with st.form("new_product_form"):
            name = st.text_input("Product Name")
            p_type = st.selectbox("Type", ["Beer", "Brandy", "Gin", "Port Wine", "Rum", "Rtd", "Tequila", "Vodka", "Wine", "Whisky" ])
            size = st.selectbox("Size", ["90ml", "180ml", "375ml", "500ml", "650ml", "750ml", "1L", "2L"])
            purchase_price = st.number_input("Purchase Price", min_value=0.0, format="%.2f")
            selling_price = st.number_input("Selling Price", min_value=0.0, format="%.2f")
            category = st.selectbox("Category", ["BEER", "IMFL", "CL", "OTHERS"])
            
            taxes_df = st.session_state.taxes_df
            gst_category = st.selectbox("VAT Category", taxes_df['tax_name'].tolist())
            
            submitted = st.form_submit_button("Add Product")
            if submitted:
                # Validate form fields
                if not name:
                    st.error("Product name is required.")
                elif purchase_price <= 0:
                    st.error("Purchase price must be greater than 0.")
                elif selling_price <= 0:
                    st.error("Selling price must be greater than 0.")
                elif not gst_category:
                    st.error("VAT category is required.")
                else:
                    success, message = db.add_product(name, p_type, size, purchase_price, selling_price, category, gst_category)
                    if success:
                        st.success(message)
                        refresh_data()
                    else:
                        st.error(message)
     
    st.subheader("Edit Products")
    st.info("Edit data directly in the table. Click 'Save Changes' to apply. To delete a row, select it and press the 'Delete' key, then save.")

    # Keep a copy of the original for comparison
    if 'original_products_df' not in st.session_state:
        st.session_state.original_products_df = st.session_state.products_df.copy()

    edited_products_df = st.data_editor(
        st.session_state.products_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "stock": st.column_config.NumberColumn(disabled=True),
            "id": st.column_config.NumberColumn(disabled=True)
        }
    )

    if st.button("Save Product Changes"):
        try:
            # Handle deleted rows first
            deleted_ids = set(st.session_state.original_products_df.index) - set(edited_products_df.index)
            for pid in deleted_ids:
                success, msg = db.delete_entity('products', pid)
                if not success:
                    st.error(f"Error deleting product ID {pid}: {msg}")

            # Handle new and modified rows
            for idx, row in edited_products_df.iterrows():
                if pd.isna(idx):  # New row
                    success, msg = db.add_product(
                        row['name'],
                        row['type'],
                        row['size'],
                        row['purchase_price'],
                        row['selling_price'],
                        row['category'],
                        row['gst_category']
                    )
                    if not success:
                        st.error(f"Error adding product {row['name']}: {msg}")
                else:  # Existing row
                    original_row = st.session_state.original_products_df.loc[idx] if idx in st.session_state.original_products_df.index else None
                    if original_row is not None and (row != original_row).any():
                        success, msg = db.update_product(
                            idx,
                            row['name'],
                            row['type'],
                            row['size'],
                            row['purchase_price'],
                            row['selling_price'],
                            row['category'],
                            row['gst_category']
                        )
                        if not success:
                            st.error(f"Error updating product {row['name']}: {msg}")

            # Refresh data and update original copy
            refresh_data(force=True)
            st.session_state.original_products_df = st.session_state.products_df.copy()
            st.success("Product changes saved successfully!")
            #st.rerun()

        except Exception as e:
            st.error(f"An error occurred while saving changes: {str(e)}")

def render_customers_section():
    st.subheader("👥 Customers Management")
    
    with st.expander("Add New Customer", expanded=False):
        with st.form("new_customer_form"):
            # Form fields for customer
            name = st.text_input("Customer Name")
            mobile = st.text_input("Mobile (Unique)")
            address = st.text_input("Address")
            # ... other fields
            submitted = st.form_submit_button("Add Customer")
            if submitted:
                # Validate that all fields are filled
                if not name.strip():
                    st.error("Customer Name is required.")
                elif not mobile.strip():
                    st.error("Mobile is required.")
                elif not address.strip():
                    st.error("Address is required.")
                else:
                    # Add customer to the database
                    success, message = db.add_customer(name, address, "", "", "", "", mobile, "")
                    if success:
                        st.success(message)
                        refresh_data()
                    else:
                        st.error(message)
    
    st.subheader("Edit Customers")
    st.info("Edit data directly in the table. Click 'Save Changes' to apply. To delete a row, select it and press the 'Delete' key, then save.")

    # Keep a copy of the original for comparison
    if 'original_customers_df' not in st.session_state:
        st.session_state.original_customers_df = st.session_state.customers_df.copy()

    # Create the data editor with specific column configurations
    edited_customers_df = st.data_editor(
        st.session_state.customers_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn(disabled=True),
            "name": st.column_config.TextColumn("Name", required=True),
            "mobile": st.column_config.TextColumn("Mobile", required=True),
            "address": st.column_config.TextColumn("Address"),
            "area": st.column_config.TextColumn("Area"),
            "city": st.column_config.TextColumn("City"),
            "state": st.column_config.TextColumn("State"),
            "pincode": st.column_config.TextColumn("Pincode"),
            "email": st.column_config.TextColumn("Email")
        }
    )

    if st.button("Save Customer Changes"):
        try:
            # Handle deleted rows first
            deleted_ids = set(st.session_state.original_customers_df.index) - set(edited_customers_df.index)
            for cid in deleted_ids:
                success, msg = db.delete_entity('customers', cid)
                if not success:
                    st.error(f"Error deleting customer ID {cid}: {msg}")

            # Handle new and modified rows
            for idx, row in edited_customers_df.iterrows():
                if pd.isna(idx):  # New row
                    success, msg = db.add_customer(
                        row['name'], row['address'], row['area'],
                        row['city'], row['state'], row['pincode'],
                        row['mobile'], row['email']
                    )
                else:  # Existing row
                    # Check if row is modified by comparing with original
                    original_row = st.session_state.original_customers_df.loc[idx] if idx in st.session_state.original_customers_df.index else None
                    if original_row is not None and (row != original_row).any():
                        success, msg = db.update_customer(
                            idx, row['name'], row['address'], row['area'],
                            row['city'], row['state'], row['pincode'],
                            row['mobile'], row['email']
                        )
                        if not success:
                            st.error(f"Error updating customer {row['name']}: {msg}")

            # Refresh data and update original copy
            refresh_data(force=True)
            st.session_state.original_customers_df = st.session_state.customers_df.copy()
            st.success("Customer changes saved successfully!")
            #st.rerun()

        except Exception as e:
            st.error(f"An error occurred while saving changes: {str(e)}")

def render_vendors_section():
    st.subheader("🏢 Vendors Management")
    
    with st.expander("Add New Vendor", expanded=False):
        with st.form("new_vendor_form"):
            name = st.text_input("Vendor Name (Unique)")
            gst_number = st.text_input("VAT Number (Unique)")
            mobile = st.text_input("Mobile")
            # ... other fields
            submitted = st.form_submit_button("Add Vendor")
            if submitted:
                # Validation checks
                if not name.strip():
                    st.error("Vendor Name is required.")
                elif not gst_number.strip():
                    st.error("VAT Number is required.")
                elif not mobile.strip():
                    st.error("Mobile number is required.")
                else:
                    # If all validations pass, proceed to add the vendor
                    success, message = db.add_vendor(name, "", "", "", "", "", mobile, "", gst_number)
                    if success:
                        st.success(message)
                        refresh_data()
                    else:
                        st.error(message)
    
    st.subheader("Edit Vendors")
    st.info("Edit data directly in the table. Click 'Save Changes' to apply. To delete a row, select it and press the 'Delete' key, then save.")

    # Keep a copy of the original for comparison
    if 'original_vendors_df' not in st.session_state:
        st.session_state.original_vendors_df = st.session_state.vendors_df.copy()

    # Create the data editor with specific column configurations
    edited_vendors_df = st.data_editor(
        st.session_state.vendors_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn(disabled=True),
            "name": st.column_config.TextColumn("Name", required=True),
            "gst_number": st.column_config.TextColumn("VAT Number", required=True),
            "mobile": st.column_config.TextColumn("Mobile"),
            "address": st.column_config.TextColumn("Address"),
            "area": st.column_config.TextColumn("Area"),
            "city": st.column_config.TextColumn("City"),
            "state": st.column_config.TextColumn("State"),
            "pincode": st.column_config.TextColumn("Pincode"),
            "email": st.column_config.TextColumn("Email")
        }
    )

    if st.button("Save Vendor Changes"):
        try:
            # Handle deleted rows first
            deleted_ids = set(st.session_state.original_vendors_df.index) - set(edited_vendors_df.index)
            for vid in deleted_ids:
                success, msg = db.delete_entity('vendors', vid)
                if not success:
                    st.error(f"Error deleting vendor ID {vid}: {msg}")

            # Handle new and modified rows
            for idx, row in edited_vendors_df.iterrows():
                if pd.isna(idx):  # New row
                    success, msg = db.add_vendor(
                        row['name'], row['address'], row['area'],
                        row['city'], row['state'], row['pincode'],
                        row['mobile'], row['email'], row['gst_number']
                    )
                    if not success:
                        st.error(f"Error adding vendor {row['name']}: {msg}")
                else:  # Existing row
                    original_row = st.session_state.original_vendors_df.loc[idx] if idx in st.session_state.original_vendors_df.index else None
                    if original_row is not None and (row != original_row).any():
                        success, msg = db.update_vendor(
                            idx, row['name'], row['address'], row['area'],
                            row['city'], row['state'], row['pincode'],
                            row['mobile'], row['email'], row['gst_number']
                        )
                        if not success:
                            st.error(f"Error updating vendor {row['name']}: {msg}")

            # Refresh data and update original copy
            refresh_data(force=True)
            st.session_state.original_vendors_df = st.session_state.vendors_df.copy()
            st.success("Vendor changes saved successfully!")
            #st.rerun()

        except Exception as e:
            st.error(f"An error occurred while saving changes: {str(e)}")

        except Exception as e:
            st.error(f"An error occurred while saving changes: {str(e)}")

def render_tax_section():
    st.subheader("💰 Tax Configuration Management")
    
    with st.expander("Add New Tax Rule", expanded=False):
        with st.form("new_tax_form", clear_on_submit=True):
            tax_name = st.text_input("Tax Name (e.g., GST 5%)")
            tax_value = st.number_input("Tax Value (%)", min_value=0.0)
            tax_type = st.selectbox("Tax Type", ["GST", "VAT", "Other"])
            submitted = st.form_submit_button("Add Tax")
            if submitted:
                # Validation checks
                if not tax_name.strip():
                    st.error("Tax Name is required.")
                elif tax_value <= 0:
                    st.error("Tax Value must be greater than 0.")
                elif not tax_type.strip():
                    st.error("Tax Type is required.")
                else:
                    # If all validations pass, proceed to add the tax rule
                    success, message = db.add_tax(tax_name, tax_value, tax_type)
                    if success:
                        st.success(message)
                        refresh_data()
                    else:
                        st.error(message)
    
    st.subheader("Edit Tax Configurations")
    st.info("Edit data directly in the table. Click 'Save Changes' to apply. To delete a row, select it and press the 'Delete' key, then save.")

    # Keep a copy of the original for comparison
    if 'original_taxes_df' not in st.session_state:
        st.session_state.original_taxes_df = st.session_state.taxes_df.copy()

    # Create the data editor with specific column configurations
    edited_taxes_df = st.data_editor(
        st.session_state.taxes_df,
        num_rows="dynamic",
        use_container_width=True,
        key="taxes_editor",
        column_config={
            "id": st.column_config.NumberColumn(disabled=True),
            "tax_name": st.column_config.TextColumn("Tax Name", required=True),
            "tax_value": st.column_config.NumberColumn("Tax Value (%)", required=True, min_value=0.0, max_value=100.0, format="%.2f"),
            "tax_type": st.column_config.SelectboxColumn(
                "Tax Type",
                options=["GST", "VAT", "Other"],
                required=True
            )
        }
    )

    if st.button("Save Tax Changes"):
        try:
            # Handle deleted rows first
            deleted_ids = set(st.session_state.original_taxes_df.index) - set(edited_taxes_df.index)
            for tid in deleted_ids:
                success, msg = db.delete_entity('tax_config', tid)
                if not success:
                    st.error(f"Error deleting tax ID {tid}: {msg}")

            # Handle new and modified rows
            for idx, row in edited_taxes_df.iterrows():
                if pd.isna(idx):  # New row
                    success, msg = db.add_tax(
                        row['tax_name'],
                        row['tax_value'],
                        row['tax_type']
                    )
                    if not success:
                        st.error(f"Error adding tax {row['tax_name']}: {msg}")
                else:  # Existing row
                    original_row = st.session_state.original_taxes_df.loc[idx] if idx in st.session_state.original_taxes_df.index else None
                    if original_row is not None and (row != original_row).any():
                        success, msg = db.update_tax(
                            idx,
                            row['tax_name'],
                            row['tax_value'],
                            row['tax_type']
                        )
                        if not success:
                            st.error(f"Error updating tax {row['tax_name']}: {msg}")

            # Refresh data and update original copy
            refresh_data(force=True)
            st.session_state.original_taxes_df = st.session_state.taxes_df.copy()
            st.success("Tax changes saved successfully!")
            #st.rerun()

        except Exception as e:
            st.error(f"An error occurred while saving changes: {str(e)}")

def render_store_info_section():
    st.subheader("🏪 Store Info")
    store_info = db.get_store_info()
    with st.form("store_info_form"):
        name = st.text_input("Store Name", value=store_info['name'])
        address = st.text_area("Store Address", value=store_info['address'])
        vat_number = st.text_input("VAT Number", value=store_info['vat_number'])
        submitted = st.form_submit_button("Save Store Info")
        if submitted:
            success, msg = db.update_store_info(name, address, vat_number)
            if success:
                st.success(msg)
            else:
                st.error(msg)

def render_reports():
    # Back to main menu button
    if st.button("← Back to Main Menu", type="secondary"):
        st.session_state.current_page = None
        st.rerun()
    
    st.header("Reports")
    
    # Initialize report type if not set
    if 'selected_report' not in st.session_state:
        st.session_state.selected_report = None
    
    # Report type selection with buttons
    st.subheader("Select Report Type")
    
    # First row of buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Bill Report", use_container_width=True):
            st.session_state.selected_report = "Bill Report"
            st.rerun()
    with col2:
        if st.button("📦 Purchase Report", use_container_width=True):
            st.session_state.selected_report = "Purchase Report"
            st.rerun()
    with col3:
        if st.button("📊 Stock Report", use_container_width=True):
            st.session_state.selected_report = "Stock Report"
            st.rerun()
    
    # Second row of buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💰 Product Sales", use_container_width=True):
            st.session_state.selected_report = "Product Wise Sale Report"
            st.rerun()
    with col2:
        if st.button("🛒 Product Purchases", use_container_width=True):
            st.session_state.selected_report = "Product Wise Purchase Report"
            st.rerun()
    with col3:
        if st.button("🍾 Bulk Litre Report", use_container_width=True):
            st.session_state.selected_report = "Bulk Litre Report"
            st.rerun()
    
    # Use the selected report type
    report_type = st.session_state.selected_report

    if report_type in ["Bill Report", "Purchase Report", "Stock Report", "Product Wise Sale Report", "Product Wise Purchase Report", "Bulk Litre Report"]:
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Start Date", date.today().replace(day=1))
        end_date = col2.date_input("End Date", date.today())
        
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
    
    if st.button("Generate Report", key=f"btn_{report_type}"):
        if report_type == "Bill Report":
            report_df = db.get_bill_report(start_date_str, end_date_str)
            st.dataframe(report_df)
            st.download_button("Download as CSV", report_df.to_csv(index=False), "bill_report.csv")

        elif report_type == "Purchase Report":
            vendors_df = st.session_state.vendors_df
            vendor_list = {row['name']: row.name for _, row in vendors_df.iterrows()}
            vendor_list['All'] = 'All'
            selected_vendor = st.selectbox("Filter by Vendor", options=vendor_list.keys(), index=len(vendor_list)-1)
            vendor_id = vendor_list[selected_vendor]
            report_df = db.get_purchase_report(start_date_str, end_date_str, vendor_id)
            st.dataframe(report_df)
            st.download_button("Download as CSV", report_df.to_csv(index=False), "purchase_report.csv")

        elif report_type == "Stock Report":
            st.info(f"Stock report showing opening and closing stock for the period {start_date_str} to {end_date_str}")
            report_df = db.get_stock_report_with_dates(start_date_str, end_date_str)
            if not report_df.empty:
                st.dataframe(report_df)
                st.download_button("Download as CSV", report_df.to_csv(index=False), "stock_report.csv")
            else:
                st.warning("No stock data found for the selected period.")

        elif report_type == "Product Wise Sale Report":
            report_df = db.get_product_wise_sales(start_date_str, end_date_str)
            st.dataframe(report_df)
            st.bar_chart(report_df.set_index('Product Name')['Total Quantity Sold'])

        elif report_type == "Product Wise Purchase Report":
            report_df = db.get_product_wise_purchases(start_date_str, end_date_str)
            st.dataframe(report_df)
            st.bar_chart(report_df.set_index('Product Name')['Total Quantity Purchased'])

        elif report_type == "Bulk Litre Report":
            report_df = db.get_bulk_litre_report(start_date_str, end_date_str)
            st.dataframe(report_df)
            st.bar_chart(report_df.set_index('Product Name'))

def render_stock_management():
    # Back to main menu button
    if st.button("← Back to Main Menu", type="secondary"):
        st.session_state.current_page = None
        st.rerun()
    
    st.header("Stock Report")
    
    # Date selection for stock report
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", date.today().replace(day=1))
    end_date = col2.date_input("End Date", date.today())
    
    if st.button("Generate Stock Report"):
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        
        st.info(f"Stock report showing opening and closing stock for the period {start_date_str} to {end_date_str}")
        stock_df = db.get_stock_report_with_dates(start_date_str, end_date_str)
        
        if not stock_df.empty:
            st.dataframe(stock_df, use_container_width=True)
            st.download_button("Download as CSV", stock_df.to_csv(index=False), "stock_report.csv")
        else:
            st.warning("No stock data found for the selected period.")
    else:
        # Show current stock as default
        st.info("Click 'Generate Stock Report' to view opening and closing stock for selected dates.")
        current_stock_df = db.get_stock_report()
        st.dataframe(current_stock_df, use_container_width=True)

def render_bills_management():
    if st.button("← Back to Main Menu", type="secondary"):
        st.session_state.current_page = None
        st.rerun()

    st.header("🧾 Bills Management")

    # Date Range Selection
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", date.today().replace(day=1), key="bills_mgmt_start")
    end_date = col2.date_input("End Date", date.today(), key="bills_mgmt_end")

    # Create tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["📋 View Bills", "🖨️ Print Bills", "🤖 Auto-Generate Bills"])

    # Get bills data once
    bills_df = db.get_bill_report(start_date.isoformat(), end_date.isoformat())

    # Tab 1: View and Manage Bills
    with tab1:
        if bills_df.empty:
            st.info("No bills found for the selected period.")
        else:
            st.dataframe(bills_df, use_container_width=True)

            # Get unique bill IDs for the dropdown
            bill_ids = (bills_df['Bill No'].drop_duplicates() if 'Bill No' in bills_df else bills_df['id'].drop_duplicates()).sort_values(ascending=False)

            # Bill Details Section
            selected_bill = st.selectbox(
                "Select Bill to View/Edit/Delete",
                options=bill_ids,
                key="bill_selector"
            )

            if selected_bill:
                col1, col2, col3 = st.columns([2,1,1])
                with col1:
                    st.subheader(f"Bill #{selected_bill}")
                with col2:
                    if st.button("🖨️ Print Single Bill", key=f"print_single_{selected_bill}"):
                        generate_single_bill_html(selected_bill)
                with col3:
                    if 'pending_delete_bill_id' not in st.session_state:
                        st.session_state.pending_delete_bill_id = None
                    if st.button("🗑️ Delete Bill", type="secondary"):
                        st.session_state.pending_delete_bill_id = selected_bill
                        st.rerun()

                # Show bill details
                #bill, items_df = db.get_bill_by_id(selected_bill)
                #st.dataframe(items_df, use_container_width=True)
                # Show bill details with product names
                bill, items_df = db.get_bill_by_id(selected_bill)
                products_df = st.session_state.products_df

                # Create a new dataframe with product names
                display_df = items_df.copy()
                display_df['Product'] = display_df['product_id'].apply(lambda x: f"{products_df.loc[x]['name']} ({products_df.loc[x]['size']})")

                # Reorder and rename columns
                display_df = display_df[['Product', 'quantity', 'rate', 'amount', 'gst_percent', 'gst_amount']]
                display_df.columns = ['Product', 'Quantity', 'Rate', 'Amount', 'GST %', 'GST Amount']

                st.dataframe(display_df, use_container_width=True)

                # Delete confirmation
                if st.session_state.pending_delete_bill_id == selected_bill:
                    st.warning(f"Are you sure you want to delete Bill #{selected_bill}?")
                    col1, col2 = st.columns(2)
                    if col1.button("✅ Confirm Delete", type="secondary"):
                        success, msg = db.delete_bill(selected_bill)
                        if success:
                            st.success(msg)
                            st.session_state.pending_delete_bill_id = None
                            refresh_data(force=True)
                            st.rerun()
                        else:
                            st.error(msg)
                    if col2.button("❌ Cancel"):
                        st.session_state.pending_delete_bill_id = None
                        st.rerun()

    # Tab 2: Print Multiple Bills
    with tab2:
        if bills_df.empty:
            st.info("No bills found for the selected period.")
        else:
            st.info(f"Found {len(bills_df)} bills between {start_date} and {end_date}")
            if st.button("📄 Generate Printable Bills"):
                generate_multiple_bills_html(bills_df, start_date, end_date)

    # Tab 3: Auto-Generate Bills
    with tab3:
        st.subheader("Auto-Generate Bills for a Month")
        products_df = st.session_state.products_df

        # Create product list with stock information
        product_list = [
            f"{row['name']} - {row['size']} ({int(row['stock'])} left)"
            for idx, row in products_df.iterrows()
        ]

        col1, col2 = st.columns(2)
        with col1:
            selected_product_id = st.selectbox(
                "Select Product",
                options=products_df.index,
                format_func=lambda x: product_list[list(products_df.index).index(x)] if x in products_df.index else "",
                index=0 if not products_df.empty else None
            )
            total_quantity = st.number_input(
                "Total Quantity Sold in Month",
                min_value=1,
                value=1,
                step=1
            )

        with col2:
            st.info("This will automatically generate multiple bills for the selected product spread across the chosen date range.")
            if st.button("🤖 Generate Bills"):
                with st.spinner("Generating bills..."):
                    success, summary = db.auto_generate_bills_for_month(
                        start_date.isoformat(),
                        end_date.isoformat(),
                        selected_product_id,
                        total_quantity
                    )
                    if success:
                        st.success(f"Auto-generated bills for {product_list[list(products_df.index).index(selected_product_id)]}")
                        st.dataframe(pd.DataFrame(summary))
                    else:
                        st.error(summary)

# Helper functions for bill generation
def generate_single_bill_html(bill_id):
    bill, items_df = db.get_bill_by_id(bill_id)
    store_info = db.get_store_info()
    products_df = db.get_products()

    # Format items for receipt
    items_table = "".join([
        f"<tr><td>{products_df.loc[row['product_id']]['name']} ({products_df.loc[row['product_id']]['size']})</td><td>{row['quantity']}</td><td>{row['rate']:.2f}</td><td>{row['amount']:.2f}</td></tr>"
        for _, row in items_df.iterrows()
    ])

    receipt_html = f'''
    <div class="bill">
        <h3>{store_info['name']}</h3>
        <div class="store-info">{store_info['address']}<br/>VAT: {store_info['vat_number']}</div>
        <hr/>
        <div class="bill-info">Bill No: <b>{bill[0]}</b><br/>Date: {bill[1]}<br/>Customer: {bill[2]}<br/>Payment: {bill[3]}</div>
        <hr/>
        <table>
            <tr><th>Product</th><th>Qty</th><th>Rate</th><th>Amt</th></tr>
            {items_table}
        </table>
        <hr/>
        <div class="totals">
            Sub-Total: ₹ {bill[5]:,.2f}<br/>
            GST: ₹ {bill[6]:,.2f}<br/>
            Grand Total: <b>₹ {bill[8]:,.2f}</b>
        </div>
        <hr/>
        <div class="footer">Thank you for shopping!</div>
    </div>
    '''

    # Create downloadable HTML with styling
    html_content = create_styled_html([receipt_html])
    st.download_button(
        "📥 Download Bill",
        html_content,
        f"bill_{bill[0]}.html",
        "text/html"
    )

def generate_multiple_bills_html(bills_df, start_date, end_date):
    store_info = db.get_store_info()
    products_df = db.get_products()
    all_bills_html = []

    for _, bill_row in bills_df.iterrows():
        bill_id = bill_row['Bill No'] if 'Bill No' in bill_row else bill_row['id']
        bill, items_df = db.get_bill_by_id(bill_id)

        # Generate HTML for each bill
        items_table = "".join([
            f"<tr><td>{products_df.loc[row['product_id']]['name']} ({products_df.loc[row['product_id']]['size']})</td><td>{row['quantity']}</td><td>{row['rate']:.2f}</td><td>{row['amount']:.2f}</td></tr>"
            for _, row in items_df.iterrows()
        ])

        bill_html = f'''
        <div class="bill">
            <h3>{store_info['name']}</h3>
            <div class="store-info">{store_info['address']}<br/>VAT: {store_info['vat_number']}</div>
            <hr/>
            <div class="bill-info">Bill No: <b>{bill[0]}</b><br/>Date: {bill[1]}<br/>Customer: {bill[2]}<br/>Payment: {bill[3]}</div>
            <hr/>
            <table>
                <tr><th>Product</th><th>Qty</th><th>Rate</th><th>Amt</th></tr>
                {items_table}
            </table>
            <hr/>
            <div class="totals">
                Sub-Total: ₹ {bill[5]:,.2f}<br/>
                GST: ₹ {bill[6]:,.2f}<br/>
                Grand Total: <b>₹ {bill[8]:,.2f}</b>
            </div>
            <hr/>
            <div class="footer">Thank you for shopping!</div>
        </div>
        '''
        all_bills_html.append(bill_html)

    # Create downloadable HTML with styling
    html_content = create_styled_html(all_bills_html)
    st.download_button(
        "📥 Download All Bills",
        html_content,
        f"bills_{start_date}_to_{end_date}.html",
        "text/html"
    )

def create_styled_html(bills_html):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; padding: 20px; }}
            .bill {{
                font-family: monospace;
                max-width: 350px;
                margin: 20px auto;
                padding: 16px;
                border: 1px solid #ccc;
                background: #fff;
                color: black;
                page-break-after: always;
            }}
            h3 {{ text-align: center; margin-bottom: 4px; }}
            .store-info {{ text-align: center; font-size: 12px; }}
            hr {{ border: 1px solid #000; margin: 8px 0; }}
            .bill-info {{ font-size: 13px; }}
            table {{ width: 100%; font-size: 13px; border-collapse: collapse; }}
            th, td {{ padding: 2px 4px; text-align: left; }}
            .totals {{ font-size: 13px; }}
            .footer {{ text-align: center; font-size: 12px; margin-top: 8px; }}
            @media print {{
                @page {{ size: A4; margin: 0; }}
                .bill {{ border: none; }}
                body {{ margin: 0; }}
            }}
        </style>
    </head>
    <body>
        {''.join(bills_html)}
        <div style="text-align:center;font-size:12px;margin:20px 0;">
            To print: Press <b>Ctrl+P</b> (Windows) or <b>Cmd+P</b> (Mac)<br/>
            Set paper size to A4 and margins to None/Minimum
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    main() 