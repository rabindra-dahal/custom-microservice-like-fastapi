import inspect

class MiddlewareManager:
    def __init__(self):
        self.middlewares = []

    def middleware(self):
        def decorator(func):
            self.middlewares.append(func)
            return func
        return decorator

    async def execute_chain(self, scope, core_handler):
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
                return await core_handler(current_scope)

        return await call_next(scope)
