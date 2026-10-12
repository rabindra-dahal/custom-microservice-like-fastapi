class APIRouter:
    """
    A modular route grouping registry that allows endpoints to be declared 
    independently and mounted onto the main framework app with common prefixes.
    """
    def __init__(self, prefix: str = ""):
        # Strip trailing slashes and ensure leading slash
        self.prefix = f"/{prefix.strip('/')}" if prefix.strip('/') else ""
        self.routes = []

    def route(self, path: str, method: str = "GET"):
        """
        Captures route definitions locally instead of instantly compiling them.
        """
        def decorator(func):
            # Clean and combine the prefix with the endpoint path
            clean_path = f"/{path.strip('/')}" if path.strip('/') else ""
            combined_path = f"{self.prefix}{clean_path}"
            # Fallback to root slash if completely empty
            if not combined_path:
                combined_path = "/"
                
            self.routes.append({
                "path": combined_path,
                "method": method.upper(),
                "handler": func
            })
            return func
        return decorator

    # Standard routing shortcuts
    def get(self, path): return self.route(path, "GET")
    def post(self, path): return self.route(path, "POST")
    def put(self, path): return self.route(path, "PUT")
    def delete(self, path): return self.route(path, "DELETE")
