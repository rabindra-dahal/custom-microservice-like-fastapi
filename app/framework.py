import json    # Python's built-in library to handle JSON conversions

class CustomMicroFramework:
    def __init__(self):
        # Maps paths and methods. Example: {"/hello": {"GET": func}}
        self.routes = {}

    # Core routing decorator engine that supports dynamic methods
    def route(self, path, method="GET"):
        def decorator(func):
            if path not in self.routes:
                self.routes[path] = {}
            # Save the function into our dictionary under its specific HTTP method
            self.routes[path][method.upper()] = func
            return func
        return decorator

    # Quick shortcut helpers to mimic FastAPI's developer syntax
    def get(self, path):
        return self.route(path, "GET")

    def post(self, path):
        return self.route(path, "POST")

    # The magic function called by Uvicorn every time a request strikes your server
    async def __call__(self, scope, receive, send):
        path = scope['path']
        method = scope.get('method', 'GET').upper() # Grab the HTTP method (GET, POST)

        try:
            print(f"🖥️ [LOG] Incoming Request -> Method: {method} | Path: {path}")

            # --- PARSE QUERY PARAMETERS (For GET requests) ---
            raw_query_bytes = scope.get('query_string', b'')
            query_string = raw_query_bytes.decode('utf-8')
            query_params = {}
            if query_string:
                for pair in query_string.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=')
                        query_params[key] = value

            # --- POST JSON BODY DATA STREAM PARSING ---
            body_data = {}
            if method == "POST":
                body_bytes = b""
                more_body = True
                
                # Uvicorn streams body bytes in chunks. Loop until we have everything.
                while more_body:
                    message = await receive()
                    body_bytes += message.get('body', b'')
                    more_body = message.get('more_body', False)
                
                # Decode the text data into a Python dictionary
                if body_bytes:
                    try:
                        body_data = json.loads(body_bytes.decode('utf-8'))
                    except json.JSONDecodeError:
                        body_data = {"error": "Invalid JSON text received"}

            # --- ROUTE MATCHING & EXECUTION ---
            if path in self.routes and method in self.routes[path]:
                handler_function = self.routes[path][method]
                
                # Run the developer's function, feeding it both potential datasets
                raw_response = handler_function(query_params, body_data)
                
                response_text = json.dumps(raw_response) 
                status = 200
            else:
                response_text = json.dumps({"error": "Route or method not found"})
                status = 404

        except Exception as bug:
            # Handle server bugs without crashing the terminal process
            print(f"🚨 [CRITICAL ERROR] A bug occurred: {str(bug)}")
            response_text = json.dumps({
                "error": "Internal Server Error", 
                "details": str(bug)
            })
            status = 500

        # --- PACK AND SEND PAYLOAD DOWN THE NETWORK PIPE ---
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [(b'content-type', b'application/json')],
        })
        await send({
            'type': 'http.response.body',
            'body': response_text.encode('utf-8'),
        })
