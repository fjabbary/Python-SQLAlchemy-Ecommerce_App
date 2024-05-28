from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from marshmallow import fields, validate, ValidationError

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import select, delete

from typing import List

from variables import db_password
import datetime


app = Flask(__name__)
cors = CORS(app)


app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://root:{db_password}@localhost/e_commerce_app_db"

class Base(DeclarativeBase):
  pass


db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)


class Customer(Base):
  __tablename__ = 'customers'
  
  customer_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
  name: Mapped[str] = mapped_column(db.String(255))
  email: Mapped[str] = mapped_column(db.String(255), unique=True)
  phone: Mapped[str] = mapped_column(db.String(15))

  customer_account: Mapped["CustomerAccount"] = db.relationship("CustomerAccount", back_populates="customer", uselist=False)
  orders: Mapped[List["Order"]] = db.relationship("Order", back_populates="customer")


class CustomerAccount(Base):
  __tablename__ = "customer_accounts"
  account_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
  username: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
  password: Mapped[str] = mapped_column(db.String(255), nullable=False)
  customer_id: Mapped[int] = mapped_column(db.ForeignKey("customers.customer_id"), unique=True)
  
  customer: Mapped["Customer"] = db.relationship("Customer", back_populates="customer_account")


order_product_association = db.Table(
    'order_product', Base.metadata,
    db.Column('order_id', db.ForeignKey('orders.order_id'), primary_key=True),
    db.Column('product_id', db.ForeignKey('products.product_id'), primary_key=True)
)

class Order(Base):
  __tablename__ = "orders"
  order_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
  date: Mapped[datetime.date] = mapped_column(db.Date, nullable=False)
  customer_id: Mapped[int] = mapped_column(db.ForeignKey("customers.customer_id"))
  status: Mapped[str] = mapped_column(db.String(255), default="pending")
  
  customer: Mapped["Customer"] = db.relationship(back_populates="orders")
  products: Mapped[List["Product"]]  = db.relationship(secondary=order_product_association)


class Product(Base):
  __tablename__ = "products"
  product_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
  name: Mapped[str] = mapped_column(db.String(255), nullable=False)
  price: Mapped[float] = mapped_column(db.Float, nullable=False)
  
  orders = db.relationship("Order", secondary=order_product_association, back_populates="products")
  inventory: Mapped["Inventory"] = db.relationship("Inventory", back_populates="product", uselist=False)
  
  
class Inventory(Base):
  __tablename__ = "inventory"
  inventory_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
  product_id: Mapped[int] = mapped_column(db.ForeignKey("products.product_id"), nullable=False, unique=True)
  quantity: Mapped[int] = mapped_column(db.Integer, nullable=False)
    
  product: Mapped["Product"] = db.relationship("Product", back_populates="inventory")



with app.app_context():
    db.create_all()
    
# =========================================================
# ======================// Schemas //======================
# =========================================================

class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=False)
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ("product_id", "name", "price")

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
    
class OrderSchema(ma.Schema):
    order_id = fields.Integer(required=False)
    customer_id = fields.Integer(required=True)
    date = fields.Date(required=True)
    status = fields.String()    
    product_id = fields.List(fields.Integer())
    products = fields.Nested(ProductSchema, many=True)

    class Meta:
        fields = ("order_id", "customer_id", "date", "status", 'products', 'product_id')

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


class AccountSchema(ma.Schema):
    account_id = fields.Integer(dump_only=True)
    username = fields.String(required=True)
    password = fields.String(required=True)
    customer_id = fields.Integer(required=True)
  
    class Meta:
      fields = ('account_id', 'username', 'password', 'customer_id')
  

account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)   

# Creating schema for models
class CustomerSchema(ma.Schema):
  customer_id = fields.Integer(dump_only=True)
  name = fields.String(required=True)
  email = fields.String(required=True)
  phone = fields.String(required=True)
  orders = fields.Nested(OrderSchema, many=True)
  customer_account = fields.Nested(AccountSchema)

  class Meta:
    fields = ('customer_id', 'name', 'email', 'phone', 'orders', 'customer_account')
  

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


class InventorySchema(ma.Schema):
  inventory_id = fields.Integer(required=False)
  product_id = fields.Integer(required=True, unique=True)
  quantity = fields.Integer(required=True, validate=validate.Range(min=0))
  
  class Meta:
    fields = ('inventory_id', 'product_id', 'quantity')

inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)   



# =========================================================
# ===================// Customer CRUD //===================
# =========================================================

# API Routes
# Get all customers
@app.route('/customers', methods=['GET'])
def get_customers():
  query = select(Customer)
  customers = db.session.execute(query).scalars().all()
  
  print(customers)
  return customers_schema.jsonify(customers)

# Get one customer
@app.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
  query = select(Customer).filter(Customer.customer_id == customer_id)
  customer = db.session.execute(query).scalars().first()
  
  print(customer)
  return customer_schema.jsonify(customer)

