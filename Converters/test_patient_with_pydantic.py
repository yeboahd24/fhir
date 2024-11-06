from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum
import json
import re
from pydantic import field_validator
import uuid


class FHIRValidationError(Exception):
    pass


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class NameUse(str, Enum):
    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    NICKNAME = "nickname"
    ANONYMOUS = "anonymous"
    OLD = "old"
    MAIDEN = "maiden"


class ContactSystem(str, Enum):
    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    PAGER = "pager"
    URL = "url"
    SMS = "sms"
    OTHER = "other"


class ContactUse(str, Enum):
    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    MOBILE = "mobile"


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


def validate_date_format(v: str) -> str:
    if not v:
        return v
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        raise ValueError("Date must be in YYYY-MM-DD format")
    try:
        date = datetime.strptime(v, "%Y-%m-%d")
        year = date.year
        current_year = datetime.now().year
        if not (1900 <= year <= current_year):
            raise ValueError("Birth year must be between 1900 and current year")
    except ValueError as e:
        raise ValueError(f"Invalid date: {str(e)}")
    return v


class IdentifierType(BaseModel):
    system: str = Field(..., description="URL of the coding system")
    code: str = Field(..., description="Code from the system")


class Identifier(BaseModel):
    system: str = Field(..., description="System that defines the identifier")
    value: str = Field(..., description="The value that is unique within the system")
    type: Optional[str] = Field(None, description="Type of identifier")


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

    @field_validator("given", "prefix", "suffix", mode="before")
    def convert_string_to_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class ContactPoint(BaseModel):
    system: ContactSystem = Field(..., description="Type of contact point")
    value: str = Field(..., description="The actual contact point details")
    use: Optional[ContactUse] = Field(None, description="Purpose of this contact point")

    @field_validator("value")
    def validate_contact_value(cls, v, values):
        system = values.get("system")
        if system == ContactSystem.EMAIL:
            if "@" not in v or "." not in v:
                raise ValueError("Invalid email format")
        elif system == ContactSystem.PHONE:
            cleaned = "".join(filter(str.isdigit, v))
            if not 8 <= len(cleaned) <= 15:
                raise ValueError("Invalid phone number length")
        return v


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

    @field_validator("line", mode="before")
    def convert_line_to_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class Language(BaseModel):
    code: str = Field(..., description="Language code (BCP-47)")
    display: str = Field(..., description="Language display name")
    preferred: Optional[bool] = Field(
        False, description="Language preference indicator"
    )


class PatientInput(BaseModel):
    identifiers: Optional[List[Identifier]] = Field(
        None, description="Patient identifiers"
    )
    names: List[HumanName] = Field(
        ..., min_items=1, description="Patient names (at least one required)"
    )
    contacts: Optional[List[ContactPoint]] = Field(
        None, description="Patient contact points"
    )
    gender: Optional[Gender] = Field(None, description="Patient gender")
    birthDate: Optional[str] = Field(
        None, description="Patient birth date in YYYY-MM-DD format"
    )  # Changed to str
    addresses: Optional[List[Address]] = Field(None, description="Patient addresses")
    maritalStatus: Optional[str] = Field(
        None, description="Patient marital status code"
    )
    languages: Optional[List[Language]] = Field(None, description="Patient languages")

    @field_validator("birthDate")
    def validate_birth_date(cls, v):
        if v:
            return validate_date_format(v)  # Reuse your existing validation logic
        return v

    @field_validator("names")
    def validate_names(cls, v):
        if not any(name.family or (name.given and len(name.given) > 0) for name in v):
            raise ValueError(
                "At least one name must have either a family name or a given name"
            )
        return v


class FHIRPatientConverter:
    """
    Converts and validates frontend form data to FHIR Patient Resource format using Pydantic
    """

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
        """
        Convert frontend form data to FHIR Patient Resource

        Args:
            form_data (Dict): The form data from frontend

        Returns:
            Dict: FHIR Patient Resource

        Raises:
            FHIRValidationError: If validation fails
        """
        try:
            validated_data = PatientInput(**form_data)
            patient_resource = {
                "resourceType": "Patient",
                "id": FHIRPatientConverter.generate_id(),  # Auto-generate the ID
                "active": True,
            }

            if validated_data.identifiers:
                patient_resource["identifier"] = [
                    {
                        "system": identifier.system,
                        "value": identifier.value,
                        "type": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                    "code": identifier.type,
                                }
                            ]
                        }
                        if identifier.type
                        else None,
                    }
                    for identifier in validated_data.identifiers
                ]

            if validated_data.names:
                patient_resource["name"] = [
                    {k: v for k, v in name.dict().items() if v is not None}
                    for name in validated_data.names
                ]

            if validated_data.contacts:
                patient_resource["telecom"] = [
                    {
                        "system": contact.system,
                        "value": contact.value,
                        "use": contact.use,
                    }
                    for contact in validated_data.contacts
                ]

            if validated_data.gender:
                patient_resource["gender"] = validated_data.gender

            if validated_data.birthDate:
                patient_resource["birthDate"] = validated_data.birthDate

            if validated_data.addresses:
                patient_resource["address"] = [
                    {k: v for k, v in address.dict().items() if v is not None}
                    for address in validated_data.addresses
                ]

            if validated_data.maritalStatus:
                patient_resource["maritalStatus"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                            "code": validated_data.maritalStatus,
                        }
                    ]
                }

            if validated_data.languages:
                patient_resource["communication"] = [
                    {
                        "language": {
                            "coding": [
                                {
                                    "system": "urn:ietf:bcp:47",
                                    "code": lang.code,
                                    "display": lang.display,
                                }
                            ]
                        },
                        "preferred": lang.preferred,
                    }
                    for lang in validated_data.languages
                ]

            return patient_resource

        except Exception as e:
            raise FHIRValidationError(f"Failed to convert to FHIR format: {str(e)}")


# Example usage:
if __name__ == "__main__":
    sample_input = {
        "names": [
            {
                "use": "official",
                "family": "Smith",
                "given": ["John", "Peter"],
                "prefix": ["Mr"],
            }
        ],
        "gender": "male",
        "birthDate": "1990-01-01",
        "addresses": [
            {
                "use": "home",
                "line": ["123 Elm St"],
                "city": "Somewhere",
                "state": "CA",
                "postalCode": "90210",
                "country": "USA",
            }
        ],
    }

    converter = FHIRPatientConverter()
    try:
        fhir_data = converter.convert_to_fhir(sample_input)
        print(json.dumps(fhir_data, indent=4))
    except FHIRValidationError as e:
        print(str(e))
