from pprint import pprint as pp  # noqa

import requests

####################
# Configure Requests
####################
session = requests.Session()
BASE_URL = "http://0.0.0.0:5560/fhir"
headers = {
    "User-Agent": "Jasper FHIR Client",
    "Content-Type": "application/fhir+json;charset=utf-8",
    "Accept": "application/fhir+json;charset=utf-8",
}
session.headers.update(headers)

#######################
# Create a Practitioner
#######################

practitioner_data = {
    "resourceType": "Practitioner",
    "id": "68935564-9414-49e6-a96a-6f6cb1a3fc67",
    "text": {
        "status": "generated",
        "div": '<div xmlns="http://www.w3.org/1999/xhtml">\n      <p>Dr Adam Careful is a Referring Practitioner for Acme Hospital from 1-Jan 2012 to 31-Mar\n        2012</p>\n    </div>',
    },
    "identifier": [{"system": "http://www.acme.org/practitioners", "value": "23"}],
    "active": True,
    "name": [{"family": "Careful", "given": ["Adam"], "prefix": ["Dr"]}],
    "address": [
        {
            "use": "home",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postalCode": "3999",
        }
    ],
    "qualification": [
        {
            "identifier": [
                {"system": "http://example.org/UniversityIdentifier", "value": "12345"}
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0360/2.7",
                        "code": "BS",
                        "display": "Bachelor of Science",
                    }
                ],
                "text": "Bachelor of Science",
            },
            "period": {"start": "1995"},
            "issuer": {"display": "Example University"},
        }
    ],
}

# resp = session.put(
#     f"{BASE_URL}/Practitioner/{practitioner_data['id']}", json=practitioner_data
# )
# Should create a new Practitioner
# pp(resp.json())
# assert resp.status_code == 201


###########################"""
# Fetch Practitioner
#############################

resp = session.get(f"{BASE_URL}/Practitioner/{practitioner_data['id']}")
pp(resp.json())
