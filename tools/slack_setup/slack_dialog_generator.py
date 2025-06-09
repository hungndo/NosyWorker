import os
import json
from typing import List, Dict
import argparse
from datetime import datetime
from together import Together
from pydantic import BaseModel, Field

class Message(BaseModel):
    user: str = Field(..., description="Name of the participant")
    text: str = Field(..., description="Content of the message")

class Conversation(BaseModel):
    messages: List[Message] = Field(..., description="List of messages in the conversation")

class SlackDialogGenerator:
    def __init__(self, api_key: str):
        self.client = Together(api_key=api_key)

    def generate_conversation(self, participants: List[str], topic: str, num_messages: int = 10) -> List[Dict]:
        # Create a prompt that describes the conversation scenario
        prompt = f"""Generate a natural conversation between {len(participants)} people ({', '.join(participants)}) 
        discussing the topic: {topic}. The conversation should be realistic and engaging, with each person contributing 
        their thoughts and responding to others. The conversation should have exactly {num_messages} messages in total.
        
        The response should be a JSON object with a 'messages' array containing {num_messages} message objects.
        Each message object should have:
        - 'user': the name of the participant
        - 'text': the content of their message"""

        try:
            response = self.client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100 * num_messages,
                response_format={
                    "type": "json_object",
                    "json_schema": Conversation.model_json_schema()
                }
            )
            
            content = response.choices[0].message.content
            print(content)
            try:
                conversation_data = json.loads(content)
                if not isinstance(conversation_data, dict) or 'messages' not in conversation_data:
                    raise ValueError("Response missing 'messages' key")
                
                conversation = conversation_data['messages']
                if len(conversation) != num_messages:
                    print(f"Warning: Expected {num_messages} messages but got {len(conversation)}")
                
                return conversation
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw response: {content}")
                return []
                
        except Exception as e:
            print(f"Error calling Together AI API: {e}")
            return []

    def save_conversation(self, conversation: List[Dict], topic: str, participants: List[str]) -> str:
        # Create base directory for conversations
        base_dir = "generated_conversations"
        os.makedirs(base_dir, exist_ok=True)

        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.json"

        # Prepare the conversation data
        conversation_data = {
            "topic": topic,
            "participants": participants,
            "timestamp": datetime.now().isoformat(),
            "messages": conversation
        }

        # Save to file
        filepath = os.path.join(base_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)

        return filepath

def main():
    parser = argparse.ArgumentParser(description="Generate Slack conversations using Together AI")
    parser.add_argument("--api-key", required=True, help="Together AI API key")
    args = parser.parse_args()

    generator = SlackDialogGenerator(args.api_key)
    
    # Get user input
    num_participants = int(input("Enter the number of participants: "))
    participants = []
    for i in range(num_participants):
        name = input(f"Enter name for participant {i+1}: ")
        participants.append(name)
    
    topic = input("Enter the conversation topic: ")
    
    # Get the number of messages
    while True:
        try:
            num_messages = int(input("Enter the maximum number of messages in the conversation (recommended: 5-20): "))
            if num_messages > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Generate conversation
    conversation = generator.generate_conversation(participants, topic, num_messages)
    
    # Print the conversation
    print("\nGenerated Conversation:")
    print("-" * 50)
    for message in conversation:
        print(f"{message['user']}: {message['text']}")
        print("-" * 50)

    # Save the conversation
    if conversation:
        filepath = generator.save_conversation(conversation, topic, participants)
        print(f"\nConversation saved to: {filepath}")

if __name__ == "__main__":
    main()
