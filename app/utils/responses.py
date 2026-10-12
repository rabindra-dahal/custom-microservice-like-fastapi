import json

class Response:
    """
    Base HTTP response object. Handles compiling custom headers and 
    encoding text bodies into raw byte responses.
    """
    def __init__(self, content: any = None, status_code: int = 200, headers: list = None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or []
        self.media_type = None
        
    def render(self) -> bytes:
        """Encodes content payload into bytes."""
        if self.content is None:
            return b""
        if isinstance(self.content, bytes):
            return self.content
        return str(self.content).encode("utf-8")

    def get_headers(self) -> list:
        """Formates and outputs an array of standard ASGI-compliant header byte pairs."""
        raw_headers = []
        has_content_type = False
        
        for k, v in self.headers:
            k_bytes, v_bytes = k.lower().encode("utf-8"), v.encode("utf-8")
            if k_bytes == b"content-type":
                has_content_type = True
            raw_headers.append((k_bytes, v_bytes))
            
        if not has_content_type and self.media_type:
            raw_headers.append((b"content-type", self.media_type.encode("utf-8")))
            
        return raw_headers


class JSONResponse(Response):
    """Encodes dictionaries and arrays into pure application/json text bytes."""
    def __init__(self, content: any, status_code: int = 200, headers: list = None):
        super().__init__(content, status_code, headers)
        self.media_type = "application/json"

    def render(self) -> bytes:
        return json.dumps(self.content).encode("utf-8")


class HTMLResponse(Response):
    """Renders raw HTML web interface page files directly to the browser client."""
    def __init__(self, content: str, status_code: int = 200, headers: list = None):
        super().__init__(content, status_code, headers)
        self.media_type = "text/html; charset=utf-8"


class RedirectResponse(Response):
    """Sends temporary or permanent HTTP location redirection codes to user clients."""
    def __init__(self, url: str, status_code: int = 307, headers: list = None):
        headers = headers or []
        headers.append(("Location", url))
        super().__init__(content=None, status_code=status_code, headers=headers)
