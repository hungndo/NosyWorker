from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import os

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

# Load channels from JSON file
channels = load_channels()

@app.route('/')
def dashboard():
    enabled_channels = [channel for channel in channels if channel["enabled"]]
    return render_template('dashboard.html', 
                         channels=channels,
                         enabled_channels=enabled_channels)

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

if __name__ == '__main__':
    app.run(debug=True)
