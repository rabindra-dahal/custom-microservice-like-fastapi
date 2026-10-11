import uvicorn
from .framework import CustomMicroFramework
from .responses import JSONResponse, HTMLResponse, RedirectResponse

app = CustomMicroFramework()

# 1. Custom JSONResponse with Custom Headers and Status Code
@app.get("/api/items")
def get_custom_json(params, body, path_params):
    return JSONResponse(
        content={"items": ["Framework", "Engine", "Router"]},
        status_code=201,
        headers=[("X-Custom-Framework-Header", "Micro-Engine-v3")]
    )

# 2. HTMLResponse rendering direct template code
@app.get("/welcome")
def get_html_page(params, body, path_params):
    template = """
    <html>
        <head><title>Micro Framework</title></head>
        <body style="font-family: sans-serif; padding: 40px; background-color: #f4f6f9;">
            <h1 style="color: #2c3e50;">Welcome to the Custom Layer!</h1>
            <p>This page is natively rendered using <strong>HTMLResponse</strong>.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=template)

# 3. RedirectResponse sending users elsewhere
@app.get("/legacy-route")
def old_route(params, body, path_params):
    # Send a temporary redirect to the welcome page
    return RedirectResponse(url="/welcome", status_code=307)

# 4. Fallback backwards compatibility checking (returns raw dict)
@app.get("/fallback")
def standard_fallback(params, body, path_params):
    return {"message": "Automatically wrapped inside a JSONResponse!"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)



# import uvicorn
# from .framework import CustomMicroFramework
# import asyncio # Standard library to allow us to simulate async delays
# import time # Standard library to measure performance of requests
# from .dependencies import Depends


# app = CustomMicroFramework()

# # Simulated database state wrapper
# class ManagedDatabasePool:
#     def __init__(self):
#         self.connected = False
#         self.pool_size = 0

#     async def connect(self):
#         print("[Lifecycle] Opening connection pool cluster...")
#         await asyncio.sleep(0.1)  # Simulate network latency
#         self.connected = True
#         self.pool_size = 10
#         print("[Lifecycle] Database connection pool is READY.")

#     async def disconnect(self):
#         print("[Lifecycle] Draining connection pool safely...")
#         await asyncio.sleep(0.1)
#         self.connected = False
#         self.pool_size = 0
#         print("[Lifecycle] Database disconnected cleanly.")

# # Single global resource reference
# db_resource = ManagedDatabasePool()

# # --- REGISTER LIFECYCLE EVENT HOOKS ---

# @app.on_event("startup")
# async def startup_event():
#     """Triggered by the ASGI server immediately upon application boot."""
#     await db_resource.connect()

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Triggered by the ASGI server when receiving SIGINT/termination signals."""
#     await db_resource.disconnect()

# # --- DEPENDENCY LAYER ---
# def get_db():
#     if not db_resource.connected:
#         raise RuntimeError("Database pool accessed before initialization!")
#     return db_resource

# # --- TEST ENDPOINT ---
# @app.get("/health")
# def health_check(params, body, path_params, db = Depends(get_db)):
#     """Validates the live status of the injected framework resource."""
#     return {
#         "status": "healthy",
#         "database_connected": db.connected,
#         "active_connections": db.pool_size
#     }

# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)




# app = CustomMicroFramework()

# # Create a clean domain exception for the business logic
# class UserNotFoundError(Exception):
#     def __init__(self, message="Target account does not exist"):
#         self.message = message
#         super().__init__(self.message)

# # 🛠️ 1. Register Exception Catcher for UserNotFoundError
# @app.exception_handler(UserNotFoundError)
# def handle_user_missing(error):
#     # Custom error handlers return a tuple: (HTTP_STATUS_CODE, JSON_DICTIONARY)
#     return 404, {"error": "Not Found", "message": str(error)}

# # 🛠️ 2. Register Exception Catcher for standard Python ValueErrors
# @app.exception_handler(ValueError)
# def handle_invalid_value(error):
#     return 400, {"error": "Bad Request", "message": f"Validation Error: {str(error)}"}


# # 🛡️ Global Security Middleware Interceptor
# @app.middleware()
# async def add_security_headers(scope, call_next):
#     # --- BEFORE ROUTE EXECUTES ---
#     start_time = time.time()
    
