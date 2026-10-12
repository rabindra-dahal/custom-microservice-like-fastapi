class Field:
    """
    Defines verification boundaries for individual request body fields.
    """
    def __init__(self, data_type: type, required: bool = True, default: any = None):
        self.data_type = data_type
        self.required = required
        self.default = default

class BaseModel:
    """
    A lightweight declarative contract class used to perform 
    Pydantic-like structural body validation checks.
    """
    def __init__(self, **kwargs):
        # Populates object attributes after clean validation passes
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def validate_dict(cls, incoming_data: dict) -> tuple:
        """
        Validates an incoming raw dictionary against declared class annotations.
        Returns: (validated_model_instance, error_details_list)
        """
        errors = []
        cleaned_fields = {}
        
        # 1. Gather all data schemas specified on the model class definition
        class_annotations = getattr(cls, "__annotations__", {})
        
        for field_name, expected_type in class_annotations.items():
            # Extract configuration constraints if declared as a Field class instance
            field_config = getattr(cls, field_name, None)
            
            is_required = True
            default_val = None
            
            if isinstance(field_config, Field):
                expected_type = field_config.data_type
                is_required = field_config.required
                default_val = field_config.default

            raw_value = incoming_data.get(field_name)

            # 2. Assert requirement parameters
            if raw_value is None:
                if is_required:
                    errors.append(f"Body missing required property field: '{field_name}'")
                else:
                    cleaned_fields[field_name] = default_val
                continue

            # 3. Assert precise type matching boundaries (Supports nested models!)
            if isinstance(expected_type, type) and issubclass(expected_type, BaseModel):
                if not isinstance(raw_value, dict):
                    errors.append(f"Field '{field_name}' expected a nested JSON object structure, got '{type(raw_value).__name__}'")
                else:
                    # Recursive validation for nested schema validation trees
                    nested_instance, nested_errors = expected_type.validate_dict(raw_value)
                    if nested_errors:
                        errors.extend([f"{field_name}.{err}" for err in nested_errors])
                    else:
                        cleaned_fields[field_name] = nested_instance
            else:
                # Standard scalar primitive verification matching logic
                if not isinstance(raw_value, expected_type):
                    errors.append(f"Field '{field_name}' expected type '{expected_type.__name__}', got '{type(raw_value).__name__}'")
                else:
                    cleaned_fields[field_name] = raw_value

        if errors:
            return None, errors
        return cls(**cleaned_fields), []
