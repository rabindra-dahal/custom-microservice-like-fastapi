import inspect

class ExceptionManager:
    def __init__(self):
        self.exception_handlers = {}

    def exception_handler(self, exception_class):
        def decorator(func):
            self.exception_handlers[exception_class] = func
            return func
        return decorator

    async def handle_exception(self, exception):
        error_class = exception.__class__
        if error_class in self.exception_handlers:
            handler = self.exception_handlers[error_class]
            if inspect.iscoroutinefunction(handler):
                return await handler(exception)
            else:
                return handler(exception)
        return None
