## Features

- CRUD operations for customers, customer accounts, products, inventories, and orders.
- Inventory restocking when quantity falls below a certain threshold.
- Order management including order cancellation and order history retrieval.
- Input validation for customer details using regular expressions.

## Tech Stack

- Python
- Flask
- SQLAlchemy
- Marshmallow
- MySQL


## Setup Instructions

1. Clone the repository:

```bash
git clone https://github.com/fjabbary/Python-SQLAlchemy-Ecommerce_App
cd ecommerce-app
```

2. Create and activate a virtual environment:
python -m venv venv
Mac: source venv/bin/activate  AND  On Windows, use `venv\Scripts\activate`

3.Install the required packages:
pip install -r requirements.txt

4.Set up the MySQL database and update the variables.py file with your database credentials:
# variables.py
db_password = 'your_db_password'


API Endpoints

## Customers
Get all customers: GET /customers
Get a customer by ID: GET /customers/<int:customer_id>
Add a new customer: POST /customers
Update a customer: PUT /customers/<int:customer_id>
Delete a customer: DELETE /customers/<int:customer_id>

## Customer Accounts
Get all accounts: GET /accounts
Add a new account: POST /accounts
Update an account: PUT /accounts/<int:account_id>
Delete an account: DELETE /accounts/<int:account_id>

## Products
Get all products: GET /products
Get products by name: GET /products/by-name?name=<product_name>
Get a product by ID: GET /products/<int:product_id>
Add a new product: POST /products
Update a product: PUT /products/<int:product_id>
Delete a product: DELETE /products/<int:product_id>

## Inventories
Get all inventories: GET /inventories
Add a new inventory: POST /inventories
Update an inventory: PUT /inventories/<int:inventory_id>
Delete an inventory: DELETE /inventories/<int:inventory_id>
Restock an inventory: POST /inventories/restock/<int:product_id>

## Orders
Get all orders: GET /orders
Get an order by ID: GET /orders/<int:order_id>
Add a new order: POST /orders
Update an order: PUT /orders/<int:order_id>
Delete an order: DELETE /orders/<int:order_id>
Cancel an order: POST /orders/cancel/<int:order_id>
Get order history for a customer: GET /orders/history/<int:customer_id>

## Validation
Customer Name: Minimum 3 characters, alphanumeric.
Customer Email: Valid email format.
Customer Phone: Valid phone number format (e.g., 123-456-7890 or (123) 456-7890 or 1234567890).