from fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import logging
from datetime import datetime
import time

# Initialize MCP server
bot_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
user_client = WebClient(token=os.environ.get("SLACK_USER_TOKEN"))
logger = logging.getLogger(__name__)
mcp = FastMCP(name="My MCP Server")


@mcp.tool
def list_public_channels() -> dict:
    """Return all public channels in the Slack workspace"""
    try:
        response = bot_client.conversations_list()
        return {"result": response.data}
    except SlackApiError as e:
        logger.error(f"Error listing channels: {e}")
        return {"result": None, "error": str(e)}
        

@mcp.tool
def get_channel_history(channel_id: str, limit: int = 100, oldest: str = "", latest: str = "") -> dict:
    """Get message history from a Slack channel
    
    Args:
        channel_id: The ID of the channel to get history from
        limit: Maximum number of messages to retrieve (default: 100)
        oldest: Start of time range of messages to include (Unix timestamp)
        latest: End of time range of messages to include (Unix timestamp)
    """
    try:
        all_messages = []
        cursor = None
        
        while True:
            params = {
                "channel": channel_id,
                "limit": limit
            }
            if oldest != "":
                params["oldest"] = oldest
            if latest != "":
                params["latest"] = latest
            if cursor:
                params["cursor"] = cursor
                
            response = bot_client.conversations_history(**params)
            
            # Add messages from this batch to our collection
            if response.data.get("messages"):
                all_messages.extend(response.data["messages"])
            
            # Check if there are more messages to fetch
            cursor = response.data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
                
        # Create a new response object with all messages
        response.data["messages"] = all_messages
        return {"result": response.data}
    except SlackApiError as e:
        logger.error(f"Error getting channel history: {e}")
        return {"result": None, "error": str(e)}


@mcp.tool
def datetime_to_timestamp(dt: str) -> dict:
    """Convert a datetime string to Unix timestamp
    
    Args:
        dt: Datetime string in format 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'
    """
    try:
        # Try parsing with time first, if fails try date only
        try:
            dt_obj = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            dt_obj = datetime.strptime(dt, '%Y-%m-%d')
        
        timestamp = time.mktime(dt_obj.timetuple())
        return {"result": str(timestamp)}
    except Exception as e:
        logger.error(f"Error converting datetime: {e}")
        return {"result": None, "error": str(e)}


@mcp.tool
def get_thread_replies(channel_id: str, thread_ts: str, limit: int = 100) -> dict:
    """Get replies from a Slack message thread
    
    Args:
        channel_id: The ID of the channel containing the thread
        thread_ts: The timestamp of the parent message that started the thread
        limit: Maximum number of replies to retrieve (default: 100)
    """
    try:
        response = bot_client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=limit
        )
        return {"result": response.data}
    except SlackApiError as e:
        logger.error(f"Error getting thread replies: {e}")
        return {"result": None, "error": str(e)}


@mcp.tool
def search_messages(query: str, count: int = 100, sort: str = "timestamp", sort_dir: str = "desc") -> dict:
    """Search for messages in Slack
    
    Args:
        query: The search query (supports Slack's search syntax)
        count: Maximum number of results to return (default: 100)
        sort: Sort results by "timestamp" or "score" (default: "timestamp")
        sort_dir: Sort direction "asc" or "desc" (default: "desc")
    """
    try:
        response = user_client.search_messages(
            query=query,
            count=count,
            sort=sort,
            sort_dir=sort_dir
        )
        return {"result": response.data}
    except SlackApiError as e:
        logger.error(f"Error searching messages: {e}")
        return {"result": None, "error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000, path="/mcp")