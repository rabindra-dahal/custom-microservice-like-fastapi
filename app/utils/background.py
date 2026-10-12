import asyncio
import inspect

class BackgroundTasks:
    """
    A collection of tasks to be executed in the background after 
    the HTTP response has been sent to the client.
    """
    def __init__(self):
        self.tasks = []

    def add_task(self, func: callable, *args, **kwargs):
        """
        Schedule a function to be executed in the background.
        """
        self.tasks.append((func, args, kwargs))

    async def execute_all(self):
        """
        Triggers all scheduled tasks asynchronously.
        """
        for func, args, kwargs in self.tasks:
            try:
                if inspect.iscoroutinefunction(func):
                    # Fire async task concurrently
                    asyncio.create_task(func(*args, **kwargs))
                else:
                    # Run sync tasks inside an executor thread block to avoid locking the loop
                    loop = asyncio.get_running_loop()
                    loop.run_in_executor(None, lambda: func(*args, **kwargs))
            except Exception as task_error:
                print(f"[Background Tasks] Error executing task {func.__name__}: {task_error}")
