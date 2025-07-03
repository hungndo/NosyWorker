import json
import os
import re
from datetime import datetime
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport, StdioTransport
from together import Together
from typing import List, Dict, Optional
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Create the transport with your MCP server URL
server_url = "http://0.0.0.0:8000/mcp"
transport = StreamableHttpTransport(server_url)

# Initialize the client with the transport
client = Client(transport=transport)
together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

# Create a client for Outlook MCP
outlook_mcp_script = '../outlook-mcp/index.js'
server_params = StdioServerParameters(
    command="node",  # Executable
    args=[outlook_mcp_script],  # Command line arguments
    env=None,  # Optional environment variables
)

def load_channels():
    try:
        with open('configs/channels.json', 'r') as f:
            data = json.load(f)
            return data['channels']
    except FileNotFoundError:
        return []

def save_channels(channels):
    with open('configs/channels.json', 'w') as f:
        json.dump({'channels': channels}, f, indent=4)

async def fetch_slack_conversation(channel_id, start_dt: str, end_dt: str):
    """Fetch messages from a Slack channel or thread."""
    async with client:
        # Fetch channel messages
        try:
            result = await client.call_tool(
                "get_channel_history",
                {
                    "channel_id": channel_id,
                    "oldest": start_dt,
                    "latest": end_dt
                }
            )
        except Exception as e:
            print(e)
        
        # Parse the raw response
        raw_response = json.loads(result[0].text).get('result', {})
        
        # Extract and format conversation
        conversation = []
        if raw_response.get("ok") and "messages" in raw_response:
            for msg in raw_response["messages"]:
                # Skip system messages and channel events
                if msg.get("subtype") in ["channel_name", "channel_join"]:
                    continue
                    
                # Get sender name from bot_profile or user
                sender = "Unknown"
                if "bot_profile" in msg:
                    sender = msg["bot_profile"].get("name", "Unknown Bot")
                elif "user" in msg:
                    sender = f"User {msg['user']}"
                
                # Get message text
                text = msg.get("text", "")
                
                # Convert timestamp to readable format
                timestamp = datetime.fromtimestamp(float(msg["ts"]))
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                # Add formatted message to conversation
                conversation.append({
                    "sender": sender,
                    "text": text,
                    "timestamp": formatted_time
                })
        
        return conversation

async def summarize_conversation(conversation, model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"):
    """Summarize the conversation using TogetherAI and save to file."""
    system_prompt = """
    Summary instructions:
    - You are a helpful assistant that summarizes conversations in chat messages.
    - You will be given a conversation and you will need to summarize it very concisely.
    - Focus and list out key points, decisions made, and tasks assigned.
    - Present the summary in a nice Markdown format.
    - The format of the output should be:
    **Key Points**
    * key point 1
    * key point 2
    * ...

    **Decisions Made**
    * decision 1
    * decision 2
    * ...

    **Tasks Assigned**
    * task assignment 1
    * task assignment 2
    * ...
    
    """
    try:
        print(f"[DEBUG] System prompt: {system_prompt}")
        print(f"[DEBUG] Conversation: {conversation}")
        response = together_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation}
            ],
        )
    except Exception as e:
        print(e)
    summary = response.choices[0].message.content
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/summary_{timestamp}.md"
    
    # Save summary to file
    with open(filename, 'w') as f:
        f.write(summary)
    
    return summary 

async def fetch_outlook_emails(folder_name: str, number_of_recent_emails) -> List[Dict]:
    """
    Fetch emails from a specified Outlook folder.
    """
    # async with client:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            emails = []
            # List recent emails
            try:
                tool_args = {
                    "folder": folder_name,
                    "count": number_of_recent_emails
                }
                list_result = await session.call_tool('list-emails', arguments=tool_args)
                print(list_result)
            except Exception as e:
                print(f"[DEBUG] Exception in list-emails: {e}")
                return emails
            # Extract email IDs from the plain text response
            try:
                list_response_text = list_result.content[0].text
                email_ids = [line.split("ID: ")[1] for line in list_response_text.splitlines() if line.startswith("ID: ")]
            except Exception as e:
                return print(e)
            
            if email_ids:
                for email_id in email_ids:
                    print(email_id)
                    try:
                        tool_args = {
                            "id": email_id
                        }
                        read_result = await session.call_tool('read-email', arguments=tool_args)
                        print(read_result)
                    except Exception as e:
                        print(f"[DEBUG] Exception in read-email: {e}")
                        return emails
                    
                    email_content = read_result.content[0].text
                    if email_content:
                        lines = email_content.splitlines()
                        headers = {}
                        body_start_index = 0
                        for i, line in enumerate(lines):
                            if not line.strip():
                                body_start_index = i + 1
                                break
                            if ': ' in line:
                                key, value = line.split(': ', 1)
                                headers[key.lower()] = value.strip()
                            else:
                                body_start_index = i
                                break
                        else:
                            body_start_index = len(lines)
                        body = "\n".join(lines[body_start_index:]).strip()
                        sender_full = headers.get("from", "")
                        sender_name = sender_full
                        sender_address = ""
                        match = re.search(r'(.*) \((.*)\)', sender_full)
                        if match:
                            sender_name = match.group(1).strip()
                            sender_address = match.group(2).strip()
                        elif sender_full:
                            sender_address = sender_full
                        emails.append({
                            "sender": sender_name,
                            "address": sender_address,
                            "subject": headers.get("subject", "No Subject"),
                            "body": body,
                            "contentType": "Text",
                            "receivedDateTime": headers.get("date")
                        })
            print("[DEBUG] Exiting async with outlook_client block")
            return emails 

async def check_outlook_auth_status() -> bool:
    """
    Check authentication status with the Outlook MCP server.
    Returns True if authenticated, otherwise False.
    """
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                result = await session.call_tool('check-auth-status')
                # The result is expected to be in result.content[0].text
                status_text = result.content[0].text.strip()
                return status_text == "Authenticated and ready"
            except Exception as e:
                print(f"[DEBUG] Exception in check-auth-status: {e}")
                return False 

async def authenticate_outlook() -> str:
    """
    Call the 'authenticate' tool from the Outlook MCP server and return the authentication link.
    """
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                await session.call_tool('authenticate')
            except Exception as e:
                print(f"[DEBUG] Exception in authenticate: {e}")
            return "http://localhost:3333/auth?client_id=" 
        
async def send_outlook_email(to_email, subject, message):

    # Connect to Outlook MCP server and send email
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize() 
            # Call the send-email tool
            result = await session.call_tool('send-email', arguments={
                'to': to_email,
                'subject': subject,
                'body': message,
                'importance': 'normal',
                'saveToSentItems': True
            })

            return result