#     # Pass control down to the next middleware or the core router endpoint
#     status, headers, response_bytes = await call_next(scope)
    
#     # --- AFTER ROUTE EXECUTES (Response Interception) ---
#     # Append modern production security headers to the outgoing list
#     headers.append((b'x-frame-options', b'DENY'))                          # Prevents clickjacking attacks
#     headers.append((b'x-content-type-options', b'nosniff'))                # Forces browser to adhere to content-type
#     headers.append((b'x-xss-protection', b'1; mode=block'))                # Blocks XSS script loading cross-site
#     headers.append((b'strict-transport-security', b'max-age=31536000'))    # Enforces strict HTTPS usage
    
#     duration = (time.time() - start_time) * 1000
#     print(f"⏱️ [PERFORMANCE LOG] Request processed in {duration:.2f}ms")
    
#     return status, headers, response_bytes

# # Simple endpoint to test the framework output
# @app.get("/secure-data")
# def get_secure_data(params, body):
#     return {"status": "success", "message": "Check your network headers! They are now locked down."}


# # Test Route 1: Normal GET request reading URL params
# @app.get("/hello")
# def say_hello(params, body):
#     user_name = params.get('name', 'Guest')
#     return {"message": f"Hello, {user_name}!"}

# # Test Route 2: POST request reading JSON inputs
# @app.post("/create-user")
# def register_user(params, body):
#     username = body.get("username", "unknown_user")
#     user_age = body.get("age", 0)
#     return {
#         "status": "Account created successfully",
#         "saved_profile": {"username": username, "age": user_age}
#     }

# # Test Route 3: Broken route to test the Error Catcher
# @app.get("/broken")
# def break_things(params, body):
#     result = 10 / 0 
#     return {"result": result}

# # Mock Database list
# users_db = {
#     "1": {"username": "Alice", "role": "Admin"},
#     "2": {"username": "Bob", "role": "Developer"}
# }

# # 1. GET: Read a user profile
# @app.get("/user")
# def get_user(params, body):
#     user_id = params.get("id", "1")
#     user = users_db.get(user_id, {"error": "User not found"})
#     return {"method_used": "GET", "data": user}

# # 2. PUT: Update/Replace an existing user profile
# """
# To test this endpoint, you can use the following curl command:
#  curl -X PUT http://127.0.0.1:8000/user?id=2 -H "Content-Type: application/json" -d "{\"username\": \"Robert\"}"
# """
# @app.put("/user")
# def update_user(params, body):
#     user_id = params.get("id")
#     if user_id in users_db:
#         # Overwrite database values with incoming JSON body values
#         users_db[user_id]["username"] = body.get("username", users_db[user_id]["username"])
#         users_db[user_id]["role"] = body.get("role", users_db[user_id]["role"])
#         return {"method_used": "PUT", "status": "Updated", "updated_user": users_db[user_id]}
#     return {"error": "User ID required or not found"}

# # 3. DELETE: Wipe out a user account
# """To test this endpoint, you can use the following curl command:
#  curl -X DELETE http://127.0.0.1:8000/user?id=2
# """
# @app.delete("/user")
# def delete_user(params, body):
#     user_id = params.get("id")
#     if user_id in users_db:
#         deleted_profile = users_db.pop(user_id)
#         return {"method_used": "DELETE", "status": "Removed", "profile": deleted_profile}
#     return {"error": "User ID not found"}

# #--------------------------------------------------
# # Asynchronous vs Synchronous Route Examples
# #-------------------------------------------------- 

# # 1. Standard Synchronous Route (Normal function)
# @app.get("/sync-data")
# def get_sync_data(params, body):
#     return {"mode": "synchronous", "message": "Fast response"}

# # 2. Upgraded Asynchronous Route (Uses async def!)
# @app.get("/async-data")
# async def get_async_data(params, body):
#     # Simulate a non-blocking database call or external API request fetch
#     print("⏳ Starting background simulation wait...")
#     await asyncio.sleep(2) # Pauses this request for 2 seconds without stopping the server!
#     print("✅ Wait complete!")
    
#     return {
#         "mode": "asynchronous", 
#         "message": "Data retrieved smoothly after 2 seconds"
#     }

# # --- ROUTES FOR TESTING ---

# # Simulated database check that crashes intentionally if ID is out of range
# @app.get("/find-user")
# def find_user(params, body):
#     user_id = params.get("id", "")
    
