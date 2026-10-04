import json

class CustomMicroFramework:
    def __init__(self):
        # Maps paths to methods. Example: {"/users": {"PUT": func, "DELETE": func}}
        self.routes = {}

    # Core routing decorator engine that supports all HTTP methods
    def route(self, path, method="GET"):
        def decorator(func):
            if path not in self.routes:
                self.routes[path] = {}
            # Save the function under its specific HTTP method uppercase
            self.routes[path][method.upper()] = func
            return func
        return decorator

    # Quick shortcut helpers matching FastAPI's syntax
    def get(self, path):
        return self.route(path, "GET")

    def post(self, path):
        return self.route(path, "POST")

    def put(self, path):
        return self.route(path, "PUT")

    def delete(self, path):
        return self.route(path, "DELETE")

    # The magic ASGI function called by Uvicorn on every network request
    async def __call__(self, scope, receive, send):
        path = scope['path']
        method = scope.get('method', 'GET').upper() # Captures GET, POST, PUT, DELETE, etc.

        try:
            print(f"🖥️ [LOG] Incoming Request -> Method: {method} | Path: {path}")

            # --- PARSE QUERY PARAMETERS (Often used in GET/DELETE) ---
            raw_query_bytes = scope.get('query_string', b'')
            query_string = raw_query_bytes.decode('utf-8')
            query_params = {}
            if query_string:
                for pair in query_string.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=')
                        query_params[key] = value

            # --- PARSE JSON BODY PACKETS (Often used in POST/PUT) ---
            body_data = {}
            # Both POST and PUT requests typically pass a payload body
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

            # --- ROUTE MATCHING & EXECUTION ---
            if path in self.routes and method in self.routes[path]:
                handler_function = self.routes[path][method]
                
                # Execute the developer's function
                raw_response = handler_function(query_params, body_data)
                
                response_text = json.dumps(raw_response) 
                status = 200
            else:
                response_text = json.dumps({"error": f"Method {method} not allowed on path {path}"})
                status = 405 # 405 Method Not Allowed

        except Exception as bug:
            print(f"🚨 [CRITICAL ERROR] A bug occurred: {str(bug)}")
            response_text = json.dumps({"error": "Internal Server Error", "details": str(bug)})
            status = 500

        # --- SEND RESPONSE DATA PACKETS BACK ---
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [(b'content-type', b'application/json')],
        })
        await send({
            'type': 'http.response.body',
            'body': response_text.encode('utf-8'),
        })
