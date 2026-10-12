import inspect
from ..utils.dependencies import Depends

class DependencyInjector:
    """
    Handles automatic inversion of control (IoC) and dependency injection.
    Recursively scans and executes functions marked with the Depends class
    to satisfy multi-layered execution graphs.
    """

    async def resolve(self, callable_obj):
        """
        Inspects a function's parameters via reflection, locates nested 
        sub-dependencies, resolves them first by recursing down the tree, 
        and then executes the parent callable.
        """
        sig = inspect.signature(callable_obj)
        dep_kwargs = {}
        
        # Scan function signature for parameter markers using Depends instances
        for param_name, param in sig.parameters.items():
            if isinstance(param.default, Depends):
                nested_callable = param.default.dependency_callable
                
                # RECURSIVE CALL: Resolve down the tree to satisfy sub-dependencies
                dep_kwargs[param_name] = await self.resolve(nested_callable)
        
        # Execute the callable dependency (handling both async and sync definitions safely)
        if inspect.iscoroutinefunction(callable_obj):
            return await callable_obj(**dep_kwargs)
        return callable_obj(**dep_kwargs)
