import json

class RequestParser:
    """
    Responsible for extracting and parsing raw incoming ASGI scope data 
    and byte streams into clean Python data structures (dictionaries).
    """

    @staticmethod
    def parse_query_params(scope) -> dict:
        """
        Extracts the raw query string from the ASGI scope and converts 
        it into a key-value dictionary.
        Example: /items?id=10&group=admin -> {"id": "10", "group": "admin"}
        """
        raw_query_bytes = scope.get('query_string', b'')
        query_string = raw_query_bytes.decode('utf-8')
        query_params = {}
        
        if query_string:
            # Split key-value pairs separated by '&'
            for pair in query_string.split('&'):
                if '=' in pair:
                    key, value = pair.split('=')
                    query_params[key] = value
        return query_params

    @staticmethod
    async def parse_body_data(method: str, receive) -> dict:
        """
        Asynchronously reads the incoming ASGI byte payload chunks for 
        POST and PUT requests, concatenates them, and decodes them as JSON.
        """
        body_data = {}
        
        # Only attempt to read payloads for structural mutation methods
        if method in ("POST", "PUT"):
            body_bytes = b""
            more_body = True
            
            # Loop through the ASGI message receiver until no chunks remain
            while more_body:
                message = await receive()
                body_bytes += message.get('body', b'')
                more_body = message.get('more_body', False)
                
            if body_bytes:
                try:
                    body_data = json.loads(body_bytes.decode('utf-8'))
                except json.JSONDecodeError:
                    # Graceful fallback error dictionary if JSON text is broken
                    body_data = {"error": "Invalid JSON text received"}
        return body_data
