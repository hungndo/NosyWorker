import os
import json
import glob
from together import Together
import re
from datetime import datetime

OUTPUTS_PATH = './outputs'
RESULTS_PATH = '../part1/results'
MODEL = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'#'meta-llama/Meta-Llama-3-8B-Instruct-Lite'

# Client mapping - you can update this based on your actual client names
CLIENT_MAPPING = {
    'workflow_approval': 'TechCorp Solutions',
    'new_feature': 'TechCorp Solutions', 
    'approval_system': 'TechCorp Solutions',
    'user_friendly': 'TechCorp Solutions',
    'frustration': 'TechCorp Solutions',
    'employees': 'TechCorp Solutions',
    'guide': 'TechCorp Solutions',
    'tutorial': 'TechCorp Solutions',
    'support': 'TechCorp Solutions',
    'training': 'TechCorp Solutions',
    'user_testing': 'TechCorp Solutions',
    'design': 'TechCorp Solutions',
    'implementation': 'TechCorp Solutions',
    'onboarding': 'TechCorp Solutions',
    'account_manager': 'TechCorp Solutions',
    'client': 'TechCorp Solutions',
    'meeting': 'TechCorp Solutions',
    'summary': 'TechCorp Solutions'
}

PROMPT = '''
You are an expert customer success manager who manages client accounts. Given the following meeting summary, generate exactly three actionable items that the customer success team should take next to address client concerns and improve the client experience. 
For each action, provide a short description and a brief reasoning for why it is important for client satisfaction and account retention.
Output the result as a JSON array, where each item is an object with 'action', 'reasoning', 'priority' (high/medium/low), and 'category' (support/training/documentation/design/communication) fields.

Meeting Summary:
"""
{summary}
"""

JSON:
'''

def identify_client(summary_text):
    """Identify the client based on keywords in the summary."""
    summary_lower = summary_text.lower()
    
    # Check for specific client mentions first
    for keyword, client_name in CLIENT_MAPPING.items():
        if keyword in summary_lower:
            return client_name
    
    # Default client if no specific identification - assume all current data is from one client
    return "TechCorp Solutions"

def get_summary_files():
    """Get all summary files from the outputs directory and part1/results directory."""
    # Get meeting summaries from outputs
    outputs_pattern = os.path.join(OUTPUTS_PATH, 'summary_*.md')
    outputs_files = glob.glob(outputs_pattern)
    
    # Get Slack conversation summaries from part1/results
    # results_pattern = os.path.join(RESULTS_PATH, 'summary_*.txt')
    # results_files = glob.glob(results_pattern)
    
    # Combine both lists
    all_files = outputs_files #+ results_files
    return all_files

def process_summary(summary_path):
    """Process a single summary file and generate actions."""
    print(f"Processing: {os.path.basename(summary_path)}")
    
    # Read the summary
    with open(summary_path, 'r') as f:
        summary = f.read()

    # Identify client
    client_name = identify_client(summary)
    print(f"  Identified client: {client_name}")

    # Prepare Together client
    api_key = os.environ.get('TOGETHER_API_KEY')
    if not api_key:
        raise ValueError('TOGETHER_API_KEY not set in environment')
    client = Together(api_key=api_key)

    # Prepare prompt
    prompt = PROMPT.format(summary=summary)

    # Call Together AI
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    content = response.choices[0].message.content.strip()

    # Try to parse JSON from the response
    try:
        # Try to extract JSON from the response (in case there's extra text)
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            actions = json.loads(json_str)
        else:
            actions = json.loads(content)
    except json.JSONDecodeError:
        print('Could not parse JSON. Raw output:')
        print(content)
        return None

    # Add metadata to each action
    for action in actions:
        action['client'] = client_name
        action['source_file'] = os.path.basename(summary_path)
        action['generated_at'] = datetime.now().isoformat()
        if 'priority' not in action:
            action['priority'] = 'medium'
        if 'category' not in action:
            action['category'] = 'support'

    return actions

def organize_by_client(all_actions):
    """Organize actions by client with burger menu structure."""
    client_organization = {}
    
    for filename, actions in all_actions.items():
        for action in actions:
            client_name = action.get('client', 'Unknown Client')
            
            if client_name not in client_organization:
                client_organization[client_name] = {
                    'client_info': {
                        'name': client_name,
                        'total_actions': 0,
                        'high_priority': 0,
                        'medium_priority': 0,
                        'low_priority': 0
                    },
                    'categories': {
                        'support': [],
                        'training': [],
                        'documentation': [],
                        'design': [],
                        'communication': []
                    },
                    'all_actions': []
                }
            
            # Add to client organization
            client_organization[client_name]['all_actions'].append(action)
            client_organization[client_name]['client_info']['total_actions'] += 1
            
            # Count priorities
            priority = action.get('priority', 'medium')
            if priority == 'high':
                client_organization[client_name]['client_info']['high_priority'] += 1
            elif priority == 'medium':
                client_organization[client_name]['client_info']['medium_priority'] += 1
            elif priority == 'low':
                client_organization[client_name]['client_info']['low_priority'] += 1
            
            # Organize by category
            category = action.get('category', 'support')
            if category in client_organization[client_name]['categories']:
                client_organization[client_name]['categories'][category].append(action)
    
    return client_organization

def main():
    # Get all summary files
    summary_files = get_summary_files()
    
    if not summary_files:
        print("No summary files found in outputs or part1/results directories.")
        return
    
    print("Available summary files:")
    for i, file_path in enumerate(summary_files):
        print(f"{i+1}. {os.path.basename(file_path)}")
    
    # Process all summaries
    all_results = {}
    
    for summary_path in summary_files:
        filename = os.path.basename(summary_path)
        actions = process_summary(summary_path)
        
        if actions:
            all_results[filename] = actions
            print(f"\nActions for {filename}:")
            print(json.dumps(actions, indent=2))
            print("-" * 50)
    
    # Organize by client
    client_organization = organize_by_client(all_results)
    
    # Save both formats
    if all_results:
        # Save original format
        output_file = './part2/all_actions.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nAll actions saved to {output_file}")
        
        # Save client-organized format
        client_output_file = './part2/actions_by_client.json'
        with open(client_output_file, 'w') as f:
            json.dump(client_organization, f, indent=2)
        print(f"Client-organized actions saved to {client_output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("CLIENT ACTION SUMMARY")
        print("="*60)
        for client_name, client_data in client_organization.items():
            info = client_data['client_info']
            print(f"\n📋 {client_name}")
            print(f"   Total Actions: {info['total_actions']}")
            print(f"   High Priority: {info['high_priority']}")
            print(f"   Medium Priority: {info['medium_priority']}")
            print(f"   Low Priority: {info['low_priority']}")
            
            for category, actions in client_data['categories'].items():
                if actions:
                    print(f"   📁 {category.title()}: {len(actions)} actions")

if __name__ == '__main__':
    main() 