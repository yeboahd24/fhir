from patient import FHIRPatientConverter, FHIRValidationError
import json 

# Example 1: Invalid gender value
invalid_gender_data = {
    "names": [{
        "use": "official",
        "family": "Smith",
        "given": ["John"]
    }],
    "gender": "invalid_gender",  # Invalid! Should be male/female/other/unknown
    "birthDate": "1990-01-01"
}

# Example 2: Invalid date format
invalid_date_data = {
    "names": [{
        "use": "official",
        "family": "Smith",
        "given": ["John"]
    }],
    "gender": "male",
    "birthDate": "01/01/1990"  # Invalid! Should be YYYY-MM-DD
}

# Example 3: Invalid contact system
invalid_contact_data = {
    "names": [{
        "use": "official",
        "family": "Smith",
        "given": ["John"]
    }],
    "contacts": [{
        "system": "whatsapp",  # Invalid! Not in allowed contact systems
        "value": "+1234567890",
        "use": "home"
    }]
}

# Example 4: Invalid name use
invalid_name_data = {
    "names": [{
        "use": "nickname2",  # Invalid! Not in allowed name uses
        "family": "Smith",
        "given": ["John"]
    }]
}

# Example 5: Missing required name
missing_name_data = {
    "gender": "male",
    "birthDate": "1990-01-01"
    # Missing names field (required)
}

# Example 6: Multiple invalid fields
multiple_invalid_data = {
    "names": [{
        "use": "invalid_use",  # Invalid name use
        "family": "Smith",
        "given": ["John"]
    }],
    "gender": "invalid_gender",  # Invalid gender
    "birthDate": "01-01-90",    # Invalid date format
    "contacts": [{
        "system": "invalid_system",  # Invalid contact system
        "value": "+1234567890",
        "use": "invalid_use"         # Invalid contact use
    }],
    "addresses": [{
        "use": "invalid_use",        # Invalid address use
        "type": "invalid_type",      # Invalid address type
        "line": ["123 Main St"],
        "city": "Boston"
    }]
}

def test_invalid_data():
    test_cases = [
        ("Invalid Gender Test", invalid_gender_data),
        ("Invalid Date Test", invalid_date_data),
        ("Invalid Contact System Test", invalid_contact_data),
        ("Invalid Name Use Test", invalid_name_data),
        ("Missing Name Test", missing_name_data),
        ("Multiple Invalid Fields Test", multiple_invalid_data)
    ]
    
    for test_name, test_data in test_cases:
        print(f"\n=== {test_name} ===")
        try:
            FHIRPatientConverter.convert_to_fhir(test_data)
            print("Conversion succeeded (unexpected!)")
        except FHIRValidationError as e:
            print(f"Validation Error (expected): {e}")

# Run the tests
test_invalid_data()
