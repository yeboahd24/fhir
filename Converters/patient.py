from datetime import datetime
from typing import List, Optional, Annotated, Dict
from pydantic import BaseModel, Field, model_validator
from pydantic.functional_validators import BeforeValidator
from enum import Enum
import re
import json


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


DateString = Annotated[str, BeforeValidator(validate_date_format)]


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

    @model_validator(mode="before")
    @classmethod
    def convert_string_to_list(cls, values):
        for field in ["given", "prefix", "suffix"]:
            if isinstance(values.get(field), str):
                values[field] = [values[field]]
        return values


class ContactPoint(BaseModel):
    system: ContactSystem = Field(..., description="Type of contact point")
    value: str = Field(..., description="The actual contact point details")
    use: Optional[ContactUse] = Field(None, description="Purpose of this contact point")

    @model_validator(mode="after")
    def validate_contact_value(self):
        if self.system == ContactSystem.EMAIL:
            if "@" not in self.value or "." not in self.value:
                raise ValueError("Invalid email format")
        elif self.system == ContactSystem.PHONE:
            cleaned = "".join(filter(str.isdigit, self.value))
            if not 8 <= len(cleaned) <= 15:
                raise ValueError("Invalid phone number length")
        return self


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

    @model_validator(mode="before")
    @classmethod
    def convert_line_to_list(cls, values):
        if isinstance(values.get("line"), str):
            values["line"] = [values["line"]]
        return values


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
    birthDate: Optional[DateString] = Field(
        None, description="Patient birth date in YYYY-MM-DD format"
    )
    addresses: Optional[List[Address]] = Field(None, description="Patient addresses")
    maritalStatus: Optional[str] = Field(
        None, description="Patient marital status code"
    )
    languages: Optional[List[Language]] = Field(None, description="Patient languages")

    @model_validator(mode="after")
    def validate_names(self):
        if not any(
            name.family or (name.given and len(name.given) > 0) for name in self.names
        ):
            raise ValueError(
                "At least one name must have either a family name or a given name"
            )
        return self


class FHIRPatientConverter:
    """
    Converts and validates frontend form data to FHIR Patient Resource format using Pydantic
    """

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
            # First validate the input data using Pydantic
            validated_data = PatientInput(**form_data)

            # Create the base resource
            patient_resource = {"resourceType": "Patient", "active": True}

            # Add identifiers
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

            # Add names
            if validated_data.names:
                patient_resource["name"] = [
                    {k: v for k, v in name.model_dump().items() if v is not None}
                    for name in validated_data.names
                ]

            # Add telecom
            if validated_data.contacts:
                patient_resource["telecom"] = [
                    {
                        "system": contact.system,
                        "value": contact.value,
                        "use": contact.use,
                    }
                    for contact in validated_data.contacts
                ]

            # Add gender
            if validated_data.gender:
                patient_resource["gender"] = validated_data.gender

            # Add birth date
            if validated_data.birthDate:
                patient_resource["birthDate"] = validated_data.birthDate

            # Add addresses
            if validated_data.addresses:
                patient_resource["address"] = [
                    {k: v for k, v in address.model_dump().items() if v is not None}
                    for address in validated_data.addresses
                ]

            # Add marital status
            if validated_data.maritalStatus:
                patient_resource["maritalStatus"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                            "code": validated_data.maritalStatus,
                        }
                    ]
                }

            # Add communication
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
        "contacts": [{"system": "phone", "value": "555-0123", "use": "home"}],
        "addresses": [
            {
                "use": "home",
                "type": "physical",
                "line": ["123 Main St"],
                "city": "Boston",
                "state": "MA",
                "postalCode": "02115",
                "country": "USA",
            }
        ],
    }

    try:
        # This will both validate and convert the data
        converter = FHIRPatientConverter()
        fhir_patient = converter.convert_to_fhir(sample_input)
        print("Conversion successful!")
        print(json.dumps(fhir_patient, indent=2))
    except Exception as e:
        print(f"Conversion failed: {str(e)}")
