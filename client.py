#!/usr/bin/env python
"""
MCP Client for Business Requests Server

This client connects to the Business Requests MCP server and uses OpenAI
to interact with business requests data.
"""

import asyncio
import os
import json
from typing import Dict, List, Any, Optional
import logging

# OpenAI SDK
from openai import AsyncOpenAI

# MCP Client SDK
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import PromptMessage, TextContent

# Load environment variables - for Azure OpenAI credentials 
from dotenv import load_dotenv

# Business Request Models
from business_request.br_models import BRQuery, BRQueryFilter

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")

# Optional OpenAI API base URL (if using a non-standard endpoint)
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")


class BusinessRequestClient:
    """Client for interacting with the Business Requests MCP server"""
    
    def __init__(self, server_url: str = MCP_SERVER_URL):
        """Initialize the client with the MCP server URL"""
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self._openai_client = None
        
    async def connect(self):
        """Connect to the MCP server"""
        try:
            self._read_stream, self._write_stream, _ = await streamablehttp_client(self.server_url)
            self.session = ClientSession(self._read_stream, self._write_stream)
            await self.session.initialize()
            logger.info(f"Connected to MCP server: {self.server_url}")
            
            # List available tools
            tools = await self.session.list_tools()
            logger.info(f"Available tools: {', '.join([t.name for t in tools])}")
            
            # List available prompts
            prompts = await self.session.list_prompts()
            logger.info(f"Available prompts: {', '.join([p.name for p in prompts])}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            raise
    
    async def close(self):
        """Close the connection to the MCP server"""
        if self.session:
            await self.session.close()
            logger.info("Disconnected from MCP server")
    
    @property
    def openai_client(self):
        """Get or create an OpenAI client"""
        if self._openai_client is None:
            # Configure OpenAI client with API key
            client_kwargs = {
                "api_key": OPENAI_API_KEY,
            }
            
            # Add custom base URL if provided
            if OPENAI_API_BASE:
                client_kwargs["base_url"] = OPENAI_API_BASE
                
            self._openai_client = AsyncOpenAI(**client_kwargs)
            logger.info("Created OpenAI client")
        
        return self._openai_client
    
    async def get_valid_search_fields(self) -> Dict[str, Dict[str, Any]]:
        """Get valid search fields for business requests"""
        if not self.session:
            raise ValueError("Not connected to MCP server")
        
        result = await self.session.call_tool("valid_search_fields")
        field_names = json.loads(result["field_names"])
        return field_names
    
    async def get_statuses_and_phases(self) -> Dict[str, List[Dict[str, str]]]:
        """Get business request statuses and phases"""
        if not self.session:
            raise ValueError("Not connected to MCP server")
        
        result = await self.session.call_tool("get_br_statuses_and_phases")
        return result
    
    async def search_business_requests(self, query: BRQuery) -> Dict[str, Any]:
        """Search for business requests based on the provided query"""
        if not self.session:
            raise ValueError("Not connected to MCP server")
        
        # Convert Pydantic model to dict for the MCP call
        query_dict = query.model_dump()
        result = await self.session.call_tool("search_business_requests", query_dict)
        return result
    
    async def get_br_by_number(self, br_numbers: List[int]) -> Dict[str, Any]:
        """Get business requests by their numbers"""
        if not self.session:
            raise ValueError("Not connected to MCP server")
        
        result = await self.session.call_tool("get_br_by_number", {"br_numbers": br_numbers})
        return result
    
    async def get_business_request_prompt(self, language: str = "en") -> str:
        """Get the business request prompt for the specified language"""
        if not self.session:
            raise ValueError("Not connected to MCP server")
        
        prompt_result = await self.session.get_prompt("business_request_prompt", {"language": language})
        # Extract the prompt text from the result
        for message in prompt_result.messages:
            if isinstance(message, PromptMessage) and hasattr(message.content, "text"):
                return message.content.text
        
        return "No prompt text found"
    
    async def chat_about_business_requests(self, user_query: str, language: str = "en") -> str:
        """Use OpenAI to chat about business requests"""
        try:
            # Get the system prompt for business requests
            system_prompt = await self.get_business_request_prompt(language)
            
            # Get valid search fields for context
            fields = await self.get_valid_search_fields()
            field_info = f"Valid search fields: {json.dumps(fields, indent=2)}"
            
            # Get statuses for context
            statuses = await self.get_statuses_and_phases()
            status_info = f"Status information: {json.dumps(statuses, indent=2)}"
            
            # Create the chat completion
            response = await self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": field_info},
                    {"role": "user", "content": status_info},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Return the assistant's response
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in chat_about_business_requests: {str(e)}")
            return f"Error: {str(e)}"
    
    async def search_with_ai(self, user_query: str, language: str = "en") -> Dict[str, Any]:
        """
        Use OpenAI to construct a search query from natural language,
        then perform the search and return results
        """
        try:
            # Get the system prompt
            system_prompt = await self.get_business_request_prompt(language)
            
            # Get valid search fields for context
            fields = await self.get_valid_search_fields()
            
            # Get statuses for context
            statuses = await self.get_statuses_and_phases()
            
            # Create a prompt that asks the model to create a structured query
            search_prompt = f"""
            Based on the user's query: "{user_query}"
            
            Create a structured search query for business requests using these valid fields:
            {json.dumps(fields, indent=2)}
            
            And these status IDs: 
            {json.dumps([s['STATUS_ID'] for s in statuses.get('statuses', [])])}
            
            Respond with ONLY a valid JSON object that matches this Python class:
            ```python
            class BRQuery:
                query_filters: Optional[list[BRQueryFilter]] = Field(..., description="List of filters to apply to the query.")
                limit: Optional[int] = Field(9000, description="Maximum number of records to return.")
                statuses: Optional[list[str]] = Field([], description="List of STATUS_ID to filter by.")
                
            class BRQueryFilter:
                name: str = Field(..., description="Name of the database field")
                value: str = Field(..., description="Value of the field")
                operator: str = Field(..., description="Operator, must be one of '=', '<', '>', '<=' or '>='")
            ```
            
            Only include filters that are relevant to the user's query. Use the valid field names.
            Return ONLY the JSON, no explanations.
            """
            
            # Generate a structured query using OpenAI
            response = await self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": search_prompt}
                ],
                temperature=0,  # Use low temperature for more deterministic responses
                response_format={"type": "json_object"}
            )
            
            # Parse the response into a query
            query_json = response.choices[0].message.content.strip()
            query_dict = json.loads(query_json)
            
            # Create a BRQuery from the dict
            query = BRQuery.model_validate(query_dict)
            
            # Execute the search
            results = await self.search_business_requests(query)
            
            return {
                "query": query.model_dump(),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in search_with_ai: {str(e)}")
            return {"error": str(e)}


async def main():
    """Main function to demonstrate the client"""
    client = BusinessRequestClient()
    
    try:
        # Connect to the MCP server
        await client.connect()
        
        # Demo 1: Get valid search fields
        print("\n=== Demo 1: Get valid search fields ===")
        fields = await client.get_valid_search_fields()
        print(f"Available search fields: {json.dumps(fields, indent=2)}")
        
        # Demo 2: Get statuses and phases
        print("\n=== Demo 2: Get statuses and phases ===")
        statuses = await client.get_statuses_and_phases()
        print(f"Statuses and phases: {json.dumps(statuses, indent=2)}")
        
        # Demo 3: Chat about business requests
        print("\n=== Demo 3: Chat about business requests ===")
        chat_response = await client.chat_about_business_requests(
            "What are business requests and how can I search for them?")
        print(f"Chat response: {chat_response}")
        
        # Demo 4: Search with AI
        print("\n=== Demo 4: Search with AI ===")
        user_query = "Find all active business requests from the last month"
        search_results = await client.search_with_ai(user_query)
        print(f"Search query: {json.dumps(search_results.get('query', {}), indent=2)}")
        print(f"Found {len(search_results.get('results', {}).get('rows', []))} results")
        
    except Exception as e:
        print(f"Error in demo: {str(e)}")
    finally:
        # Close the connection
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
