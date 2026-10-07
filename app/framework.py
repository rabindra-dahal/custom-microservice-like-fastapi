import json
import inspect

class CustomMicroFramework:
    def __init__(self):
        self.routes = {}
        self.middlewares = []
        self.exception_handlers = {}

    def exception_handler(self, exception_class):
        def decorator(func):
            self.exception_handlers[exception_class] = func
            return func
        return decorator

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

    def get(self, path): return self.route(path, "GET")
    def post(self, path): return self.route(path, "POST")
    def put(self, path): return self.route(path, "PUT")
    def delete(self, path): return self.route(path, "DELETE")

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b''})
            return

        index = 0

        async def call_next(current_scope):
            nonlocal index
            if index < len(self.middlewares):
                mw = self.middlewares[index]
                index += 1
                if inspect.iscoroutinefunction(mw):
                    return await mw(current_scope, call_next)
                else:
                    return mw(current_scope, call_next)
            else:
                return await self._execute_core_route(current_scope, receive)

        status, headers, response_bytes = await call_next(scope)

        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': headers,
        })
        await send({
            'type': 'http.response.body',
            'body': response_bytes,
        })

    async def _execute_core_route(self, scope, receive):
        path = scope['path']
        method = scope.get('method', 'GET').upper()
        content_type = b'application/json'

        try:
            # Check for a specific internal check for our HTML documentation dashboard
            if path == "/docs" and method == "GET":
                response_text = self._render_docs_html()
                status = 200
                content_type = b'text/html; charset=utf-8'
            else:
                # Standard Route Lifecycle Execution
                raw_query_bytes = scope.get('query_string', b'')
                query_string = raw_query_bytes.decode('utf-8')
                query_params = {}
                if query_string:
                    for pair in query_string.split('&'):
                        if '=' in pair:
                            key, value = pair.split('=')
                            query_params[key] = value

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
            error_class = bug.__class__
            if error_class in self.exception_handlers:
                handler = self.exception_handlers[error_class]
                if inspect.iscoroutinefunction(handler):
                    status, raw_response = await handler(bug)
                else:
                    status, raw_response = handler(bug)
                response_text = json.dumps(raw_response)
            else:
                response_text = json.dumps({"error": "Internal Server Error", "details": str(bug)})
                status = 500

        headers = [(b'content-type', content_type)]
        return status, headers, response_text.encode('utf-8')

    # Generates a dynamic HTML/CSS template reflecting all active workspace endpoints
    def _render_docs_html(self):
        route_cards_html = ""
        
        for path, methods in sorted(self.routes.items()):
            for method, func in methods.items():
                # Color code standard HTTP verbs
                badge_color = "#34d399" if method == "GET" else "#60a5fa" if method == "POST" else "#f59e0b" if method == "PUT" else "#f87171"
                docstring = inspect.getdoc(func) or "No documentation provided for this endpoint."
                
                route_cards_html += f"""
                <div class="route-card" data-path="{path}" data-method="{method}">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                        <span class="method-badge" style="background-color: {badge_color};">{method}</span>
                        <span class="route-path">{path}</span>
                    </div>
                    <p style="color: #9ca3af; font-size: 0.9rem; line-height: 1.4; margin: 4px 0 12px 0;">{docstring}</p>
                    <div style="font-size: 0.8rem; color: #6b7280; font-family: monospace;">Handler: {func.__name__}()</div>
                </div>
                """

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Custom Framework API Dashboard</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 40px 20px; }}
                .container {{ max-width: 900px; margin: 0 auto; }}
                h1 {{ font-size: 2rem; color: #fff; margin-bottom: 8px; }}
                .subtitle {{ color: #94a3b8; margin-bottom: 32px; font-size: 1.1rem; }}
                .search-bar {{ width: 100%; padding: 12px 16px; background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; color: #fff; font-size: 1rem; margin-bottom: 24px; box-sizing: border-box; }}
                .search-bar:focus {{ outline: 2px solid #3b82f6; border-color: transparent; }}
                .route-card {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 18px; margin-bottom: 16px; transition: transform 0.2s, border-color 0.2s; }}
                .route-card:hover {{ border-color: #475569; transform: translateY(-1px); }}
                .method-badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; color: #fff; font-weight: bold; font-size: 0.8rem; width: 60px; text-align: center; font-family: monospace; }}
                .route-path {{ font-size: 1.1rem; font-weight: 600; color: #f1f5f9; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚡ API Interactive Dashboard</h1>
                <p class="subtitle">Auto-generated OpenAPI blueprint detailing active backend route handlers.</p>
                <input type="text" id="search" class="search-bar" placeholder="Filter routes by path or method (e.g. GET, /user)..." oninput="filterRoutes()">
                <div id="routes-list">
                    {route_cards_html}
                </div>
            </div>
            <script>
                function filterRoutes() {{
                    const query = document.getElementById('search').value.toLowerCase();
                    const cards = document.querySelectorAll('.route-card');
                    cards.forEach(card => {{
                        const path = card.getAttribute('data-path').toLowerCase();
                        const method = card.getAttribute('data-method').toLowerCase();
                        if (path.includes(query) || method.includes(query)) {{
                            card.style.display = 'block';
                        }} else {{
                            card.style.display = 'none';
                        }}
                    }});
                }}
            </script>
        </body>
        </html>
        """
