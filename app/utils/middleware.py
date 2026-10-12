import inspect

class MiddlewareManager:
    """
    Manages the sequential execution of registered middleware layers, 
    wrapping around the core HTTP execution pipeline.
    """
    def __init__(self):
        self.middlewares = []

    def middleware(self):
        """Decorator used to append a new middleware function into the execution chain."""
        def decorator(func):
            self.middlewares.append(func)
            return func
        return decorator

    async def execute_chain(self, scope, core_pipeline_callable) -> tuple:
        """
        Executes middleware layers sequentially before passing the request 
        down to the main handler.
        """
        # Create an execution layer that ends by running the core route handler
        async def call_next(current_scope):
            return await core_pipeline_callable(current_scope)

        # Wrap handlers around each other from the outside in
        handler = call_next
        for mw in reversed(self.middlewares):
            # Create a closure capturing the current middleware state level
            def make_layer(current_mw, next_handler):
                async def layer(s):
                    if inspect.iscoroutinefunction(current_mw):
                        return await current_mw(s, next_handler)
                    return current_mw(s, next_handler)
                return layer
            handler = make_layer(mw, handler)

        return await handler(scope)
