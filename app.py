from flask import Flask, render_template, jsonify, request
from datetime import datetime
import markdown2
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

if __name__ == '__main__':
    app.run(debug=True)
