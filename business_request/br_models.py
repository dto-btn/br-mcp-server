from pydantic import BaseModel, Field, field_validator
from typing import Optional

from business_request.br_fields import BRFields
from business_request.br_statuses_cache import StatusesCache

class BRQueryFilter(BaseModel):
    """Model for BRQueryFilter."""
    name: str = Field(..., description="Name of the database field", )
    value: str = Field(..., description="Value of the field")
    operator: str = Field(..., description="Operator, must be one of '=', '<', '>', '<=' or '>='")

    # Validator for the 'operator' field
    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Validate the operator field."""
        if v not in {"=", "<", ">", "<=", ">="}:
            raise ValueError("Operator, must be one of '=', '<', '>', '<=' or '>='")
        return v

    # Validator for the 'name' field
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate the name field.Ensure its a valid DB field"""
        if v not in BRFields.valid_search_fields_no_statuses:
            raise ValueError(f"Name must be one of {list(BRFields.valid_search_fields_no_statuses.keys())}")
        return v

    def is_date(self) -> bool:
        """Check if the field is a date."""
        return str(self.name).endswith("_DATE")

class BRQuery(BaseModel):
    """Represent the query that the AI does on behalf of the user"""
    query_filters: Optional[list[BRQueryFilter]] = Field(..., description="List of filters to apply to the query.")
    limit: Optional[int] = Field(9000, description="Maximum number of records to return. Optional. Defaults to 9000.") #It's over 9000!
    statuses: Optional[list[str]] = Field([], description="List of of STATUS_ID to filter by.")

    # Validator for the 'statuses' field
    @field_validator("statuses")
    @classmethod
    def validate_statuses(cls, v: list[str]) -> list[str]:
        """Validate the statuses field."""
        valid_statuses = StatusesCache.get_status_ids()
        invalid = [status for status in v if status not in valid_statuses]
        if invalid:
            raise ValueError(f"Invalid STATUS_ID(s): {invalid}. Must be one of: {sorted(valid_statuses)}")
        return v

