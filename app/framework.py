import json

class CustomMicroFramework:
    def __init__(self):
        # The master routing book. It stores paths and their HTTP methods.
        # Example layout: {"/user": {"GET": get_user_func, "PUT": update_user_func}}
        self.routes = {}

    # The master decorator function that handles all routing logic underneath
    def route(self, path, method="GET"):
        def decorator(func):
            # If this is the first time registering this path, make a new dictionary for it
            if path not in self.routes:
                self.routes[path] = {}
            # Save the function under its specific HTTP method (forced to uppercase)
            self.routes[path][method.upper()] = func
            return func
        return decorator

    # Quick shortcut helpers that mimic FastAPI's clean syntax
    def get(self, path):
        return self.route(path, "GET")

    def post(self, path):
        return self.route(path, "POST")

    def put(self, path):
        return self.route(path, "PUT")

    def delete(self, path):
        return self.route(path, "DELETE")

    # The core ASGI interface engine called by Uvicorn on every incoming request
    async def __call__(self, scope, receive, send):
        # Extract the target URL path (e.g., "/user") and method (e.g., "PUT") from server packets
        path = scope['path']
        method = scope.get('method', 'GET').upper() 

        # A global try/except block acts as our error catcher to prevent server crashes
        try:
            print(f"🖥️ [LOG] Incoming Request -> Method: {method} | Path: {path}")

            # --- 1. PARSE URL QUERY PARAMETERS (Like catching ?id=2) ---
            raw_query_bytes = scope.get('query_string', b'')
            query_string = raw_query_bytes.decode('utf-8') # Convert raw network bytes to text string
            query_params = {}
            
            if query_string:
                # Split key-value pairs separated by '&' (e.g., "id=2&name=bob")
                for pair in query_string.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=')
                        query_params[key] = value

            # --- 2. PARSE JSON BODY PACKETS (For data payloads sent via POST or PUT) ---
            body_data = {}
            if method in ("POST", "PUT"):
                body_bytes = b""
                more_body = True
                
                # Uvicorn streams long body request chunks in parts. Loop until it finishes.
                while more_body:
                    message = await receive()
                    body_bytes += message.get('body', b'')
                    more_body = message.get('more_body', False) # True means more chunks are coming
                
                # If a body was sent, convert the string text back into a standard Python dict
                if body_bytes:
                    try:
                        body_data = json.loads(body_bytes.decode('utf-8'))
                    except json.JSONDecodeError:
                        body_data = {"error": "Invalid JSON text received"}

            # --- 3. ROUTE MATCHING & FUNCTION EXECUTION ---
            # Check if the requested path and HTTP method both exist in our master routing book
            if path in self.routes and method in self.routes[path]:
                handler_function = self.routes[path][method]
                
                # Execute the developer's function, handing it the parsed data blocks
                raw_response = handler_function(query_params, body_data)
                
                # Convert the returned dictionary back into string text for transport
                response_text = json.dumps(raw_response) 
                status = 200 # HTTP 200 OK
            else:
                # If path exists but method doesn't (or path is missing entirely), trigger 405/404 handling
                response_text = json.dumps({"error": f"Method {method} not allowed on path {path}"})
                status = 405 # HTTP 405 Method Not Allowed

        except Exception as bug:
            # If any code crashes inside the developer's space, safely intercept it here
            print(f"🚨 [CRITICAL ERROR] A bug occurred: {str(bug)}")
            response_text = json.dumps({"error": "Internal Server Error", "details": str(bug)})
            status = 500 # HTTP 500 Internal Server Error

        # --- 4. PACK AND SEND RESPONSE DATA PACKETS BACK DOWN THE PIPE ---
        # Step A: Initialize connection stream and state that content type is JSON application
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [(b'content-type', b'application/json')],
        })
        # Step B: Push the encoded payload bytes directly across the network to the client browser
        await send({
            'type': 'http.response.body',
            'body': response_text.encode('utf-8'),
        })
