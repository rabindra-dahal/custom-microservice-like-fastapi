import uvicorn
from .framework import CustomMicroFramework

app = CustomMicroFramework()

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

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
