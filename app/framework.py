import json
import inspect
from .routing import Router
from .middleware import MiddlewareManager
from .exceptions import ExceptionManager
from .documentation import DocumentationManager
from .dependencies import Depends
from .responses import Response, JSONResponse, HTMLResponse

class CustomMicroFramework:
    def __init__(self):
        self._router = Router()
        self._middleware_manager = MiddlewareManager()
        self._exception_manager = ExceptionManager()
        self._startup_handlers = []
        self._shutdown_handlers = []

    @property
    def routes(self):
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
    def on_event(self, event_type: str):
        def decorator(func):
            if event_type == "startup": self._startup_handlers.append(func)
            elif event_type == "shutdown": self._shutdown_handlers.append(func)
            return func
        return decorator

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    try:
                        for handler in self._startup_handlers:
                            if inspect.iscoroutinefunction(handler): await handler()
                            else: handler()
                        await send({'type': 'lifespan.startup.complete'})
                    except Exception as e:
                        await send({'type': 'lifespan.startup.failed', 'message': str(e)})
                        break
                elif message['type'] == 'lifespan.shutdown':
                    try:
                        for handler in self._shutdown_handlers:
                            if inspect.iscoroutinefunction(handler): await handler()
                            else: handler()
                        await send({'type': 'lifespan.shutdown.complete'})
                    except Exception as e:
                        await send({'type': 'lifespan.shutdown.failed', 'message': str(e)})
                    break
            return

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

    async def _resolve_dependency(self, callable_obj):
        sig = inspect.signature(callable_obj)
        dep_kwargs = {}
        for param_name, param in sig.parameters.items():
            if isinstance(param.default, Depends):
                nested_callable = param.default.dependency_callable
                dep_kwargs[param_name] = await self._resolve_dependency(nested_callable)
        
        if inspect.iscoroutinefunction(callable_obj): return await callable_obj(**dep_kwargs)
        return callable_obj(**dep_kwargs)

    async def _execute_core_route(self, scope, receive):
        path = scope['path']
        method = scope.get('method', 'GET').upper()

        try:
            if path == "/docs" and method == "GET":
                html_content = DocumentationManager.render_docs_html(self.routes)
                response_obj = HTMLResponse(content=html_content)
            else:
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
                        try: body_data = json.loads(body_bytes.decode('utf-8'))
                        except json.JSONDecodeError: body_data = {"error": "Invalid JSON text received"}

                handler_function, path_params = self._router.match(path, method)
                
                if handler_function:
                    sig = inspect.signature(handler_function)
                    kwargs = {}
                    for param_name, param in sig.parameters.items():
                        if isinstance(param.default, Depends):
                            kwargs[param_name] = await self._resolve_dependency(param.default.dependency_callable)

                    param_keys = list(sig.parameters.keys())
                    if len(param_keys) >= 3 and param_keys == 'params' and param_keys == 'body' and param_keys == 'path_params':
                        if inspect.iscoroutinefunction(handler_function):
                            raw_response = await handler_function(query_params, body_data, path_params, **kwargs)
                        else:
                            raw_response = handler_function(query_params, body_data, path_params, **kwargs)
                    else:
                        if inspect.iscoroutinefunction(handler_function):
                            raw_response = await handler_function(**kwargs)
                        else:
                            raw_response = handler_function(**kwargs)
                    
                    # PROCESS THE ROUTE INTERACTION VALUE
                    if isinstance(raw_response, Response):
                        response_obj = raw_response
                    elif isinstance(raw_response, (dict, list)):
                        response_obj = JSONResponse(content=raw_response)
                    else:
                        response_obj = Response(content=raw_response)
                else:
                    response_obj = JSONResponse(content={"error": f"Method {method} not allowed or missing path matching: {path}"}, status_code=405)

        except Exception as bug:
            handled_res = await self._exception_manager.handle_exception(bug)
            if handled_res is not None:
                err_status, err_payload = handled_res
                response_obj = JSONResponse(content=err_payload, status_code=err_status)
            else:
                response_obj = JSONResponse(content={"error": "Internal Server Error", "details": str(bug)}, status_code=500)

        return response_obj.status_code, response_obj.get_headers(), response_obj.render()
