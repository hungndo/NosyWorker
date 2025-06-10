# suppress warnings
import warnings
import os
import json
from datetime import datetime
from typing import List, Dict

warnings.filterwarnings("ignore")

from together import Together
import gradio as gr
from pydantic import BaseModel, Field

class Message(BaseModel):
    user: str = Field(..., description="Name of the participant")
    text: str = Field(..., description="Content of the message")

class Conversation(BaseModel):
    messages: List[Message] = Field(..., description="List of messages in the conversation")

def summarize_conversation(conversation, together_api_key, model="meta-llama/Meta-Llama-3-8B-Instruct-Lite"):
    """Summarize the conversation using TogetherAI."""
    system_prompt = """
    Summary instructions:
    - You are a helpful assistant that summarizes conversations in chat messages.
    - You will be given a conversation and you will need to summarize it concisely.
    - Focus and list out key points, decisions made, and tasks assigned.
    """
    together_client = Together(api_key=together_api_key)

    response = together_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation}
        ],
    )

    return response.choices[0].message.content

def generate_slack_conversation(participants_str, topic, num_messages, api_key):
    """Generate a Slack conversation using TogetherAI."""
    # Convert comma-separated string to list
    participants = [p.strip() for p in participants_str.split(',')]
    
    # Create a prompt that describes the conversation scenario
    prompt = f"""Generate a natural conversation between {len(participants)} people ({', '.join(participants)}) 
    discussing the topic: {topic}. The conversation should be realistic and engaging, with each person contributing 
    their thoughts and responding to others. The conversation should have exactly {num_messages} messages in total.
    
    The response should be a JSON object with a 'messages' array containing {num_messages} message objects.
    Each message object should have:
    - 'user': the name of the participant
    - 'text': the content of their message"""

    try:
        client = Together(api_key=api_key)
        response = client.chat.completions.create(
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
        try:
            conversation_data = json.loads(content)
            if not isinstance(conversation_data, dict) or 'messages' not in conversation_data:
                return "Error: Response missing 'messages' key"
            
            conversation = conversation_data['messages']
            
            # Format the conversation for display
            formatted_conversation = ""
            for message in conversation:
                formatted_conversation += f"{message['user']}: {message['text']}\n\n"
            
            return formatted_conversation
            
        except json.JSONDecodeError as e:
            return f"Error parsing JSON response: {str(e)}\nRaw response: {content}"
            
    except Exception as e:
        return f"Error calling Together AI API: {str(e)}"

with gr.Blocks(title="NosyWorker") as demo:
    gr.Markdown("# NosyWorker")
    
    gr.Markdown("Generate and summarize conversations from Slack, Outlook, ...")
    gr.Markdown("""TODO: The full prototype should be able to retrieve generated conversations that are already populated in Slack 
                instead of working directly with the generated output as in the demo""")
    
    with gr.Row():
        with gr.Column():
            participants_input = gr.Textbox(
                label="Participants (comma-separated)",
                placeholder="Enter participant names separated by commas...",
                lines=1
            )
            topic_input = gr.Textbox(
                label="Conversation Topic",
                placeholder="Enter the topic for the conversation...",
                lines=1
            )
            num_messages_input = gr.Number(
                label="Number of Messages",
                value=10,
                minimum=1,
                maximum=50
            )
            api_key_input = gr.Textbox(
                label="TogetherAI API Key",
                placeholder="Enter your TogetherAI API key",
                type="password"
            )
            
            generate_btn = gr.Button("Generate Conversation")
        
        with gr.Column():
            generated_conversation = gr.Textbox(
                label="Generated Conversation",
                lines=15
            )
            summary_output = gr.Textbox(
                label="Generated Summary",
                lines=10
            )
    
    generate_btn.click(
        fn=generate_slack_conversation,
        inputs=[
            participants_input,
            topic_input,
            num_messages_input,
            api_key_input
        ],
        outputs=[generated_conversation]
    ).then(
        fn=summarize_conversation,
        inputs=[generated_conversation, api_key_input],
        outputs=[summary_output]
    )

if __name__ == "__main__":
    demo.launch()