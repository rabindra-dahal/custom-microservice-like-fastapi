import uvicorn
from .framework import CustomMicroFramework
import asyncio # Standard library to allow us to simulate async delays


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

# Mock Database list
users_db = {
    "1": {"username": "Alice", "role": "Admin"},
    "2": {"username": "Bob", "role": "Developer"}
}

# 1. GET: Read a user profile
@app.get("/user")
def get_user(params, body):
    user_id = params.get("id", "1")
    user = users_db.get(user_id, {"error": "User not found"})
    return {"method_used": "GET", "data": user}

# 2. PUT: Update/Replace an existing user profile
"""
To test this endpoint, you can use the following curl command:
 curl -X PUT http://127.0.0.1:8000/user?id=2 -H "Content-Type: application/json" -d "{\"username\": \"Robert\"}"
"""
@app.put("/user")
def update_user(params, body):
    user_id = params.get("id")
    if user_id in users_db:
        # Overwrite database values with incoming JSON body values
        users_db[user_id]["username"] = body.get("username", users_db[user_id]["username"])
        users_db[user_id]["role"] = body.get("role", users_db[user_id]["role"])
        return {"method_used": "PUT", "status": "Updated", "updated_user": users_db[user_id]}
    return {"error": "User ID required or not found"}

# 3. DELETE: Wipe out a user account
"""To test this endpoint, you can use the following curl command:
 curl -X DELETE http://127.0.0.1:8000/user?id=2
"""
@app.delete("/user")
def delete_user(params, body):
    user_id = params.get("id")
    if user_id in users_db:
        deleted_profile = users_db.pop(user_id)
        return {"method_used": "DELETE", "status": "Removed", "profile": deleted_profile}
    return {"error": "User ID not found"}

#--------------------------------------------------
# Asynchronous vs Synchronous Route Examples
#-------------------------------------------------- 

# 1. Standard Synchronous Route (Normal function)
@app.get("/sync-data")
def get_sync_data(params, body):
    return {"mode": "synchronous", "message": "Fast response"}

# 2. Upgraded Asynchronous Route (Uses async def!)
@app.get("/async-data")
async def get_async_data(params, body):
    # Simulate a non-blocking database call or external API request fetch
    print("⏳ Starting background simulation wait...")
    await asyncio.sleep(2) # Pauses this request for 2 seconds without stopping the server!
    print("✅ Wait complete!")
    
    return {
        "mode": "asynchronous", 
        "message": "Data retrieved smoothly after 2 seconds"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
