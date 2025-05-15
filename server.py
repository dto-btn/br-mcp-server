import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, ValidationError

from business_request.br_fields import BRFields
from business_request.br_models import BRQuery, FilterParams
from business_request.br_prompts import (BITS_SYSTEM_PROMPT_EN,
                                         BITS_SYSTEM_PROMPT_FR)
from business_request.br_statuses_cache import StatusesCache
from business_request.br_utils import get_br_query
from business_request.database import DatabaseConnection

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@dataclass
class BRContext:
    """Context for Business Request operations"""
    database: DatabaseConnection
    results: Optional[str] = None

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[BRContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize resources on startup
    db = DatabaseConnection(os.getenv("BITS_DB_SERVER", "missing.domain"),
                            os.getenv("BITS_DB_USERNAME", "missing.username"),
                            os.getenv("BITS_DB_PWD", "missing.password"),
                            os.getenv("BITS_DB_DATABASE", "missing.dbname"))

    # Yield the context to the server
    try:
        yield BRContext(database=db)
    finally:
        # Cleanup resources on shutdown
        pass  # Add cleanup code here if needed

# Create an MCP server with lifespan management
mcp = FastMCP("Business Requests",
              version="1.0.0",
              lifespan=server_lifespan,
              dependencies=["pydantic", "pandas"])  # Add any dependencies your server needs

@mcp.tool()
async def search_business_requests(query: BRQuery, ctx: Context) -> dict:
    """Returns the BR database query

    Args:
        query: The business request query parameters

    Returns:
        The generated SQL query string
    """
    await ctx.info(f"Validated query: {query}")
    # Prepare the SQL statement for this request.
    sql_query = get_br_query(limit=bool(query.limit),
                                        br_filters=query.query_filters,
                                        active=True,
                                        status=len(query.statuses) if query.statuses else 0)

    # Build query parameters dynamically, #1 statuses, #2 all other fields, #3 limit
    query_params = []
    if query.statuses:
        query_params.extend(query.statuses)
    for query_filter in query.query_filters:
        if query_filter.is_date():
            query_params.append(query_filter.value)
        else:
            query_params.append(f"%{query_filter.value}%")
    query_params.append(query.limit)
    result = ctx.request_context.lifespan_context.database.execute_query(sql_query, *query_params)
    result["brquery"] = query.model_dump()
    ctx.request_context.lifespan_context.results = result
    return result

@mcp.tool()
def get_br_by_number(br_numbers: list[int], ctx: Context) -> dict:
    """Returns a BR requests by their numbers"""
    #BRs here do not need to be active to be returned
    query = get_br_query(len(br_numbers), active=False)
    result = ctx.request_context.lifespan_context.database.execute_query(query, *br_numbers)
    ctx.request_context.lifespan_context.results = result
    return result

@mcp.tool()
def get_business_requests_context(ctx: Context) -> str:
    """Returns the context of the business requests"""
    # Check if results are available in the context
    if ctx.request_context.lifespan_context.results:
        return ctx.request_context.lifespan_context.results
    else:
        raise ValueError("No business request results found in context")

@mcp.tool()
def get_br_statuses_and_phases() -> dict:
    """
    This will retreive the code table BR_STATUSES (Active == True)
        (and distinct DISP_STATUS_EN, since we dont want duplicates)

    WITH DistinctStatus AS (
        SELECT DISP_STATUS_EN, MIN(STATUS_ID) AS MinStatusID
        FROM [EDR_CARZ].[DIM_BITS_STATUS]
        WHERE BR_ACTIVE_EN = 'Active'
        GROUP BY DISP_STATUS_EN
    )
    SELECT
        t.STATUS_ID,
        ds.DISP_STATUS_EN AS NAME_EN,
        t.DISP_STATUS_FR AS NAME_FR,
        t.BITS_PHASE_EN AS PHASE_EN,
        t.BITS_PHASE_FR AS PHASE_FR
    FROM
        DistinctStatus AS ds
    JOIN
        [EDR_CARZ].[DIM_BITS_STATUS] AS t
    ON
        ds.DISP_STATUS_EN = t.DISP_STATUS_EN AND ds.MinStatusID = t.STATUS_ID
    WHERE
        t.BR_ACTIVE_EN = 'Active';
    """
    return { "statuses": StatusesCache.get_statuses() }

@mcp.tool()
def get_organization_names(ctx: Context) -> dict:
    """
    This will retreive organization so AI can look them up.
    """
    query = """
    SELECT GC_ORG_NAME_EN, GC_ORG_NAME_FR, ORG_SHORT_NAME, ORG_ACRN_EN, ORG_ACRN_FR, ORG_ACRN_BIL, ORG_WEBSITE
    FROM EDR_CARZ.DIM_GC_ORGANIZATION
    """
    return ctx.request_context.lifespan_context.database.execute_query(query, result_key="org_names")

@mcp.tool()
def valid_search_fields() -> dict:
    """
    This function returns all the valid search fields
    """
    fields_with_descriptions = {
        key: {
            'description': value.get('description', ''),
            'is_user_field': value.get('is_user_field', False)
        }
        for key, value in BRFields.valid_search_fields_no_statuses.items()
    }

    return {
        "field_names": json.dumps(fields_with_descriptions)
    }

@mcp.prompt(description="""Business Request Prompt.
            Anything that relates to BR (Business Request) should be handled by this prompt.
            Ask for 'en' or 'fr'""")
def business_request_prompt(language: str) -> str:
    """Prompt for business request"""
    return BITS_SYSTEM_PROMPT_FR if language == "fr" else BITS_SYSTEM_PROMPT_EN

@mcp.tool()
def filter_results(filters: list[FilterParams], ctx: Context) -> dict:
    """
    Filters the results in the context using pandas DataFrame operations.

    Args:
        filters: List of filter parameters to apply to the results
                Each filter is a dictionary with keys:
                - column: The column name to filter on
                - value: The value to filter by
                - operator: The operator to use (eq, neq, gt, lt, gte, lte, contains, startswith, endswith)

    Returns:
        Filtered results as a dictionary
    """        # Check if results are available in the context
    if ctx.request_context.lifespan_context.results and "br" in ctx.request_context.lifespan_context.results:
        # Log the filter parameters for debugging
        logger.debug(f"Applying filters: {filters}")

        results = ctx.request_context.lifespan_context.results
        data = results["br"]

        # Convert to DataFrame with explicit index
        df = pd.DataFrame(data, index=range(len(data)))

        # Apply filters sequentially
        filtered_df = df.copy()
        for filter_param in filters:
            filtered_df = filter_param.apply_filter(filtered_df)

        # Convert filtered DataFrame back to dictionary format
        filtered_result = filtered_df.to_dict(orient="records")

        # Update the context with filtered results
        results["br"] = filtered_result
        ctx.request_context.lifespan_context.results = results

        return results
    return []

if __name__ == "__main__":
    mcp.run(transport="streamable-http") # supported since 2.3.0
