class CORSEngine:
    """
    Evaluates incoming origin states against defined access control lists 
    and determines safety approvals.
    """
    def __init__(self, allow_origins: list = None, allow_methods: list = None, allow_headers: list = None):
        self.allow_origins = allow_origins or []
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]

    def get_cors_headers(self, origin: str) -> list:
        """
        Compiles appropriate access control tracking strings based on validation rules.
        """
        headers = []
        
        # Determine origin allowance approval parameters
        if "*" in self.allow_origins:
            headers.append(("Access-Control-Allow-Origin", "*"))
        elif origin in self.allow_origins:
            headers.append(("Access-Control-Allow-Origin", origin))
            # Vary header instructs upstream browser caches to evaluate origins independently
            headers.append(("Vary", "Origin"))
        else:
            # Origin not allowed; don't attach origin headers (browser blocks natively)
            return []

        # Map methods and headers arrays
        headers.append(("Access-Control-Allow-Methods", ", ".join(self.allow_methods)))
        headers.append(("Access-Control-Allow-Headers", ", ".join(self.allow_headers)))
        return headers
