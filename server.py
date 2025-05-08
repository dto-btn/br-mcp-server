from mcp.server.fastmcp import FastMCP

from business_request.br_models import BRQuery
from business_request.br_prompts import BITS_SYSTEM_PROMPT_EN, BITS_SYSTEM_PROMPT_FR
from business_request.br_utils import BRQueryBuilder

mcp = FastMCP("Business Requests", "1.0.0")

query_builder = BRQueryBuilder()

@mcp.resource("database://{query}")
def get_br_database_query(query: BRQuery) -> str:
    """Returns the BR database query"""
    print("Query: ", query)
    return query_builder.get_br_query(query)

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
