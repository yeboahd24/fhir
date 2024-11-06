from patient import FHIRPatientConverter, FHIRValidationError
import json 


form_data = {
    "names": [{
        "use": "official",
        "family": "Smith",
        "given": ["John", "Peter"],
        "prefix": "Mr"
    }],
    "gender": "male",
    "birthDate": "1990-01-01",
    "contacts": [{
        "system": "phone",
        "value": "+1-555-555-5555",
        "use": "home"
    }],
    "addresses": [{
        "use": "home",
        "type": "physical",
        "line": ["123 Main St"],
        "city": "Boston",
        "state": "MA",
        "postalCode": "02108",
        "country": "USA"
    }],
    "identifiers": [{
        "system": "http://hospital.com/patients",
        "value": "12345",
        "type": "MR"
    }],
    "languages": [{
        "code": "en",
        "display": "English",
        "preferred": True
    }]
}

try:
    fhir_patient = FHIRPatientConverter.convert_to_fhir(form_data)
    print(json.dumps(fhir_patient, indent=2))
except FHIRValidationError as e:
    print(f"Validation error: {e}")
