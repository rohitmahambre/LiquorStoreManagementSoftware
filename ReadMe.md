Liquor Store Management System
Overview
The Liquor Store Management System is a comprehensive application designed to manage the operations of a liquor store. It includes features for managing products, customers, vendors, taxes, purchase orders, billing, stock, and reporting. The system is built using Python and SQLite, with a user interface powered by Streamlit.  <hr></hr>
Features
1. Product Management
   Add, edit, and delete products.
   Manage product details such as name, type, size, purchase price, selling price, category, and VAT category.
   Track product stock levels.
2. Customer Management
   Add, edit, and delete customer details.
   Manage customer information such as name, address, mobile number, and email.
3. Vendor Management
   Add, edit, and delete vendor details.
   Manage vendor information such as name, address, mobile number, and VAT number.
4. Tax Configuration
   Add, edit, and delete tax rules.
   Configure tax types such as GST, VAT, and others.
5. Purchase Order Management
   Create and edit purchase orders.
   Manage purchase order items, including product details, quantity, rate, and taxes.
   Automatically update product stock upon purchase order creation.
6. Billing
   Create and manage bills for customers.
   Auto-generate bills for a product over a specified date range.
   Print and download bills in HTML format.
7. Stock Management
   View current stock levels.
   Generate stock reports with opening and closing stock for a specified date range.
8. Reports
   Generate various reports, including:
   Bill Report
   Purchase Report
   Stock Report
   Product-Wise Sales Report
   Product-Wise Purchase Report
   Bulk Litre Report
   Download reports in CSV format.
9. Store Information
   Manage store details such as name, address, and VAT number.
<hr></hr>
Installation
Prerequisites
Python 3.8 or higher
SQLite (pre-installed with Python)
Streamlit library
Steps
Clone the repository:  
git clone <repository-url>
cd liquor-store-management
Install dependencies:  
pip install -r requirements.txt
Initialize the database:  
python database.py
Run the application:  
streamlit run app.py
<hr></hr>
File Structure
app.py: Main application file for the Streamlit interface.
database.py: Handles database creation and schema setup.
db_functions.py: Contains database interaction functions.
requirements.txt: Lists all required Python libraries.
<hr></hr>
Database Schema
The system uses SQLite as the database. Key tables include:  
products: Stores product details.
customers: Stores customer details.
vendors: Stores vendor details.
tax_config: Stores tax rules.
purchase_orders and purchase_order_items: Manage purchase orders and their items.
bills and bill_items: Manage bills and their items.
store_info: Stores store details.
<hr></hr>
Usage
Start the Application: Run the Streamlit app and navigate through the menu to access different features.
Manage Data: Use the Master Data Management section to add or edit products, customers, vendors, and taxes.
Create Purchase Orders: Add purchase orders to update stock levels.
Generate Bills: Create bills for customers and manage stock accordingly.
View Reports: Generate and download reports for analysis.
<hr></hr>
Key Technologies
Frontend: Streamlit
Backend: Python
Database: SQLite
Libraries: Pandas, NumPy, Streamlit
<hr></hr>
License
This project is licensed under the MIT License. See the LICENSE file for details.  <hr></hr>
Acknowledgments
Special thanks to the contributors and open-source libraries that made this project possible