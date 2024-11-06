import uuid  # For generating the ID
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

import json


class FHIRValidationError(Exception):
    pass


class NameUse(str, Enum):
    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    NICKNAME = "nickname"
    ANONYMOUS = "anonymous"
    OLD = "old"
    MAIDEN = "maiden"


class AddressUse(str, Enum):
    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    BILLING = "billing"


class AddressType(str, Enum):
    POSTAL = "postal"
    PHYSICAL = "physical"
    BOTH = "both"


class Coding(BaseModel):
    system: str = Field(..., description="System URL for the coding")
    code: str = Field(..., description="Code value from the system")
    display: Optional[str] = Field(None, description="Display text for the code")


class CodeableConcept(BaseModel):
    coding: List[Coding] = Field(..., description="A list of codings")
    text: Optional[str] = Field(
        None, description="Plain text representation of the concept"
    )


class IdentifierType(BaseModel):
    system: str = Field(..., description="URL of the coding system")
    value: str = Field(..., description="Code from the system")


class HumanName(BaseModel):
    use: Optional[NameUse] = Field(None, description="The use of this name")
    family: Optional[str] = Field(
        None, description="Family name (often called 'Surname')"
    )
    given: Optional[List[str]] = Field(
        None, description="Given names (not always 'first'). Includes middle names"
    )
    prefix: Optional[List[str]] = Field(
        None, description="Parts that come before the name"
    )
    suffix: Optional[List[str]] = Field(
        None, description="Parts that come after the name"
    )

    @classmethod
    def validate_name(cls, v):
        if not v.family and not (v.given and len(v.given) > 0):
            raise ValueError("A family or given name must be provided.")
        return v


class Qualification(BaseModel):
    identifier: Optional[List[IdentifierType]] = Field(
        None, description="Identifier for the qualification"
    )
    code: CodeableConcept = Field(
        ..., description="Qualification code with coding and text"
    )
    period: Optional[Dict[str, str]] = Field(
        None, description="Period of qualification"
    )
    issuer: Optional[Dict[str, str]] = Field(
        None, description="Issuer of qualification"
    )


class Address(BaseModel):
    use: Optional[AddressUse] = Field(None, description="Purpose of this address")
    type: Optional[AddressType] = Field(None, description="Postal, physical, etc.")
    line: Optional[List[str]] = Field(
        None, description="Street name, number, direction & P.O. Box etc."
    )
    city: Optional[str] = Field(None, description="Name of city, town etc.")
    state: Optional[str] = Field(
        None, description="Sub-unit of country (state, region, province etc.)"
    )
    postalCode: Optional[str] = Field(None, description="Postal code for area")
    country: Optional[str] = Field(
        None, description="Country (e.g. can be ISO 3166 2 or 3 letter code)"
    )


#
# class Qualification(BaseModel):
#     identifier: Optional[List[IdentifierType]] = Field(
#         None, description="Identifier for the qualification"
#     )
#     code: Dict[str, str] = Field(
#         ..., description="Qualification code with coding and text"
#     )
#     period: Optional[Dict[str, str]] = Field(
#         None, description="Period of qualification"
#     )
#     issuer: Optional[Dict[str, str]] = Field(
#         None, description="Issuer of qualification"
#     )
#


class PractitionerInput(BaseModel):
    identifier: Optional[List[IdentifierType]] = Field(
        None, description="Practitioner identifiers"
    )
    active: Optional[bool] = Field(
        None, description="Whether the practitioner is active"
    )
    name: List[HumanName] = Field(..., min_items=1, description="Practitioner names")
    address: Optional[List[Address]] = Field(None, description="Practitioner addresses")
    qualification: Optional[List[Qualification]] = Field(
        None, description="Practitioner qualifications"
    )


class FHIRPractitionerConverter:
    @staticmethod
    def generate_id() -> str:
        """
        Generates a unique ID for the FHIR resource. Can be replaced with more complex logic if needed.

        Returns:
            str: A generated ID (UUID4).
        """
        return str(uuid.uuid4())  # Using UUID4 for unique ID generation

    @staticmethod
    def convert_to_fhir(form_data: Dict) -> Dict:
        try:
            validated_data = PractitionerInput(**form_data)
            practitioner_resource = {
                "resourceType": "Practitioner",
                "id": FHIRPractitionerConverter.generate_id(),  # Auto-generate the ID
                "active": validated_data.active or True,
                "text": {
                    "status": "generated",
                    "div": '<div xmlns="http://www.w3.org/1999/xhtml"><p>Practitioner Details</p></div>',
                },
            }

            if validated_data.identifier:
                practitioner_resource["identifier"] = [
                    {"system": identifier.system, "value": identifier.value}
                    for identifier in validated_data.identifier
                ]

            if validated_data.name:
                practitioner_resource["name"] = [
                    {k: v for k, v in name.dict().items() if v is not None}
                    for name in validated_data.name
                ]

            if validated_data.address:
                practitioner_resource["address"] = [
                    {k: v for k, v in address.dict().items() if v is not None}
                    for address in validated_data.address
                ]

            if validated_data.qualification:
                practitioner_resource["qualification"] = [
                    {
                        "identifier": [
                            {"system": idf.system, "value": idf.value}
                            for idf in qual.identifier
                        ]
                        if qual.identifier
                        else None,
                        "code": {
                            "coding": [
                                {
                                    "system": coding.system,
                                    "code": coding.code,
                                    "display": coding.display,
                                }
                                for coding in qual.code.coding
                            ],
                            "text": qual.code.text,
                        },
                        "period": qual.period,
                        "issuer": qual.issuer,
                    }
                    for qual in validated_data.qualification
                ]

            return practitioner_resource

        except Exception as e:
            raise FHIRValidationError(f"Failed to convert to FHIR format: {str(e)}")


if __name__ == "__main__":
    sample_input = {
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
                    {
                        "system": "http://example.org/UniversityIdentifier",
                        "value": "12345",
                    }
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

    converter = FHIRPractitionerConverter()
    try:
        fhir_data = converter.convert_to_fhir(sample_input)
        print(json.dumps(fhir_data, indent=4))
    except FHIRValidationError as e:
        print(str(e))
