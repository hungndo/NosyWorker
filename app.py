from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import os
from together import Together
import json
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import markdown2  # Add markdown2 for markdown to HTML conversion

app = Flask(__name__)

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

# Create the transport with your MCP server URL
server_url = "http://0.0.0.0:8000/mcp"
transport = StreamableHttpTransport(server_url)

# Initialize the client with the transport
client = Client(transport=transport)
together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

async def fetch_slack_conversation(channel_id, start_dt: str, end_dt: str):
    """Fetch messages from a Slack channel or thread."""
    async with client:
        # Fetch channel messages
        result = await client.call_tool(
            "get_channel_history",
            {
                "channel_id": channel_id,
                "oldest": start_dt,
                "latest": end_dt
            }
        )
        
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

async def summarize_conversation(conversation, together_client, model="meta-llama/Meta-Llama-3-8B-Instruct-Lite"):
    """Summarize the conversation using TogetherAI."""
    system_prompt = """
    Summary instructions:
    - You are a helpful assistant that summarizes conversations in chat messages.
    - You will be given a conversation and you will need to summarize it very concisely.
    - Focus and list out key points, decisions made, and tasks assigned.
    - Present the summary in a nice Markdown format.
    - The format of the output should be:
    ** Key Points **
    * key point 1
    * key point 2
    * ...

    ** Decisions Made **
    * decision 1
    * decision 2
    * ...

    ** Tasks Assigned **
    * task assignment 1
    * task assignment 2
    * ...
    
    """

    response = together_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation}
        ],
    )

    return response.choices[0].message.content

# Load channels from JSON file
channels = load_channels()

@app.route('/')
def dashboard():
    return render_template('dashboard.html', 
                         channels=channels,
                         enabled_channels=channels)

@app.route('/api/channels/<channel_id>/profile', methods=['POST'])
def update_channel_profile(channel_id):
    data = request.json
    for channel in channels:
        if channel["id"] == channel_id:
            channel["profile"] = {
                "audience": data["audience"],
                "dataSources": data["dataSources"]
            }
            # Save changes to JSON file
            save_channels(channels)
            return jsonify({"success": True, "profile": channel["profile"]})
    return jsonify({"success": False, "error": "Channel not found"}), 404

@app.route('/api/channels/<channel_id>/summarize', methods=['POST'])
async def summarize_channel(channel_id):
    try:
        # Find channel in config and get its slack_channel_id
        channel = None
        for ch in channels:
            if ch["id"] == channel_id:
                channel = ch
                break
                
        if not channel or "slack_channel_id" not in channel:
            return jsonify({
                "success": False,
                "error": "Channel not found or not configured for Slack"
            }), 404

        data = request.json
        start_time = data.get('startTime')
        end_time = data.get('endTime')

        # Convert ISO timestamps to Unix timestamps
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        start_timestamp = int(start_dt.timestamp())
        end_timestamp = int(end_dt.timestamp())

        # Fetch conversation from Slack using the slack_channel_id
        conversation = await fetch_slack_conversation(channel["slack_channel_id"], str(start_timestamp), str(end_timestamp))

        # Generate summary
        markdown_summary = await summarize_conversation(str(conversation), together_client)
        
        # Convert markdown to HTML
        html_summary = markdown2.markdown(markdown_summary)
        
        return jsonify({
            "success": True,
            "summary": html_summary,
            "markdown_summary": markdown_summary  # Keep original markdown for reference
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
