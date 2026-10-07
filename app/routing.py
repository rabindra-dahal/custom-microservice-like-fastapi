import inspect

class Router:
    def __init__(self):
        self.routes = {}

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

    def match(self, path, method):
        if path in self.routes and method in self.routes[path]:
            return self.routes[path][method]
        return None
