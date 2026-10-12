import inspect
from typing import TYPE_CHECKING

# Import core management engines and orchestrators
from .utils.routing import Router
from .utils.middleware import MiddlewareManager
from .utils.exceptions import ExceptionManager
from .core.injector import DependencyInjector
from .core.lifespan import LifespanManager
from .core.pipeline import HttpPipelineProcessor

# --- STATIC TYPE CHECKING GUARD ---
# This block is only visible to Pylance/Mypy during static analysis.
# It prevents runtime circular import loops between the framework and router utilities.
if TYPE_CHECKING:
    from .utils.router_group import APIRouter

class CustomMicroFramework:
    """
    The central coordinator and primary gateway interface for our framework.
    Implements the standard ASGI call specification to orchestrate life-cycle,
    routing, middleware, validation, background tasks, and streaming operations.
    """

    def __init__(self):
        # Initialize supporting managers and core execution engines
        self._router = Router()
        self._middleware_manager = MiddlewareManager()
        self._exception_manager = ExceptionManager()
        self._injector = DependencyInjector()
        self._lifespan_manager = LifespanManager()
        
        # Instantiate the HTTP Processing Pipeline with references to its core subsystems
        self._pipeline = HttpPipelineProcessor(
            router=self._router,
            injector=self._injector,
            exception_manager=self._exception_manager,
            routes_accessor=lambda: self.routes
        )

    @property
    def routes(self):
        """
        Combines static and dynamic path definitions into a single dictionary representation.
        Enables structural inspection by utilities like the DocumentationManager dashboard.
        """
        merged = dict(self._router.routes)
        for entry in self._router.dynamic_routes:
            merged[entry["path_str"]] = entry["methods"]
        return merged

    def include_router(self, router_group: "APIRouter"):
        """
        Unpacks a modular APIRouter group registry and transfers all its underlying
        endpoints directly into the framework's core runtime router.
        """
        for route_entry in router_group.routes:
            path = route_entry["path"]
            method = route_entry["method"]
            handler = route_entry["handler"]
            
            # Re-apply our existing core decorator logic to register the endpoint cleanly
            self._router.route(path, method)(handler)

    # --- CORE ROUTER DECORATOR SHORTCUTS ---
    def route(self, path, method="GET"): return self._router.route(path, method)
    def get(self, path): return self._router.get(path)
    def post(self, path): return self._router.post(path)
    def put(self, path): return self._router.put(path)
    def delete(self, path): return self._router.delete(path)
    
    # --- CONFIGURATION SUBSYSTEM SHORTCUTS ---
    def middleware(self): return self._middleware_manager.middleware()
    def exception_handler(self, exc_class): return self._exception_manager.exception_handler(exc_class)
    
    def on_event(self, event_type: str):
        """
        Decorator mapping registration functions to startup/shutdown lifecycle handles.
        Allowed event types: 'startup', 'shutdown'.
        """
        def decorator(func):
            if event_type == "startup": 
                self._lifespan_manager.register_startup(func)
            elif event_type == "shutdown": 
                self._lifespan_manager.register_shutdown(func)
            return func
        return decorator

    async def __call__(self, scope, receive, send):
        """
        Primary entry point for ASGI server communication (e.g., Uvicorn).
        Routes incoming messages based on their event protocol scope.
        """
        # 1. Route ASGI Lifespan Events (boot/shutdown) to LifespanManager
        if scope['type'] == 'lifespan':
            await self._lifespan_manager.handle_loop(receive, send)
            return

        # 2. Block non-HTTP client interactions gracefully (e.g. WebSockets handled elsewhere)
        if scope['type'] != 'http':
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b''})
            return

        # 3. Process Execution Pipeline through Middleware Chain and Pipeline Processor
        # Captures the 5-element tuple containing status, headers, body bytes, background tasks, and response objects
        status, headers, response_bytes, background_tasks, response_obj = await self._middleware_manager.execute_chain(
            scope, 
            lambda current_scope: self._pipeline.execute(current_scope, receive)
        )

        # 4. Stream response headers frame back to the client via ASGI server channels
        await send({'type': 'http.response.start', 'status': status, 'headers': headers})

        # 5. DYNAMIC RESPONSE TRANSMISSION PIPELINE
        from .utils.responses import FileResponse
        if isinstance(response_obj, FileResponse):
            # Asynchronously stream the resource file off the disk block-by-block
            async for file_chunk in response_obj.stream_chunks():
                await send({
                    'type': 'http.response.body',
                    'body': file_chunk,
                    'more_body': True  # Informs ASGI server that more chunks are following
                })
            # Emit empty terminal frame to close the active connection socket stream
            await send({
                'type': 'http.response.body',
                'body': b'',
                'more_body': False
            })
        else:
            # Emit the full raw pre-rendered response byte chunk instantly for typical web responses
            await send({
                'type': 'http.response.body',
                'body': response_bytes,
                'more_body': False
            })

        # 6. POST-RESPONSE EXECUTION PHASE: Trigger deferred background workers safely after network write completes
        if background_tasks:
            await background_tasks.execute_all()
