import json
import inspect

class CustomMicroFramework:
    def __init__(self):
        # Master routing book maps paths and methods to functions
        self.routes = {}
        # List to hold registered global middleware functions
        self.middlewares = []

    # Decorator to register global middleware functions
    def middleware(self):
        def decorator(func):
            self.middlewares.append(func)
            return func
        return decorator

    def route(self, path, method="GET"):
        def decorator(func):
            if path not in self.routes:
                self.routes[path] = {}
            self.routes[path][method.upper()] = func
            return func
        return decorator

    # Quick shortcut helpers
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
        # We only intercept standard HTTP requests (ignore lifecycles/websockets for now)
        if scope['type'] != 'http':
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b''})
            return

        # ---------------------------------------------------------------------
        # MIDDLEWARE EXECUTION CHAIN
        # ---------------------------------------------------------------------
        # We construct a chain of responsibility. If middlewares exist, we pass the 
        # execution down the line. The final step of the chain is our core request handler.
        
        index = 0

        async def call_next(current_scope):
            nonlocal index
            if index < len(self.middlewares):
                # Select the next middleware in line
                mw = self.middlewares[index]
                index += 1
                # Execute the middleware, handing it the scope and the next step in line
                if inspect.iscoroutinefunction(mw):
                    return await mw(current_scope, call_next)
                else:
                    return mw(current_scope, call_next)
            else:
                # We reached the end of the middleware list! Run the core route logic.
                return await self._execute_core_route(current_scope, receive)

        # Start executing the chain
        status, headers, response_bytes = await call_next(scope)

        # Send the final packed response back across the network to the client
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': headers,
        })
        await send({
            'type': 'http.response.body',
            'body': response_bytes,
        })

    # Internal helper that handles parsing, matching, and executing the actual route functions
    async def _execute_core_route(self, scope, receive):
        path = scope['path']
        method = scope.get('method', 'GET').upper()

        try:
            print(f"🖥️ [LOG] Core Router -> Processing Method: {method} | Path: {path}")

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

            # --- 3. ROUTE MATCHING & SMART FUNCTION EXECUTION ---
            if path in self.routes and method in self.routes[path]:
                handler_function = self.routes[path][method]
                
                if inspect.iscoroutinefunction(handler_function):
                    raw_response = await handler_function(query_params, body_data)
                else:
                    raw_response = handler_function(query_params, body_data)
                
                response_text = json.dumps(raw_response) 
                status = 200
            else:
                response_text = json.dumps({"error": f"Method {method} not allowed on path {path}"})
                status = 405

        except Exception as bug:
            print(f"🚨 [CRITICAL ERROR] A bug occurred: {str(bug)}")
            response_text = json.dumps({"error": "Internal Server Error", "details": str(bug)})
            status = 500

        # Return the components up to the middleware wrapper instead of sending immediately
        headers = [(b'content-type', b'application/json')]
        return status, headers, response_text.encode('utf-8')
