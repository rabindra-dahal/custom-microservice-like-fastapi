import time

class RateLimiter:
    """
    An ultra-lean sliding window rate limiter tracking client interactions 
    at native dictionary lookup speeds.
    """
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.client_records = {} # Map structure: { client_ip: [timestamps] }

    def is_allowed(self, client_ip: str) -> bool:
        """
        Evaluates connection history logs. Removes expired timestamps 
        and asserts velocity thresholds.
        """
        current_time = time.time()
        
        # Initialize record arrays if the IP is new
        if client_ip not in self.client_records:
            self.client_records[client_ip] = []
            
        timestamps = self.client_records[client_ip]

        # SLIDING WINDOW: Remove timestamps that fall outside the active tracking window
        while timestamps and (current_time - timestamps[0] > self.window_seconds):
            timestamps.pop(0)

        # Assert if the count of valid recent requests fits under the threshold
        if len(timestamps) < self.requests_limit:
            timestamps.append(current_time)
            return True
            
        return False