# Add new customer
@app.route('/customers', methods=['POST'])
def add_customer():
    try:
      customer_data = customer_schema.load(request.json)
      
    except ValidationError as err:  
      return jsonify(err.messages), 400

    with Session(db.engine) as session:
        with session.begin():
          name = customer_data['name']
          email = customer_data['email']
          phone = customer_data['phone']
          
          new_customer = Customer(name=name, email=email, phone=phone)
          session.add(new_customer)
          session.commit()
    
    return jsonify({"Message": "New customer added successfully"})


# Update customer
@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
  with Session(db.engine) as session:
    with session.begin():
        query = select(Customer).filter(Customer.customer_id == customer_id)
        customer = session.execute(query).scalars().first()

        if customer is None:
          return jsonify({"Message": "Customer not found"}), 404
        
        try:
          customer_data = customer_schema.load(request.json)
          print(customer)
          print(customer_data)
          
        except ValidationError as err:
          return jsonify(err.messages), 400
        
        for field, value in customer_data.items():
          setattr(customer, field, value)

        session.commit()
        return jsonify({"Message": "Customer updated successfully"}), 200


@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    query = delete(Customer).where(Customer.customer_id == customer_id)
    with db.session.begin():
      result = db.session.execute(query)
      
      if result.rowcount == 0:
        return jsonify({"Message": "Customer not found"}), 404
      
      return jsonify({"Message": "Customer removed successfully"})
    
      
# =============================================================================
# =======================// Customer Accounts CRUD  //=========================
# =============================================================================          
      
@app.route('/accounts', methods=['GET'])
def get_accounts():
  query = select(CustomerAccount)
  accounts = db.session.execute(query).scalars().all()
  return accounts_schema.jsonify(accounts)     
      
      
@app.route('/accounts', methods=['POST'])
def add_account():
    try:
      account_data = account_schema.load(request.json)
      
    except ValidationError as err:  
      return jsonify(err.messages), 400
    
    try:
      with Session(db.engine) as session:
          with session.begin():
            username = account_data['username']
            password = account_data['password']
            customer_id = account_data['customer_id']
            
            new_account = CustomerAccount(username=username, password=password, customer_id=customer_id)
            session.add(new_account)
            session.commit()
            
    except:
      return jsonify({"Message": "Error adding account - Each customer can have one account"})
    
    return jsonify({"Message": "New Account added successfully"})     
      
      
      
# Update customer
@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
  with Session(db.engine) as session:
    with session.begin():
        query = select(CustomerAccount).filter(CustomerAccount.account_id == account_id)
        account = session.execute(query).scalars().first()

        if account is None:
          return jsonify({"Message": "Account not found"}), 404
        
        try:
          account_data = account_schema.load(request.json)
         
          
        except ValidationError as err:
          return jsonify(err.messages), 400
        
        for field, value in account_data.items():
          setattr(account, field, value)

        session.commit()
        return jsonify({"Message": "Account updated successfully"}), 200


@app.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    query = delete(CustomerAccount).where(CustomerAccount.account_id == account_id)
    with db.session.begin():
      result = db.session.execute(query)
      
      if result.rowcount == 0:
        return jsonify({"Message": "Account not found"}), 404
      
      return jsonify({"Message": "Account removed successfully"})
        
      
# =============================================================================
# ============================// PRODCUTS CRUD  //=============================
# =============================================================================

@app.route('/products', methods=["POST"])
def add_product():
    try:
        product_data = product_schema.load(request.json)
        
    except ValidationError as err:
        return jsonify(err.messages), 400

    with Session(db.engine) as session:
        with session.begin():
            # new_product = Product(**product_data)
            new_product = Product(name=product_data['name'], price=product_data['price'])
            session.add(new_product)
            session.commit()

    return jsonify({"Message": "New product successfully added!"}), 201 #new resource has been created



@app.route('/products', methods=["GET"])
def get_products():
    query = select(Product) #SELECT * FROM Product
    result = db.session.execute(query).scalars()
    products = result.all()

    return products_schema.jsonify(products)


# get product by name
@app.route("/products/by-name", methods=["GET"])
def get_product_by_name():
    name = request.args.get("name")
    search = f"%{name}%" #% is a wildcard
    # use % with LIKE to find partial matches
    query = select(Product).where(Product.name.like(search)).order_by(Product.price.asc())

    products = db.session.execute(query).scalars().all()

    return products_schema.jsonify(products)


# Get one product
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
  query = select(Product).filter(Product.product_id == product_id)
  product = db.session.execute(query).scalars().first()
  
  print(product)
  return product_schema.jsonify(product)


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Product).filter(Product.product_id == product_id)
            result = session.execute(query).scalar() # the same as scalars().first() - first result in the scalars object
            
            if result is None:
                return jsonify({"error": "Product not found!"}), 404
            product = result
            try:
                product_data = product_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            
            for field, value in product_data.items():
                setattr(product, field, value)

            session.commit()
            return jsonify({"message": "Product details succesfully updated!"}), 200       