#     if user_id == "99":
#         raise UserNotFoundError("User account #99 has been deactivated or never existed.")
        
#     return {"status": "success", "user_id": user_id}

# # Route that forces a standard python system validation ValueError crash
# @app.get("/parse-age")
# def parse_age(params, body):
#     age_str = params.get("age", "")
    
#     # Int conversion will automatically raise a ValueError if age is not a number (e.g. "abc")
#     age = int(age_str)
    
#     return {"status": "success", "validated_age": age}


# # Test Route 1: Simple dynamic route with single argument
# @app.get("/users/{user_id}")
# def get_user_profile(params, body, path_params):
#     """
#     Fetch user summary info using inline route properties.
#     """
#     extracted_id = path_params.get("user_id")
#     return {
#         "message": f"Successfully pulled metadata for profile user #{extracted_id}",
#         "extracted_path_variables": path_params,
#         "additional_queries": params
#     }

# # Test Route 2: Advanced complex multi-parameter matching
# @app.get("/stores/{store_id}/items/{item_sku}")
# def get_store_inventory(params, body, path_params):
#     """
#     Locate specific catalog entries across distributed local storage centers.
#     """
#     return {
#         "status": "synchronized",
#         "lookup_parameters": path_params
#     }




# # Mock Database Connection Pool class
# class DatabaseConnectionPool:
#     def __init__(self):
#         self.state = "connected_to_cluster_v2"

#     def fetch_all(self, query):
#         return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

# # Initialize a global pool instance
# db_pool = DatabaseConnectionPool()

# # Dependency Provider function
# def get_db_session():
#     """
#     Simulates checking or resolving a clean pool connection context.
#     """
#     print("[DI Log] Resolving Database connection pool instance...")
#     return db_pool


# # --- DATABASE POOL MOCK ---
# class DatabaseConnection:
#     def __init__(self):
#         self.scope_id = "db_pool_active"
#     def find_user(self, user_name):
#         return {"username": user_name, "role": "admin" if user_name == "admin" else "guest"}

# def get_db_session():
#     print("[DI] Resolving Database Session...")
#     return DatabaseConnection()

# # --- NESTED SUB-DEPENDENCY ---
# # This dependency requires the database dependency to be resolved first!
# def get_current_user(db = Depends(get_db_session)):
#     print("[DI] Resolving Current User using Injected DB...")
#     # Hardcoded simulation mimicking looking up a credential token
#     return db.find_user("admin")


# # --- ENDPOINTS USING INJECTED DEPENDENCIES ---

# @app.get("/users")
# def list_users(params, body, path_params, db = Depends(get_db_session)):
#     """
#     Fetch system profiles leveraging an isolated, injected database engine.
#     """
#     # Use the injected dependency directly!
#     records = db.fetch_all("SELECT * FROM users")
#     return {
#         "status": "success",
#         "pool_status": db.state,
#         "data": records
#     }

# @app.get("/users/{user_id}")
# async def get_single_user(params, body, path_params, db = Depends(get_db_session)):
#     """
#     Pull granular profile targets via the dependency pool layer.
#     """
#     uid = path_params.get("user_id")
#     return {
#         "user_id": uid,
#         "database_reference": id(db),
#         "note": "Dependency resolved successfully!"
#     }


# # --- VERIFICATION ENDPOINTS ---

# # 1. Verification of Sub-Dependencies
# @app.get("/secure/dashboard")
# def dashboard(params, body, path_params, current_user = Depends(get_current_user)):
#     """
#     Endpoint protected by a multi-layered sub-dependency tree.
#     """
#     return {
#         "status": "authenticated",
#         "user_profile": current_user
#     }

# # 2. Verification of Type Casting (Int and Float)
# @app.get("/items/{item_id:int}/tax/{rate:float}")
# def calculated_item(params, body, path_params):
#     """
#     Verifies automatic route parameter injection and runtime type casting.
#     """
#     item_id = path_params["item_id"]
#     rate = path_params["rate"]
    
#     return {
#         "raw_path_params": path_params,
#         "item_id_type": str(type(item_id)),
#         "rate_type": str(type(rate)),
#         "computed_math_test": item_id * rate  # Will crash if strings aren't casted correctly!
#     }


# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


