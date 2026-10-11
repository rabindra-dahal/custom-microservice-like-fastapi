import json

class Response:
    def __init__(self, content: any = None, status_code: int = 200, headers: list = None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or []
        self.media_type = None
        
    def render(self) -> bytes:
        if self.content is None:
            return b""
        if isinstance(self.content, bytes):
            return self.content
        return str(self.content).encode("utf-8")

    def get_headers(self) -> list:
        # Build out headers array matching ASGI byte-pair formats
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
    def __init__(self, content: any, status_code: int = 200, headers: list = None):
        super().__init__(content, status_code, headers)
        self.media_type = "application/json"

    def render(self) -> bytes:
        return json.dumps(self.content).encode("utf-8")


class HTMLResponse(Response):
    def __init__(self, content: str, status_code: int = 200, headers: list = None):
        super().__init__(content, status_code, headers)
        self.media_type = "text/html; charset=utf-8"


class RedirectResponse(Response):
    def __init__(self, url: str, status_code: int = 307, headers: list = None):
        headers = headers or []
        headers.append(("Location", url))
        super().__init__(content=None, status_code=status_code, headers=headers)
