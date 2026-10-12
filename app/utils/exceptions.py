import inspect

class ExceptionManager:
    """
    Maintains custom error rules and matches thrown exceptions 
    against user-defined handlers.
    """
    def __init__(self):
        self.handlers = {}

    def exception_handler(self, exc_class):
        """Decorator to register a custom handler function for a specific exception class."""
        def decorator(func):
            self.handlers[exc_class] = func
            return func
        return decorator

    async def handle_exception(self, exception_instance) -> tuple:
        """
        Checks if there is a handler registered for the thrown exception class.
        Returns a tuple containing: (status_code, error_payload_dict) if matched, else None.
        """
        exc_class = type(exception_instance)
        
        # Look for an exact match or match against parent exception classes
        for registered_class, handler in self.handlers.items():
            if issubclass(exc_class, registered_class):
                if inspect.iscoroutinefunction(handler):
                    return await handler(exception_instance)
                return handler(exception_instance)
                
        return None

class QueryValidationError(Exception):
    """Raised when query parameters fail validation schemas."""
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(str(errors))

class BodyValidationError(Exception):
    """Raised when request payload bodies fail structural model contracts."""
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(str(errors))
