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

  customer_account: Mapped["CustomerAccount"] = db.relationship(back_populates="customer")
  orders: Mapped[List["Order"]] = db.relationship(back_populates="customer")



class CustomerAccount(Base):
  __tablename__ = "customer_accounts"
  account_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
  username: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
  password: Mapped[str] = mapped_column(db.String(255), nullable=False)
  customer_id: Mapped[int] = mapped_column(db.ForeignKey("customers.customer_id"))
  
  customer: Mapped["Customer"] = db.relationship(back_populates="customer_account")


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
  
  customer: Mapped["Customer"] = db.relationship(back_populates="orders")
  products: Mapped[List["Product"]]  = db.relationship(secondary=order_product_association)


class Product(Base):
  __tablename__ = "products"
  product_id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
  name: Mapped[str] = mapped_column(db.String(255), nullable=False)
  price: Mapped[float] = mapped_column(db.Float, nullable=False)



with app.app_context():
    db.create_all()


# Creating schema for models
class CustomerSchema(ma.Schema):
  customer_id = fields.Integer(dump_only=True)
  name = fields.String(required=True)
  email = fields.String(required=True)
  phone = fields.String(required=True)
  
  class Meta:
    fields = ('customer_id', 'name', 'email', 'phone')
  

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


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
def create_customer():
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
      
      



if __name__ == '__main__':
  app.run(debug=True)