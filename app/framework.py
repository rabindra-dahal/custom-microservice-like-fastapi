import json
import inspect
from .routing import Router
from .middleware import MiddlewareManager
from .exceptions import ExceptionManager
from .documentation import DocumentationManager

class CustomMicroFramework:
    def __init__(self):
        self._router = Router()
        self._middleware_manager = MiddlewareManager()
        self._exception_manager = ExceptionManager()

    @property
    def routes(self):
        # Merge both static and dynamic configurations just for the /docs visual rendering panel
        merged = dict(self._router.routes)
        for entry in self._router.dynamic_routes:
            merged[entry["path_str"]] = entry["methods"]
        return merged

    def route(self, path, method="GET"): return self._router.route(path, method)
    def get(self, path): return self._router.get(path)
    def post(self, path): return self._router.post(path)
    def put(self, path): return self._router.put(path)
    def delete(self, path): return self._router.delete(path)
    def middleware(self): return self._middleware_manager.middleware()
    def exception_handler(self, exc_class): return self._exception_manager.exception_handler(exc_class)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b''})
            return

        status, headers, response_bytes = await self._middleware_manager.execute_chain(
            scope, 
            lambda current_scope: self._execute_core_route(current_scope, receive)
        )

        await send({'type': 'http.response.start', 'status': status, 'headers': headers})
        await send({'type': 'http.response.body', 'body': response_bytes})

    async def _execute_core_route(self, scope, receive):
        path = scope['path']
        method = scope.get('method', 'GET').upper()
        content_type = b'application/json'

        try:
            if path == "/docs" and method == "GET":
                response_text = DocumentationManager.render_docs_html(self.routes)
                status = 200
                content_type = b'text/html; charset=utf-8'
            else:
                # 1. PARSE QUERY STRINGS
                raw_query_bytes = scope.get('query_string', b'')
                query_string = raw_query_bytes.decode('utf-8')
                query_params = {}
                if query_string:
                    for pair in query_string.split('&'):
                        if '=' in pair:
                            key, value = pair.split('=')
                            query_params[key] = value

                # 2. PARSE REQUEST BODIES
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

                # 3. ROUTE MATCHING WITH PATH PARAMS EXTRACTION
                handler_function, path_params = self._router.match(path, method)
                
                if handler_function:
                    # Provide path_params as the third argument to endpoints
                    if inspect.iscoroutinefunction(handler_function):
                        raw_response = await handler_function(query_params, body_data, path_params)
                    else:
                        raw_response = handler_function(query_params, body_data, path_params)
                    
                    response_text = json.dumps(raw_response) 
                    status = 200
                else:
                    response_text = json.dumps({"error": f"Method {method} not allowed or missing path matching: {path}"})
                    status = 405

        except Exception as bug:
            handled_res = await self._exception_manager.handle_exception(bug)
            if handled_res is not None:
                status, raw_response = handled_res
                response_text = json.dumps(raw_response)
            else:
                response_text = json.dumps({"error": "Internal Server Error", "details": str(bug)})
                status = 500

        headers = [(b'content-type', content_type)]
        return status, headers, response_text.encode('utf-8')
