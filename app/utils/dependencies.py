class Depends:
    """
    A marker class used to declare dependencies within route signatures.
    Instructs the injection engine to execute the specified callable before running the endpoint.
    """
    def __init__(self, dependency_callable):
        # Store the target function/callable that needs to be resolved
        self.dependency_callable = dependency_callable
