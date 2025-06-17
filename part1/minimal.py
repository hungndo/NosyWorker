# suppress warnings
import warnings
import os
from datetime import datetime

warnings.filterwarnings("ignore")

import argparse
from together import Together
import textwrap
import asyncio
import json
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# Create the transport with your MCP server URL
server_url = "http://0.0.0.0:8000/mcp"
transport = StreamableHttpTransport(server_url)

# Initialize the client with the transport
client = Client(transport=transport)

async def fetch_slack_conversation(channel_id):
    """Fetch messages from a Slack channel or thread."""
    async with client:

        tools = await client.list_tools()
        print(f"\nAvailable tools: ")
        for i, tool in enumerate(tools):
            print(f"{i+1}. {tool.name}: {tool.description}")
            print("-" * 50)
        # Fetch channel messages
        result = await client.call_tool(
            "get_channel_history",
            {
                "channel_id": channel_id
            }
        )
        
        return json.loads(result[0].text)

async def summarize_conversation(conversation, together_client, model="meta-llama/Meta-Llama-3-8B-Instruct-Lite"):
    """Summarize the conversation using TogetherAI."""
    system_prompt = """
    Summary instructions:
    - You are a helpful assistant that summarizes conversations in chat messages.
    - You will be given a conversation and you will need to summarize it concisely.
    - Focus and list out key points, decisions made, and tasks assigned.
    """

    response = together_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation}
        ],
    )

    return response.choices[0].message.content

def read_conversation_from_file(file_path):
    """Read conversation data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find conversation file at {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file {file_path}")

def save_summary(summary, source_info):
    """Save the summary to a file in the results folder with timestamp."""
    # Create results directory if it doesn't exist
    results_dir = "part1/results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Generate timestamp and filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{results_dir}/summary_{timestamp}.txt"
    
    # Prepare content with metadata
    content = f"Summary generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"Source: {source_info}\n"
    content += "-" * 50 + "\n"
    content += summary
    
    # Save to file
    with open(filename, 'w') as f:
        f.write(content)
    
    return filename

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--channel", type=str, help="Slack channel ID")
    parser.add_argument("-f", "--file", type=str, help="Path to JSON file containing conversation (optional)")
    args = parser.parse_args()

    # Initialize TogetherAI client
    together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

    # Get conversation data either from Slack or file
    if args.file:
        print(f"Reading conversation from file {args.file}...")
        conversation_data = read_conversation_from_file(args.file)
        source_info = f"File: {args.file}"
    else:
        if not args.channel:
            raise ValueError("Either --file or --channel must be provided")
        print(f"Fetching conversation from Slack channel {args.channel}...")
        conversation_data = await fetch_slack_conversation(args.channel)
        source_info = f"Slack Channel: {args.channel}"
    
    print(conversation_data)

    # Format conversation for summarization
    # formatted_conversation = "\n".join([
    #     f"- {msg.get('user', 'Unknown')}: {msg.get('text', '')}"
    #     for msg in conversation_data.get('messages', [])
    # ])

    # print(formatted_conversation)
    # Summarize the conversation
    print("\nSummarizing conversation...")
    summary = await summarize_conversation(str(conversation_data), together_client)
    
    # Print the summary
    print("-" * 50)
    print(summary)
    print("-" * 50)
    
    # Save the summary
    saved_file = save_summary(summary, source_info)
    print(f"\nSummary saved to: {saved_file}")

if __name__ == "__main__":
    asyncio.run(main())