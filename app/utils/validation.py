class QueryField:
    """
    Defines strict structural validation and parsing rules for a single query parameter field.
    """
    def __init__(self, default: any = None, required: bool = False, min_val: float = None, max_val: float = None):
        self.default = default
        self.required = required
        self.min_val = min_val
        self.max_val = max_val

class QueryValidator:
    """
    Evaluates incoming query strings against defined schemas, handles safe type parsing,
    and reports clear error tracking fields when validation fails.
    """
    @staticmethod
    def validate(incoming_params: dict, schema: dict, annotations: dict) -> tuple:
        """
        Validates and transforms query values.
        Returns: (validated_parameters_dict, error_details_list)
        """
        errors = []
        validated = {}

        for field_name, rule in schema.items():
            # Ensure rule is a QueryField instance
            if not isinstance(rule, QueryField):
                continue

            raw_val = incoming_params.get(field_name)
            target_type = annotations.get(field_name, str)

            # 1. Handle Missing Fields
            if raw_val is None:
                if rule.required:
                    errors.append(f"Field '{field_name}' is required but was not provided.")
                else:
                    validated[field_name] = rule.default
                continue

            # 2. Type Coercion
            try:
                if target_type is bool:
                    # Special parsing for string-boolean values
                    coerced_val = raw_val.lower() in ("true", "1", "yes")
                else:
                    coerced_val = target_type(raw_val)
            except (ValueError, TypeError):
                errors.append(f"Field '{field_name}' expected type '{target_type.__name__}', got '{raw_val}'.")
                continue

            # 3. Numeric Boundary Checking
            if isinstance(coerced_val, (int, float)):
                if rule.min_val is not None and coerced_val < rule.min_val:
                    errors.append(f"Field '{field_name}' value {coerced_val} is below minimum allowed value ({rule.min_val}).")
                    continue
                if rule.max_val is not None and coerced_val > rule.max_val:
                    errors.append(f"Field '{field_name}' value {coerced_val} exceeds maximum allowed value ({rule.max_val}).")
                    continue

            validated[field_name] = coerced_val

        return validated, errors
