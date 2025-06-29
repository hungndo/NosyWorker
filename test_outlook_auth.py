import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_outlook_auth():
    try:
        # Set environment variables
        os.environ['OUTLOOK_CLIENT_ID'] = 'dcb19bb8-79ea-4b1d-ac28-7c05ed3b4c0e'
        os.environ['OUTLOOK_CLIENT_SECRET'] = 'tvt8Q~~mj82y5VVOrsAV2F-Hs5i00PD1cUJcncld%'
        
        # Create MCP server parameters for Outlook
        outlook_mcp_script = '../outlook-mcp/index.js'
        server_params = StdioServerParameters(
            command="node",
            args=[outlook_mcp_script],
            env=None,
        )
        
        print("Testing Outlook MCP authentication...")
        
        # Connect to Outlook MCP server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test authentication status
                print("Testing authentication status...")
                result = await session.call_tool('check-auth-status', arguments={})
                
                if result.content and len(result.content) > 0:
                    print(f"Auth result: {result.content[0].text}")
                    
                    # If not authenticated, try to authenticate
                    if "Not authenticated" in result.content[0].text:
                        print("Not authenticated. Trying to authenticate...")
                        auth_result = await session.call_tool('authenticate', arguments={})
                        if auth_result.content and len(auth_result.content) > 0:
                            print(f"Auth response: {auth_result.content[0].text}")
                else:
                    print("No response from auth check")
                    
    except Exception as e:
        print(f"Error testing Outlook auth: {e}")

if __name__ == "__main__":
    asyncio.run(test_outlook_auth()) 