# NosyWorker

A powerful communication analysis and automation tool that helps summarize conversations and automate follow-up actions across multiple platforms including Slack, Microsoft Teams, Outlook, and other chat/email applications. NosyWorker uses AI to provide insights, generate summaries, and automate routine tasks like responding to emails, updating tickets, and managing follow-ups, making your team's communication more efficient and productive.

## Features

- Multi-platform support for popular communication tools:
  - Chat platforms (Slack, Microsoft Teams, Discord)
  - Email clients (Outlook, Gmail)
  - More platforms coming soon
- Unified dashboard for viewing and managing all communication channels
- AI-powered conversation summarization and analysis
- Automated follow-up actions:
  - Smart email responses and follow-ups
  - Ticket updates and status changes
  - Meeting scheduling and calendar management
  - Task creation and assignment
  - Custom automation workflows
- Customizable channel profiles and data source configurations
- Advanced search capabilities across all connected platforms
- Thread and conversation analysis with context preservation
- Export and reporting features for communication insights
- Integration with popular productivity tools and services

## Prerequisites

- Python 3.10 or higher
- Conda (Anaconda or Miniconda)
- Slack API tokens (Bot Token and User Token)
- Together API key (for AI-powered conversation summarization)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd NosyWorker
```

2. Create and activate a Conda environment:
```bash
# Create a new conda environment
conda create -n nosyworker python=3.10

# Activate the environment
conda activate nosyworker
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Environment Setup

Set up your API tokens as environment variables:

```bash
# For Linux/Mac
export SLACK_BOT_TOKEN=xoxb-your-bot-token
export SLACK_USER_TOKEN=xoxp-your-user-token
export TOGETHER_API_KEY=your-together-api-key

# For Windows (Command Prompt)
set SLACK_BOT_TOKEN=xoxb-your-bot-token
set SLACK_USER_TOKEN=xoxp-your-user-token
set TOGETHER_API_KEY=your-together-api-key

# For Windows (PowerShell)
$env:SLACK_BOT_TOKEN="xoxb-your-bot-token"
$env:SLACK_USER_TOKEN="xoxp-your-user-token"
$env:TOGETHER_API_KEY="your-together-api-key"
```

To make these environment variables persistent, you can add them to your shell's configuration file:
- For Linux/Mac: Add to `~/.bashrc` or `~/.zshrc`
- For Windows: Set them through System Properties > Environment Variables

## Running the Applications

### 1. MCP Server

The MCP server provides Slack API integration and runs on port 8000.

```bash
python ./part1/mcp_server.py
```

The server will start on `http://localhost:8000/mcp`

### 2. Flask Application

The Flask application provides the web interface and runs on port 5000.

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Troubleshooting

1. Make sure both the MCP server and Flask app are running simultaneously.
2. Verify that your Slack tokens have the necessary permissions.
3. Check the console output for any error messages.

## License

[Add your license information here]