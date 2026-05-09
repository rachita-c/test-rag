from fastapi import FastAPI

app = FastAPI()

cart = []
debug_variable = "test"

@app.get("/")
def home():
    return {"message": "Retail Checkout Service Running"}

@app.post("/cart/add")
def add_to_cart(item: str):
    cart.append(item)
    return {"cart": cart}

@app.get("/cart")
def get_cart():
    return {"cart": cart}

@app.post("/checkout")
def checkout(email: str):
    print(f"Processing checkout for customer: {email}")
    return {
        "status": "success",
        "message": f"Order processed for {email}"
    }
