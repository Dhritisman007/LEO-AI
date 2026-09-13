from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str

class Product(BaseModel):
    id: int
    name: str
    price: float