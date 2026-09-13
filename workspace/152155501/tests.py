import pytest
from models import User, Product

def test_user_model():
    user = User(id=1, username="testuser", email="test@example.com")
    assert user.id == 1
    assert user.username == "testuser"
    assert user.email == "test@example.com"

def test_product_model():
    product = Product(id=1, name="Laptop", price=999.99)
    assert product.id == 1
    assert product.name == "Laptop"
    assert product.price == 999.99

def test_invalid_user():
    with pytest.raises(Exception):
        User(id="not_an_int", username="test", email="test@test.com")