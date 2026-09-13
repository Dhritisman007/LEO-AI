from fastapi import FastAPI
from models import User, Product
from typing import List

app = FastAPI()

users = []
products = []

@app.post("/users/")
def create_user(user: User):
    users.append(user)
    return user

@app.get("/users/", response_model=List[User])
def get_users():
    return users

@app.post("/products/")
def create_product(product: Product):
    products.append(product)
    return product

@app.get("/products/", response_model=List[Product])
def get_products():
    return products