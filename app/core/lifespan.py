import inspect

class LifespanManager:
    """
    Orchestrates the ASGI Lifespan protocol state loops, safely firing 
    registered application hooks during server bootup and teardown.
    """

    def __init__(self):
        self.startup_handlers = []
        self.shutdown_handlers = []

    def register_startup(self, func):
        """Registers a callback function to run on application startup."""
        self.startup_handlers.append(func)

    def register_shutdown(self, func):
        """Registers a callback function to run on application shutdown."""
        self.shutdown_handlers.append(func)

    async def handle_loop(self, receive, send):
        """
        Listens for ASGI lifespan operational events and systematically triggers 
        the associated callback pipelines, signaling back status to the server.
        """
        while True:
            message = await receive()
            
            # --- STARTUP PHASE ---
            if message['type'] == 'lifespan.startup':
                try:
                    # Fire all startup hooks sequentially
                    for handler in self.startup_handlers:
                        if inspect.iscoroutinefunction(handler): 
                            await handler()
                        else: 
                            handler()
                    # Acknowledge successful startup to ASGI server
                    await send({'type': 'lifespan.startup.complete'})
                except Exception as e:
                    # Abort bootup and report failure
                    await send({'type': 'lifespan.startup.failed', 'message': str(e)})
                    break
                    
            # --- SHUTDOWN PHASE ---
            elif message['type'] == 'lifespan.shutdown':
                try:
                    # Fire all clean shutdown/cleanup hooks sequentially
                    for handler in self.shutdown_handlers:
                        if inspect.iscoroutinefunction(handler): 
                            await handler()
                        else: 
                            handler()
                    # Acknowledge clean shutdown completion
                    await send({'type': 'lifespan.shutdown.complete'})
                except Exception as e:
                    # Report cleanup error
                    await send({'type': 'lifespan.shutdown.failed', 'message': str(e)})
                break
