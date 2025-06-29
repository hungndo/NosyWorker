from flask import Flask, render_template, jsonify, request
from datetime import datetime
import markdown2
import json
import os
from services.channel_service import (
    load_channels,
    save_channels,
    fetch_slack_conversation,
    summarize_conversation,
    fetch_outlook_emails,
    check_outlook_auth_status,
    authenticate_outlook
)
import asyncio

app = Flask(__name__)

# Load channels from JSON file
channels = load_channels()

@app.route('/')
def dashboard():
    return render_template('dashboard.html', 
                         channels=channels,
                         enabled_channels=channels)

@app.route('/api/action-items', methods=['GET'])
def get_action_items():
    try:
        # Look for the action items JSON file in part2 directory
        action_items_path = os.path.join('part2', 'all_actions.json')
        if os.path.exists(action_items_path):
            with open(action_items_path, 'r') as f:
                action_items = json.load(f)
            return jsonify({"success": True, "action_items": action_items})
        else:
            return jsonify({"success": False, "error": "No action items found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/action-items-by-client', methods=['GET'])
def get_action_items_by_client():
    try:
        # Look for the client-organized action items JSON file in part2 directory
        action_items_path = os.path.join('part2', 'actions_by_client.json')
        if os.path.exists(action_items_path):
            with open(action_items_path, 'r') as f:
                action_items = json.load(f)
            return jsonify({"success": True, "action_items": action_items})
        else:
            return jsonify({"success": False, "error": "No client-organized action items found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/channels/<channel_id>/profile', methods=['GET'])
def get_channel_profile(channel_id):
    for channel in channels:
        if channel["id"] == channel_id:
            return jsonify({
                "success": True, 
                "profile": channel.get("profile"),
                "name": channel.get("name")
            })
    return jsonify({"success": False, "error": "Channel not found"}), 404

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
        # Find channel in config
        channel = None
        for ch in channels:
            if ch["id"] == channel_id:
                channel = ch
                break
        
        if not channel:
            return jsonify({
                "success": False,
                "error": "Channel not found"
            }), 404

        data = request.json
        start_time = data.get('startTime')
        end_time = data.get('endTime')

        if channel["type"] == "slack":
            if "slack_channel_id" not in channel:
                return jsonify({
                    "success": False,
                    "error": "Channel not configured for Slack"
                }), 404
            # Convert ISO timestamps to Unix timestamps
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            start_timestamp = int(start_dt.timestamp())
            end_timestamp = int(end_dt.timestamp())
            # Fetch conversation from Slack
            conversation = await fetch_slack_conversation(channel["slack_channel_id"], str(start_timestamp), str(end_timestamp))
            # Generate summary
            markdown_summary = await summarize_conversation(str(conversation))
        elif channel["type"] == "outlook":
            if "outlook_folder" not in channel or not channel["outlook_folder"]:
                return jsonify({
                    "success": False,
                    "error": "Channel not configured for Outlook"
                }), 404
            # Fetch recent emails (e.g., 20 most recent)
            emails = await fetch_outlook_emails(channel["outlook_folder"], 1)
            # Format emails as a conversation string for summarization
            conversation = ""
            for email in emails:
                conversation += f"From: {email['sender']} <{email['address']}>, Subject: {email['subject']}, Date: {email['receivedDateTime']}\n{email['body']}\n---\n"
            # Generate summary
            markdown_summary = await summarize_conversation(conversation)
        else:
            return jsonify({
                "success": False,
                "error": "Unsupported channel type"
            }), 400
        # Convert markdown to HTML
        html_summary = markdown2.markdown(markdown_summary)
        return jsonify({
            "success": True,
            "summary": html_summary,
            "markdown_summary": markdown_summary
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/outlook/auth-status', methods=['GET'])
def outlook_auth_status():
    try:
        authenticated = asyncio.run(check_outlook_auth_status())
        return jsonify({"success": True, "authenticated": authenticated})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/outlook/authenticate', methods=['POST'])
def outlook_authenticate():
    try:
        auth_link = asyncio.run(authenticate_outlook())
        return jsonify({"success": True, "auth_link": auth_link})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/send-action-email', methods=['POST'])
async def send_action_email():
    try:
        data = request.json
        to_email = data.get('to')
        subject = data.get('subject')
        message = data.get('message')
        action = data.get('action')
        
        if not all([to_email, subject, message]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        # Use the existing MCP client to send email via Outlook
        try:
            # Import the MCP client functions
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
            
            # Create MCP server parameters for Outlook with environment variables
            outlook_mcp_script = '../outlook-mcp/index.js'
            server_params = StdioServerParameters(
                command="node",
                args=[outlook_mcp_script],
                env={
                    'OUTLOOK_CLIENT_ID': 'dcb19bb8-79ea-4b1d-ac28-7c05ed3b4c0e',
                    'OUTLOOK_CLIENT_SECRET': 'tvt8Q~~mj82y5VVOrsAV2F-Hs5i00PD1cUJcncld%'
                },
            )
            
            # Connect to Outlook MCP server and send email
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # First check authentication status
                    auth_result = await session.call_tool('check-auth-status', arguments={})
                    if auth_result.content and len(auth_result.content) > 0:
                        auth_status = auth_result.content[0].text
                        if "Not authenticated" in auth_status:
                            # Try to authenticate
                            auth_response = await session.call_tool('authenticate', arguments={})
                            if auth_response.content and len(auth_response.content) > 0:
                                auth_text = auth_response.content[0].text
                                if "Authentication required" in auth_text:
                                    return jsonify({
                                        "success": False,
                                        "error": "Outlook authentication required. Please authenticate first.",
                                        "auth_url": "http://localhost:3333/auth?client_id=dcb19bb8-79ea-4b1d-ac28-7c05ed3b4c0e"
                                    }), 401
                    
                    # Call the send-email tool
                    result = await session.call_tool('send-email', arguments={
                        'to': to_email,
                        'subject': subject,
                        'body': message,
                        'importance': 'normal',
                        'saveToSentItems': True
                    })
                    
                    # Check if email was sent successfully
                    if result.content and len(result.content) > 0:
                        response_text = result.content[0].text
                        if "Email sent successfully" in response_text:
                            return jsonify({
                                "success": True,
                                "message": "Email sent successfully via Outlook",
                                "details": {
                                    "to": to_email,
                                    "subject": subject,
                                    "action": action,
                                    "outlook_response": response_text
                                }
                            })
                        else:
                            return jsonify({
                                "success": False,
                                "error": f"Outlook MCP error: {response_text}"
                            }), 500
                    else:
                        return jsonify({
                            "success": False,
                            "error": "No response from Outlook MCP server"
                        }), 500
                        
        except Exception as mcp_error:
            print(f"MCP Error: {mcp_error}")
            return jsonify({
                "success": False,
                "error": f"Failed to send email via Outlook MCP: {str(mcp_error)}"
            }), 500
        
    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
