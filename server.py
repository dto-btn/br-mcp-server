import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from pydantic import ValidationError

from business_request.br_models import BRQuery, BrResults, BusinessRequest, Metadata
from business_request.br_prompts import (BITS_SYSTEM_PROMPT_EN,
                                         BITS_SYSTEM_PROMPT_FR)
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
    results: Optional[BrResults] = None

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
              dependencies=["pydantic"])  # Add any dependencies your server needs

@mcp.tool()
async def search_business_requests(query: BRQuery, ctx: Context) -> str:
    """Returns the BR database query
    
    Args:
        query: The business request query parameters

    Returns:
        The generated SQL query string
    """
    ctx.info(f"Validated query: {query}")
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
    
    # Create BrResults object from the query result
    try:
        # Extract metadata
        metadata = Metadata(
            execution_time=result["metadata"]["execution_time"],
            results=result["metadata"]["results"],
            total_rows=result["metadata"]["total_rows"],
            extraction_date=result["metadata"]["extraction_date"]
        )
        
        # Create BrResults object
        br_results = BrResults(
            br=result["br"],
            metadata=metadata
        )
        
        # Store results in the context
        ctx.request_context.lifespan_context.results = br_results
        ctx.info(f"Stored {len(br_results.br)} business requests in context")
    except Exception as e:
        ctx.error(f"Failed to create BrResults object: {str(e)}")
    
    # Append the original query to the result (keep for compatibility)
    result["brquery"] = query.model_dump()
    return result

@mcp.tool()
def get_br_by_number(br_numbers: list[int], ctx: Context) -> str:
    """Returns a BR requests by their numbers"""
    #BRs here do not need to be active to be returned
    query = get_br_query(len(br_numbers), active=False)
    return ctx.request_context.lifespan_context.database.execute_query(query, *br_numbers)

@mcp.tool()
def get_business_requests_context(ctx: Context) -> BrResults:
    """Returns the context of the business requests"""
    # Check if results are available in the context
    if ctx.request_context.lifespan_context.results:
        return ctx.request_context.lifespan_context.results
    else:
        raise ValueError("No business request results found in context")

@mcp.prompt(description="""Business Request Prompt.
            Anything that relates to BR (Business Request) should be handled by this prompt.
            Ask for 'en' or 'fr'""")
def business_request_prompt(language: str) -> str:
    """Prompt for business request"""
    return BITS_SYSTEM_PROMPT_FR if language == "fr" else BITS_SYSTEM_PROMPT_EN

if __name__ == "__main__":
    mcp.run(transport="streamable-http") # supported since 2.3.0
