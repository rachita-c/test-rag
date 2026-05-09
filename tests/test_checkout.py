from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Retail Checkout Service Running"


def test_add_to_cart():
    response = client.post("/cart/add", params={"item": "shoes"})
    assert response.status_code == 200
    assert "shoes" in response.json()["cart"]


def test_checkout_does_not_return_email():
    response = client.post("/checkout", params={"email": "test@example.com"})
    assert response.status_code == 200
    assert "test@example.com" not in response.text
