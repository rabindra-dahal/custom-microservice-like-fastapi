import json
import inspect # Imported to dynamically detect if a developer wrote a standard function or an 'async def'

class CustomMicroFramework:
    def __init__(self):
        # Master routing book maps paths and methods to functions
        # Example layout: {"/user": {"GET": get_user_func}}
        self.routes = {}

    # The master decorator function that registers endpoints under specific HTTP methods
    def route(self, path, method="GET"):
        def decorator(func):
            if path not in self.routes:
                self.routes[path] = {}
            # Save the function under its specific HTTP method forced to uppercase
            self.routes[path][method.upper()] = func
            return func
        return decorator

    # Quick shortcut helpers matching FastAPI's clean syntax
    def get(self, path):
        return self.route(path, "GET")

    def post(self, path):
        return self.route(path, "POST")

    def put(self, path):
        return self.route(path, "PUT")

    def delete(self, path):
        return self.route(path, "DELETE")

    # Core ASGI engine called by Uvicorn on every incoming network request
    async def __call__(self, scope, receive, send):
        path = scope['path']
        method = scope.get('method', 'GET').upper() 

        # Global try/except block acts as our error catcher to prevent server crashes
        try:
            print(f"🖥️ [LOG] Incoming Request -> Method: {method} | Path: {path}")

            # --- 1. PARSE URL QUERY PARAMETERS ---
            raw_query_bytes = scope.get('query_string', b'')
            query_string = raw_query_bytes.decode('utf-8')
            query_params = {}
            if query_string:
                for pair in query_string.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=')
                        query_params[key] = value

            # --- 2. PARSE JSON BODY PACKETS ---
            body_data = {}
            if method in ("POST", "PUT"):
                body_bytes = b""
                more_body = True
                while more_body:
                    message = await receive()
                    body_bytes += message.get('body', b'')
                    more_body = message.get('more_body', False)
                if body_bytes:
                    try:
                        body_data = json.loads(body_bytes.decode('utf-8'))
                    except json.JSONDecodeError:
                        body_data = {"error": "Invalid JSON text received"}

            # --- 3. ROUTE MATCHING & SMART FUNCTION EXECUTION (ASYNC UPGRADE) ---
            if path in self.routes and method in self.routes[path]:
                handler_function = self.routes[path][method]
                
                # Check if the developer wrote 'async def' for this specific endpoint function
                if inspect.iscoroutinefunction(handler_function):
                    # It's an asynchronous function! We MUST use 'await' to let it run in the background
                    raw_response = await handler_function(query_params, body_data)
                else:
                    # It's a standard synchronous function! Execute it normally without 'await'
                    raw_response = handler_function(query_params, body_data)
                
                # Convert the returned dictionary back into text string for transport
                response_text = json.dumps(raw_response) 
                status = 200 # HTTP 200 OK
            else:
                response_text = json.dumps({"error": f"Method {method} not allowed on path {path}"})
                status = 405 # HTTP 405 Method Not Allowed

        except Exception as bug:
            # If any code crashes inside the developer's space, safely intercept it here
            print(f"🚨 [CRITICAL ERROR] A bug occurred: {str(bug)}")
            response_text = json.dumps({"error": "Internal Server Error", "details": str(bug)})
            status = 500 # HTTP 500 Internal Server Error

        # --- 4. SEND RESPONSE DATA PACKETS BACK ---
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [(b'content-type', b'application/json')],
        })
        await send({
            'type': 'http.response.body',
            'body': response_text.encode('utf-8'),
        })
