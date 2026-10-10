import inspect
import re

TYPE_CASTERS = {
    "int": (r"\d+", int),
    "float": (r"\d+(?:\.\d+)?", float),
    "str": (r"[^/]+", str),
}

class Router:
    def __init__(self):
        self.routes = {}
        self.dynamic_routes = []

    def route(self, path, method="GET"):
        def decorator(func):
            if '{' in path and '}' in path:
                # Find all parameter markers, e.g., {item_id:int} or {name}
                # group(1) matches the name, group(2) matches the type part if present (e.g. :int)
                pattern = path
                casters = {}
                
                # Find occurrences of {param_name} or {param_name:type}
                markers = re.findall(r'{([^}]+)}', path)
                for marker in markers:
                    if ':' in marker:
                        name, type_str = marker.split(':', 1)
                    else:
                        name, type_str = marker, 'str'
                    
                    regex_str, converter = TYPE_CASTERS.get(type_str, TYPE_CASTERS['str'])
                    casters[name] = converter
                    # Replace the marker with a named regex capture group
                    pattern = pattern.replace(f"{{{marker}}}", f"(?P<{name}>{regex_str})")
                
                compiled_regex = re.compile(f"^{pattern}$")
                
                existing = None
                for entry in self.dynamic_routes:
                    if entry['path_str'] == path:
                        existing = entry
                        break
                
                if not existing:
                    existing = {"regex": compiled_regex, "path_str": path, "methods": {}, "casters": casters}
                    self.dynamic_routes.append(existing)
                
                existing["methods"][method.upper()] = func
            else:
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
        method = method.upper()

        if path in self.routes and method in self.routes[path]:
            return self.routes[path][method], {}

        for route_entry in self.dynamic_routes:
            match_obj = route_entry["regex"].match(path)
            if match_obj and method in route_entry["methods"]:
                raw_params = match_obj.groupdict()
                # Apply explicit casting definitions
                cast_params = {}
                for name, val in raw_params.items():
                    caster = route_entry["casters"].get(name, str)
                    try:
                        cast_params[name] = caster(val)
                    except ValueError:
                        cast_params[name] = val # Fallback on exception
                return route_entry["methods"][method], cast_params

        return None, {}
