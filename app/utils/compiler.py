import re

# Central mapping for pattern builders and conversions
TYPE_CASTERS = {
    "int": (r"\d+", int),
    "float": (r"\d+(?:\.\d+)?", float),
    "str": (r"[^/]+", str),
}

class RouteCompiler:
    """
    Handles parsing parameter syntax from URL strings (e.g., '{item_id:int}'),
    generating clean compiled regular expressions, and managing type casters.
    """
    
    @staticmethod
    def compile_dynamic_path(path: str) -> tuple:
        """
        Parses path variables and transforms user strings into named regex groups.
        Returns: (compiled_regex_object, casters_dictionary)
        """
        pattern = path
        casters = {}
        
        # Extract parameter tokens out of curly brace declarations
        markers = re.findall(r'{([^}]+)}', path)
        for marker in markers:
            if ':' in marker:
                name, type_str = marker.split(':', 1)
            else:
                name, type_str = marker, 'str'
            
            # Fetch regex match string and matching caster conversion rules
            regex_str, converter = TYPE_CASTERS.get(type_str, TYPE_CASTERS['str'])
            casters[name] = converter
            
            # Swap path token for a named capture group regex statement
            pattern = pattern.replace(f"{{{marker}}}", f"(?P<{name}>{regex_str})")
            
        return re.compile(f"^{pattern}$"), casters

    @staticmethod
    def coerce_parameters(raw_params: dict, casters: dict) -> dict:
        """
        Applies type conversion rules to string variables extracted from paths.
        """
        cast_params = {}
        for name, val in raw_params.items():
            caster = casters.get(name, str)
            try:
                cast_params[name] = caster(val)
            except ValueError:
                cast_params[name] = val  # Fallback on parsing exceptions
        return cast_params
