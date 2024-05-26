from flask import Flask
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
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










if __name__ == '__main__':
  app.run(debug=True)