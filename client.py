#!/usr/bin/env python
"""
MCP Client for Business Requests Server

This client connects to the Business Requests MCP server and uses OpenAI
to interact with business requests data.
"""

import asyncio
from contextlib import AsyncExitStack
import json
import logging
import os
from typing import Any, Dict, List, Optional
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Load environment variables - for Azure OpenAI credentials
from dotenv import load_dotenv
# MCP Client SDK
from mcp import ClientSession
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp.types import PromptMessage, TextContent
# OpenAI SDK
from openai import AsyncOpenAI, AzureOpenAI

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
azure_openai_uri        = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version             = os.getenv("AZURE_OPENAI_VERSION", "2024-05-01-preview")
mcp_server_url          = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")

aoi = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=str(azure_openai_uri),
    azure_ad_token_provider=token_provider,
)

class MCPClient:
    """MCP Client for interacting with an MCP Streamable HTTP server
    code heavily based off:
    https://github.com/invariantlabs-ai/mcp-streamable-http/blob/main/python-example/client/client.py
    """

    def __init__(self):
        # Initialize session and client objects
        self.client: Optional[Client] = None
        self.exit_stack = AsyncExitStack()
        self.aoi = AzureOpenAI(
                            api_version=api_version,
                            azure_endpoint=str(azure_openai_uri),
                            azure_ad_token_provider=token_provider,
                        )

    async def connect_to_streamable_http_server(
        self, server_url: str, headers: Optional[dict] = None
    ):
        """Connect to an MCP server running with HTTP Streamable transport"""
        transport = StreamableHttpTransport(server_url)
        self.client = Client(transport)


    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""
        async with self.client:
            system_prompt = await self.client.get_prompt("business_request_prompt", {"language": "en"})
            messages = []
            for message in system_prompt.messages:
                if message.content.type == "text":
                    messages.append(
                        {
                            "role": message.role,
                            "content": message.content.text,
                        }
                    )
            messages.append({"role": "user", "content": query})

            response = await self.client.list_tools()
            #logger.debug(f"Available tools: {response.tools}")
            # should be a fasterway to do this, such as using the tool.inputSchema directly, but couldn't do it quickly.
            # mcp is also supported directly in OpenAI API now ... you can just pass the server directly.
            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": tool.inputSchema.get("properties", {}),
                            "required": tool.inputSchema.get("required", []),
                        },
                    },
                }
                for tool in response
                if tool.name != "get_business_requests_context"
            ]

            # available_tools.append([
            #     [{
            #         "type": "mcp",
            #         "server_label": "business_requests",
            #         "server_url": mcp_server_url,
            #     }]
            # ])

            additional_tools_required = True
            final_text = []
            while additional_tools_required:

                response = self.aoi.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=available_tools,
                )
                message = response.choices[0].message
                #logger.debug(f"Message Received: {message}")

                if message.content:
                    final_text.append(message.content)

                if hasattr(message, "tool_calls") and message.tool_calls:
                    #logger.debug(f"Tool calls: {message.tool_calls}")
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        result = await self.client.call_tool(tool_name, tool_args)
                        logger.debug(f"[Called tool {tool_name} with args {tool_args}]")
                        final_text.append(f"[Called tool {tool_name} with args {tool_args}]")
                        # Continue conversation with tool results
                        if hasattr(message, "content") and message.content:
                            messages.append({"role": "assistant", "content": message.content})
                        messages.append({"role": "user", "content": result.content})
                else:
                    additional_tools_required = False #exit clause

            return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                if query.lower() == "context":
                    # Get context from the server
                    async with self.client:
                        result = await self.client.call_tool('get_business_requests_context', {})
                        result = json.loads(result.content[0].text)
                        if 'metadata' in result:
                            print("\nContext: \n", result['metadata'])
                    continue

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Properly clean up the session and streams"""
        if self.client:
            await self.client.close()

async def main():
    """Main function to demonstrate the client"""

    client = MCPClient()

    try:
        await client.connect_to_streamable_http_server(mcp_server_url)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
