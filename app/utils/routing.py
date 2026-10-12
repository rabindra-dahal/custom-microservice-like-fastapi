from .compiler import RouteCompiler

class Router:
    """
    Manages route endpoint lists and performs request path target lookups.
    Delegates path regex compilation and type conversions to the RouteCompiler.
    """
    def __init__(self):
        self.routes = {}            # For fixed static paths like /health
        self.dynamic_routes = []    # For parameterized paths like /items/{item_id:int}

    def route(self, path: str, method: str = "GET"):
        """
        Decorator registering endpoints into local method arrays.
        """
        def decorator(func):
            if '{' in path and '}' in path:
                # Delegate path parsing and regex compilation to the compiler
                compiled_regex, casters = RouteCompiler.compile_dynamic_path(path)
                
                existing = next((r for r in self.dynamic_routes if r['path_str'] == path), None)
                if not existing:
                    existing = {
                        "regex": compiled_regex, 
                        "path_str": path, 
                        "methods": {}, 
                        "casters": casters
                    }
                    self.dynamic_routes.append(existing)
                
                existing["methods"][method.upper()] = func
            else:
                if path not in self.routes:
                    self.routes[path] = {}
                self.routes[path][method.upper()] = func
                
            return func
        return decorator

    # Standard routing method shortcuts
    def get(self, path): return self.route(path, "GET")
    def post(self, path): return self.route(path, "POST")
    def put(self, path): return self.route(path, "PUT")
    def delete(self, path): return self.route(path, "DELETE")

    def match(self, path: str, method: str) -> tuple:
        """
        Matches request strings against registered static or dynamic routes.
        Returns: (handler_function, casted_path_parameters_dict)
        """
        method = method.upper()

        # 1. Fast path check for exact matching static entries
        if path in self.routes and method in self.routes[path]:
            return self.routes[path][method], {}

        # 2. Scanning loop for dynamic regex pattern evaluation
        for route_entry in self.dynamic_routes:
            match_obj = route_entry["regex"].match(path)
            if match_obj and method in route_entry["methods"]:
                # Delegate value type coercion to the compiler utility
                casted_params = RouteCompiler.coerce_parameters(
                    raw_params=match_obj.groupdict(), 
                    casters=route_entry["casters"]
                )
                return route_entry["methods"][method], casted_params

        return None, {}
