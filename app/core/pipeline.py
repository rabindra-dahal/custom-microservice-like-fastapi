import inspect
from .request_parser import RequestParser
from ..utils.responses import Response, JSONResponse, HTMLResponse
from ..utils.documentation import DocumentationManager
from ..utils.dependencies import Depends
from ..utils.validation import QueryValidator, QueryField
from ..utils.exceptions import QueryValidationError
from ..utils.background import BackgroundTasks

class HttpPipelineProcessor:
    """
    The main coordinator for processing an HTTP request.
    Handles route matching, request parsing, input parameter validation,
    recursive dependency resolution, endpoint execution, exception normalization, 
    and non-blocking background task extraction.
    """

    def __init__(self, router, injector, exception_manager, routes_accessor):
        self._router = router
        self._injector = injector
        self._exception_manager = exception_manager
        self._routes_accessor = routes_accessor  # Lambda pointing back to dynamic application route map

    async def execute(self, scope, receive):
        """
        Executes the matched route handler or standard documentation generator 
        while automatically trapping internal system errors through an isolated boundary.
        """
        path = scope['path']
        method = scope.get('method', 'GET').upper()
        background_tasks = None  # Holds background tasks instance if requested by the handler signature

        try:
            # --- DOCS GENERATOR ROUTE ---
            if path == "/docs" and method == "GET":
                html_content = DocumentationManager.render_docs_html(self._routes_accessor())
                response_obj = HTMLResponse(content=html_content)
                
            # --- APPLICATION ROUTING ---
            else:
                # Delegate raw parsing logic out to RequestParser static helpers
                raw_query_params = RequestParser.parse_query_params(scope)
                body_data = await RequestParser.parse_body_data(method, receive)

                # Query the router to find a matching path pattern and capture variables
                handler_function, path_params = self._router.match(path, method)
                
                if handler_function:
                    sig = inspect.signature(handler_function)
                    
                    # 1. SCAN AND COMPILE VALIDATION SCHEMAS
                    schema = {}
                    annotations = {}
                    for param_name, param in sig.parameters.items():
                        annotations[param_name] = param.annotation if param.annotation != inspect.Parameter.empty else str
                        if isinstance(param.default, QueryField):
                            schema[param_name] = param.default

                    # 2. RUN VALIDATION ON SCHEMAS FOR QUERY STRINGS
                    validated_query_params = {}
                    if schema:
                        validated_query_params, errors = QueryValidator.validate(raw_query_params, schema, annotations)
                        if errors:
                            raise QueryValidationError(errors)

                    # 3. RESOLVE DEPENDENCIES & INJECT BACKGROUND TASKS CONTAINER
                    kwargs = {}
                    for param_name, param in sig.parameters.items():
                        # Explicit check for BackgroundTasks annotation request
                        if param.annotation == BackgroundTasks:
                            background_tasks = BackgroundTasks()
                            kwargs[param_name] = background_tasks
                        elif isinstance(param.default, Depends):
                            kwargs[param_name] = await self._injector.resolve(param.default.dependency_callable)
                        elif param_name in validated_query_params:
                            kwargs[param_name] = validated_query_params[param_name]

                    # 4. DYNAMIC ENDPOINT CALL MAP EXECUTION
                    param_keys = list(sig.parameters.keys())
                    if len(param_keys) >= 3 and 'params' in param_keys and 'body' in param_keys and 'path_params' in param_keys:
                        # Legacy/Explicit signature compatibility (params, body, path_params)
                        if inspect.iscoroutinefunction(handler_function):
                            raw_response = await handler_function(raw_query_params, body_data, path_params, **kwargs)
                        else:
                            raw_response = handler_function(raw_query_params, body_data, path_params, **kwargs)
                    else:
                        # Modern declarative signature layout (relies exclusively on dependency extraction)
                        if inspect.iscoroutinefunction(handler_function):
                            raw_response = await handler_function(**kwargs)
                        else:
                            raw_response = handler_function(**kwargs)
                    
                    # Normalize output payload into structured Response objects
                    if isinstance(raw_response, Response):
                        response_obj = raw_response
                    elif isinstance(raw_response, (dict, list)):
                        response_obj = JSONResponse(content=raw_response)
                    else:
                        response_obj = Response(content=raw_response)
                else:
                    # 405 Method Not Allowed / 404 Fallback Wrapper
                    response_obj = JSONResponse(
                        content={"error": f"Method {method} not allowed or missing path matching: {path}"}, 
                        status_code=405
                    )

        except Exception as bug:
            # --- GLOBAL EXCEPTION CAPTURING LAYER ---
            handled_res = await self._exception_manager.handle_exception(bug)
            if handled_res is not None:
                err_status, err_payload = handled_res
                response_obj = JSONResponse(content=err_payload, status_code=err_status)
            else:
                # Catch-all safety net for unhandled code errors
                response_obj = JSONResponse(
                    content={"error": "Internal Server Error", "details": str(bug)}, 
                    status_code=500
                )

        # Return the expanded 5-element response tuple layout up the chain to the application gateway
        return response_obj.status_code, response_obj.get_headers(), response_obj.render(), background_tasks, response_obj
