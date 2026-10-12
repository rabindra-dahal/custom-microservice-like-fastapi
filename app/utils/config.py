import os

class BaseSettings:
    """
    A lightweight, declarative configuration loader. Parses environment variables
    from a local `.env` file and merges them with system environment properties.
    """
    def __init__(self, _env_file: str = ".env"):
        # 1. Read and load local .env file variables if present
        env_file_data = self._read_env_file(_env_file)
        
        # 2. Dynamically collect ALL configuration fields defined on the subclass
        config_keys = set()
        
        # Gather keys from type annotations (e.g., SECRET_KEY: str)
        class_annotations = getattr(self, "__annotations__", {})
        config_keys.update(class_annotations.keys())
        
        # Gather keys from standard attribute assignments (e.g., PORT = 8000), ignoring private items
        for attr in dir(self):
            if not attr.startswith("_") and not callable(getattr(self, attr)):
                config_keys.add(attr)
        
        print("\n[Config Loader] Scanning environment keys...")
        
        # 3. Process every single discovered config property
        for var_name in config_keys:
            expected_type = class_annotations.get(var_name, str)
            
            # Fetch existing default layout parameters safely
            default_value = getattr(self, var_name) if hasattr(self, var_name) else None
            
            # Lookup chain: System Env -> .env File -> Class Default Fallback
            raw_value = os.environ.get(var_name, env_file_data.get(var_name, default_value))
            
            if raw_value is not None:
                # Handle conversion rules
                if isinstance(raw_value, str):
                    coerced_value = self._coerce_type(raw_value, expected_type)
                else:
                    coerced_value = raw_value
                    
                setattr(self, var_name, coerced_value)
                print(f"  Loaded: {var_name} -> type: {type(coerced_value).__name__}")
            else:
                # Fail fast on server boot if a property is completely missing
                raise AttributeError(
                    f"\n[Configuration Error] Required variable '{var_name}' "
                    f"is missing from your environment variables and your local .env file!"
                )
        print("[Config Loader] All configuration settings loaded successfully.\n")

    def _read_env_file(self, env_file_path: str) -> dict:
        """Parses standard key-value configurations out of plain text .env files."""
        data = {}
        if not os.path.exists(env_file_path):
            print(f"  [Warning] Local environment file not found at: {os.path.abspath(env_file_path)}")
            return data
            
        with open(env_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    data[key.strip()] = value.strip().strip("'\"")
        return data

    def _coerce_type(self, raw_str: str, target_type: type) -> any:
        """Coerces strings into native Python datatypes."""
        if target_type is bool:
            return raw_str.lower() in ("true", "1", "yes", "on")
        try:
            return target_type(raw_str)
        except (ValueError, TypeError):
            return raw_str
