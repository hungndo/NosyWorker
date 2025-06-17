from flask import Flask, render_template, jsonify, request
from datetime import datetime
import markdown2
from services.channel_service import (
    load_channels,
    save_channels,
    fetch_slack_conversation,
    summarize_conversation
)

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
        markdown_summary = await summarize_conversation(str(conversation))
        
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
