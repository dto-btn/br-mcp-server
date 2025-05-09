import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional
from pydantic import ValidationError

from mcp.server.fastmcp import Context, FastMCP

from business_request.br_models import BRQuery
from business_request.br_prompts import BITS_SYSTEM_PROMPT_EN, BITS_SYSTEM_PROMPT_FR
from business_request.br_utils import get_br_query
from business_request.database import DatabaseConnection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@dataclass
class BRContext:
    """Context for Business Request operations"""
    database: DatabaseConnection
    # Add other context items like database connections here if needed

@asynccontextmanager
async def br_lifespan(server: FastMCP) -> AsyncIterator[BRContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize resources on startup
    db = DatabaseConnection(os.getenv("BITS_DB_SERVER", "missing.domain"),
                            os.getenv("BITS_DB_USERNAME", "missing.username"),
                            os.getenv("BITS_DB_PWD", "missing.password"),
                            os.getenv("BITS_DB_DATABASE", "missing.dbname"))
    # You could also initialize database connections or other resources here
    
    # Yield the context to the server
    try:
        yield BRContext(database=db)
    finally:
        # Cleanup resources on shutdown
        pass  # Add cleanup code here if needed

# Create an MCP server with lifespan management
mcp = FastMCP("Business Requests", 
              version="1.0.0", 
              lifespan=br_lifespan,
              dependencies=["pydantic"])  # Add any dependencies your server needs

@mcp.tool()

@mcp.tool()
async def get_br_database_query(query: BRQuery) -> str:
    """Returns the BR database query
    
    Args:
        query: The business request query parameters

    Returns:
        The generated SQL query string
    """
    try:
        user_query = BRQuery.model_validate_json(query)
        logger.info("Valided query: %s", user_query)

        # Prepare the SQL statement for this request.
        sql_query = get_br_query(limit=bool(user_query.limit),
                                            br_filters=user_query.query_filters,
                                            active=True,
                                            status=len(user_query.statuses) if user_query.statuses else 0)
        return sql_query
    except (json.JSONDecodeError, ValidationError) as e:
        # Handle validation errors
        logger.error("Validation failed!")
        return {
            "error": str(e)
            }

@mcp.tool()
def get_br_by_number(br_numbers: list[int]) -> str:
    """Returns a BR requests by their numbers"""
    return f"super br no {str(br_numbers)}!"

@mcp.prompt(description="""Business Request Prompt.
            Anything that relates to BR (Business Request) should be handled by this prompt.
            Ask for 'en' or 'fr'""")
def business_request_prompt(language: str) -> str:
    """Prompt for business request"""
    return BITS_SYSTEM_PROMPT_FR if language == "fr" else BITS_SYSTEM_PROMPT_EN

if __name__ == "__main__":
    mcp.run(transport="streamable-http") # supported since 2.3.0