@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    delete_statement = delete(Product).where(Product.product_id==product_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error" "Product not found"}), 404
        
        return jsonify({"message": "Product successfully deleted!"}), 200
      
      
# =============================================================================
# =======================// PRODCUTS INVENTORY CRUD  //========================
# =============================================================================     

@app.route('/inventories', methods=["POST"])
def add_inventory():
    try:
        inventory_data = inventory_schema.load(request.json)
        
    except ValidationError as err:
        return jsonify(err.messages), 400

    try:
      with Session(db.engine) as session:
          with session.begin():
              # new_product = Product(**product_data)
              new_inventory = Inventory(product_id=inventory_data['product_id'], quantity=inventory_data['quantity'])
              session.add(new_inventory)
              session.commit()
    except:
      return jsonify({"error": "Failed to add inventory"}), 404

    return jsonify({"Message": "New inventory successfully added!"}), 201 #new resource has been created



@app.route('/inventories', methods=["GET"])
def get_inventories():
    query = select(Inventory)
    result = db.session.execute(query).scalars()
    inventories = result.all()

    return inventories_schema.jsonify(inventories)   
   
   

@app.route("/inventories/<int:inventory_id>", methods=["PUT"])
def update_inventory(inventory_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Inventory).filter(Inventory.inventory_id == inventory_id)
            result = session.execute(query).scalar() # the same as scalars().first() - first result in the scalars object
            
            if result is None:
                return jsonify({"error": "Inventory not found!"}), 404
            inventory = result
            try:
                inventory_data = inventory_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            
            for field, value in inventory_data.items():
                setattr(inventory, field, value)

            session.commit()
            return jsonify({"message": "Inventory details succesfully updated!"}), 200       



@app.route("/inventories/<int:inventory_id>", methods=["DELETE"])
def delete_inventory(inventory_id):
    delete_statement = delete(Inventory).where(Inventory.inventory_id == inventory_id)
    try:
        with db.session.begin():
            result = db.session.execute(delete_statement)
            if result.rowcount == 0:
                return jsonify({"error" "Inventory not found"}), 404
            
            return jsonify({"message": "Inventory successfully deleted!"}), 200 
    except:
      return jsonify({"error": "Failed to delete inventory"}), 404

# ============================================================
# ===================// ORDERS CRUD //========================
# ============================================================

@app.route("/orders", methods = ["POST"])
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session:
        with session.begin():
            new_order = Order(customer_id=order_data['customer_id'], date = order_data['date'])

            session.add(new_order)
            session.commit()

    return jsonify({"message": "New order succesfully added!"}), 201



@app.route("/orders", methods=["GET"])
def get_orders():
    query = select(Order)
    result = db.session.execute(query).scalars()
    return orders_schema.jsonify(result)


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
  query = select(Order).filter(Order.order_id == order_id)
  order = db.session.execute(query).scalars().first()
  
  return order_schema.jsonify(order)


@app.route('/orders/<int:order_id>', methods=["PUT"])
def update_order(order_id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Order).filter(Order.order_id==order_id)
            result = session.execute(query).scalar() #first result object
            if result is None:
                return jsonify({"message": "Product Not Found"}), 404
            order = result
            try:
                order_data = order_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            
            for field, value in order_data.items():
                setattr(order, field, value)

            session.commit()
            return jsonify({"Message": "Order was successfully updated! "})



@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    delete_statement = delete(Order).where(Order.order_id==order_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error": "Order not found" }), 404
        return jsonify({"message": "Order removed successfully"}), 200


# ===================================================== 
# ===================================================== 
# ===================================================== 

@app.route('/orders/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
  try:
      with db.session.begin():
        query = select(Order).filter(Order.order_id == order_id)
        result = db.session.execute(query).scalars().first() #first result object
        if result is None:
          return jsonify({"message": "Order Not Found"}), 404
        order = result
        print(order.status)
        if order.status in ['pending', 'processing']:
          order.status = "cancelled"
          db.session.commit()
        return jsonify({"message": "Order was successfully cancelled!"}), 200
  except:
    return jsonify({"message": "Failed to cancel order"}), 404
  



@app.route('/orders/history/<int:customer_id>', methods=['GET'])
def get_order_history(customer_id):
  try:
    with db.session.begin():
      query = select(Order).filter(Order.customer_id == customer_id)
      result = db.session.execute(query).scalars().all() 
      if result is None:
        return jsonify({"message": "No orders found"}), 404
      
      return orders_schema.jsonify(result)
    
  except:
    return jsonify({"message": "Failed to get order history"}), 404
















if __name__ == '__main__':
  app.run(debug=True)