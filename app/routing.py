import inspect
import re

class Router:
    def __init__(self):
        # Maps raw paths to method handlers for exact/static matches
        self.routes = {}
        # Compiled list of dynamic path tuples: (regex_compiled_pattern, path_string, methods_dict)
        self.dynamic_routes = []

    def route(self, path, method="GET"):
        def decorator(func):
            # Check if this route has parameters like {id}
            if '{' in path and '}' in path:
                # Convert path to regex. Example: "/users/{id}" -> r"^/users/(?P<id>[^/]+)$"
                regex_pattern = re.sub(r'{([^}]+)}', r'(?P<\1>[^/]+)', path)
                compiled_regex = re.compile(f"^{regex_pattern}$")
                
                # Check if we already registered this dynamic pattern
                existing = None
                for entry in self.dynamic_routes:
                    if entry['path_str'] == path:
                        existing = entry
                        break
                
                if not existing:
                    existing = {"regex": compiled_regex, "path_str": path, "methods": {}}
                    self.dynamic_routes.append(existing)
                
                existing["methods"][method.upper()] = func
            else:
                # Fallback to standard static routing
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
        """
        Attempts to match an incoming path against static routes first, then dynamic paths.
        Returns a tuple: (handler_function, path_parameters_dict)
        """
        method = method.upper()

        # 1. Try an exact static route match
        if path in self.routes and method in self.routes[path]:
            return self.routes[path][method], {}

        # 2. Fall back to regex scanning for parameters
        for route_entry in self.dynamic_routes:
            match_obj = route_entry["regex"].match(path)
            if match_obj and method in route_entry["methods"]:
                # extract named groups into a clean dictionary (e.g., {"id": "123"})
                path_params = match_obj.groupdict()
                return route_entry["methods"][method], path_params

        return None, {}
