from pydantic import BaseModel, Field, field_validator

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
    query_filters: list[BRQueryFilter] = Field(..., description="List of filters to apply to the query.")
    limit: int = Field(9000, description="Maximum number of records to return. Optional. Defaults to 9000.") #It's over 9000!
    statuses: list[str] = Field([], description="List of of STATUS_ID to filter by.")

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

class BusinessRequest(BaseModel):
    """Model for a Business Request."""
    BR_NMBR: float = Field(..., description="Business request number")
    EXTRACTION_DATE: str = Field(None, description="Date the data was extracted")
    LEAD_PRODUCT_EN: str = Field(None, description="The Lead Product associated with the BR in English")
    LEAD_PRODUCT_FR: str = Field(None, description="The Lead Product associated with the BR in French")
    BR_SHORT_TITLE: str = Field(..., description="Title which relates to the Business Request (BR)")
    RPT_GC_ORG_NAME_EN: str = Field(None, description="The primary partner/client requesting the BR in English")
    RPT_GC_ORG_NAME_FR: str = Field(None, description="The primary partner/client requesting the BR in French")
    ORG_TYPE_EN: str = Field(None, description="Organization type in English")
    ORG_TYPE_FR: str = Field(None, description="Organization type in French")
    BR_TYPE_EN: str = Field(None, description="BR type in English")
    BR_TYPE_FR: str = Field(None, description="BR type in French")
    PRIORITY_EN: str = Field(None, description="The priority of the request in English")
    PRIORITY_FR: str = Field(None, description="The priority of the request in French")
    CPLX_EN: str = Field(None, description="The complexity of the BR in English")
    CPLX_FR: str = Field(None, description="The complexity of the BR in French")
    SCOPE_EN: str = Field(None, description="Scope of the BR in English")
    SCOPE_FR: str = Field(None, description="Scope of the BR in French") 
    CLIENT_SUBGRP_EN: str = Field(None, description="Client subgroup in English")
    CLIENT_SUBGRP_FR: str = Field(None, description="Client subgroup in French")
    GROUP_EN: str = Field(None, description="Group in English")
    GROUP_FR: str = Field(None, description="Group in French")
    ASSOC_BRS: str = Field(None, description="Associated BRs")
    BR_ACTIVE_EN: str = Field(None, description="Active status of the BR in English")
    BR_ACTIVE_FR: str = Field(None, description="Active status of the BR in French")
    ACC_MANAGER_OPI: str = Field(None, description="Account Manager OPI")
    AGR_OPI: str = Field(None, description="Agreement OPI")
    BA_OPI: str = Field(None, description="Business Analyst OPI")
    BA_PRICING_OPI: str = Field(None, description="Business Analyst Pricing OPI")
    BA_PRICING_TL: str = Field(None, description="Business Analyst Pricing Team Lead")
    BA_TL: str = Field(None, description="Business Analyst Team Lead")
    CSM_DIRECTOR: str = Field(None, description="Client Executive")
    EAOPI: str = Field(None, description="EA OPI/BPR AE")
    PM_OPI: str = Field(None, description="PM Coordinator")
    QA_OPI: str = Field(None, description="QA OPI")
    SDM_TL_OPI: str = Field(None, description="Service Delivery Manager Team Lead")
    TEAMLEADER: str = Field(None, description="Team Leader")
    WIO_OPI: str = Field(None, description="WIO OPI")
    GCIT_CAT_EN: str = Field(None, description="GCIT Category in English")
    GCIT_CAT_FR: str = Field(None, description="GCIT Category in French")
    GCIT_PRIORITY_EN: str = Field(None, description="GCIT Priority in English")
    GCIT_PRIORITY_FR: str = Field(None, description="GCIT Priority in French")
    IO_ID: str = Field(None, description="IO ID")
    EPS_NMBR: str = Field(None, description="EPS Number")
    ECD_NMBR: str = Field(None, description="ECD Number")
    PROD_OPI: str = Field(None, description="Production OPI")
    PHASE_EN: str = Field(None, description="Phase in English")
    PHASE_FR: str = Field(None, description="Phase in French")
    BR_OWNER: str = Field(None, description="The OPI responsible for the BR")
    REQST_IMPL_DATE: str = Field(None, description="Requested implementation date")
    SUBMIT_DATE: str = Field(None, description="Date the BR was created in BITS")
    RVSD_TARGET_IMPL_DATE: str = Field(None, description="Revised target implementation date")
    ACTUAL_IMPL_DATE: str = Field(None, description="Actual implementation date")
    AGRMT_END_DATE: str = Field(None, description="Agreement end date")
    PRPO_TARGET_DATE: str = Field(None, description="PRPO target date")
    IMPL_SGNOFF_DATE: str = Field(None, description="Implementation sign-off date")
    CLIENT_REQST_SOL_DATE: str = Field(None, description="Client requested solution date")
    TARGET_IMPL_DATE: str = Field(None, description="Target implementation date")
    BITS_STATUS_EN: str = Field(None, description="The current BITS BR status in English")
    BITS_STATUS_FR: str = Field(None, description="The current BITS BR status in French")
    TotalCount: int = Field(None, description="Total count of records")

    class Config:
        """Pydantic config."""
        populate_by_name = True

class Metadata(BaseModel):
    """Metadata for the results."""
    execution_time: float = Field(..., description="Time taken to execute the query in seconds")
    results: int = Field(..., description="Number of business requests returned in this response")
    total_rows: int = Field(..., description="Total number of business requests matching the query")
    extraction_date: str = Field(None, description="Date when the data was extracted")

class BrResults(BaseModel):
    """Results of a business request query."""
    br: list[BusinessRequest] = Field(..., description="List of business requests")
    metadata: Metadata = Field(..., description="Metadata about the results")
