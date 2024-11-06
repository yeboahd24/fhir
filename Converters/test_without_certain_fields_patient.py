from patient import FHIRPatientConverter, FHIRValidationError
import json 




# Example 1: Valid data without addresses (perfectly fine)
data_without_addresses = {
    "names": [{
        "use": "official",
        "family": "Smith",
        "given": ["John"]
    }],
    "gender": "male",
    "birthDate": "1990-01-01",
    "contacts": [{
        "system": "phone",
        "value": "+1234567890",
        "use": "home"
    }]
}

# Example 2: Valid data with addresses
data_with_valid_addresses = {
    "names": [{
        "use": "official",
        "family": "Smith",
        "given": ["John"]
    }],
    "gender": "male",
    "birthDate": "1990-01-01",
    "addresses": [{
        "use": "home",
        "type": "physical",
        "line": ["123 Main St"],
        "city": "Boston",
        "state": "MA",
        "postalCode": "02108"
    }]
}

# Example 3: Data with invalid addresses (will cause error)
data_with_invalid_addresses = {
    "names": [{
        "use": "official",
        "family": "Smith",
        "given": ["John"]
    }],
    "gender": "male",
    "birthDate": "1990-01-01",
    "addresses": [{
        "use": "invalid_use",  # This will cause an error
        "type": "physical",
        "line": ["123 Main St"],
        "city": "Boston"
    }]
}

def test_address_validation():
    # Test 1: Without addresses
    print("\n=== Test: Valid Data Without Addresses ===")
    try:
        result = FHIRPatientConverter.convert_to_fhir(data_without_addresses)
        print("Success! Resulting FHIR resource:")
        print(json.dumps(result, indent=2))
    except FHIRValidationError as e:
        print(f"Error (unexpected): {e}")

    # Test 2: With valid addresses
    print("\n=== Test: Valid Data With Addresses ===")
    try:
        result = FHIRPatientConverter.convert_to_fhir(data_with_valid_addresses)
        print("Success! Resulting FHIR resource:")
        print(json.dumps(result, indent=2))
    except FHIRValidationError as e:
        print(f"Error (unexpected): {e}")

    # Test 3: With invalid addresses
    print("\n=== Test: Data With Invalid Addresses ===")
    try:
        result = FHIRPatientConverter.convert_to_fhir(data_with_invalid_addresses)
        print("Success (unexpected)!")
    except FHIRValidationError as e:
        print(f"Validation Error (expected): {e}")

# Run the tests
test_address_validation()
