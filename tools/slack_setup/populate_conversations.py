from slack_bolt import App
import json
import glob
import time
from config import USER_TOKENS, SLACK_CHANNEL_ID

def send_message(channel_id, message, user):
    """
    Send a message to a specific Slack channel using the appropriate bot token
    
    Args:
        channel_id (str): The ID of the channel to send the message to
        message (dict): The message to send
        user (str): The user sending the message
    """
    try:
        # Get the appropriate bot token for the user
        bot_token = USER_TOKENS.get(user)
        if not bot_token:
            print(f"No bot token found for user: {user}")
            return None
            
        # Create a new app instance with the user's token
        app = App(token=bot_token)
        
        result = app.client.chat_postMessage(
            channel=channel_id,
            text=message['text']
        )
        print(f"Message sent successfully from {user}: {result['ts']}")
        return result
    except Exception as e:
        print(f"Error sending message from {user}: {str(e)}")
        return None

def post_conversation(messages, channel_id):
    """Post messages to Slack"""
    for msg in messages:
        send_message(channel_id, msg, msg['user'])
        time.sleep(0.5)  # Add a 0.5 second delay between messages

def main():
    # Get all JSON files from the generated_conversations directory
    conversation_files = glob.glob("generated_conversations/*.json")
    
    for file_path in conversation_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                messages = data.get('messages', [])
                print(f"Posting conversation from {file_path}")
                post_conversation(messages, SLACK_CHANNEL_ID)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

if __name__ == "__main__":
    main()
