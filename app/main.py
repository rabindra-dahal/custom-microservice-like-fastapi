import uvicorn

# Import your custom engine class from your other file!
from .framework import CustomMicroFramework


# Create the application engine
app = CustomMicroFramework()

# Test Route 1: Normal GET request reading URL params
@app.get("/hello")
def say_hello(params, body):
    user_name = params.get('name', 'Guest')
    return {"message": f"Hello, {user_name}!"}

# Test Route 2: POST request reading JSON inputs
@app.post("/create-user")
def register_user(params, body):
    username = body.get("username", "unknown_user")
    user_age = body.get("age", 0)
    return {
        "status": "Account created successfully",
        "saved_profile": {"username": username, "age": user_age}
    }

# Test Route 3: Broken route to test the Error Catcher
@app.get("/broken")
def break_things(params, body):
    result = 10 / 0 
    return {"result": result}

if __name__ == "__main__":
    # CRITICAL: We point Uvicorn to "main:app" because the file name is main.py
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
