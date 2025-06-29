import os
import json
import glob
from together import Together
import re

OUTPUTS_PATH = '../outputs'
RESULTS_PATH = '../part1/results'
MODEL = 'meta-llama/Meta-Llama-3-8B-Instruct-Lite'

PROMPT = '''
You are an expert customer success manager who manages client accounts. Given the following meeting summary, generate exactly three actionable items that the customer success team should take next to address client concerns and improve the client experience. 
For each action, provide a short description and a brief reasoning for why it is important for client satisfaction and account retention.
Output the result as a JSON array, where each item is an object with 'action' and 'reasoning' fields.

Meeting Summary:
"""
{summary}
"""

JSON:
'''

def get_summary_files():
    """Get all summary files from the outputs directory and part1/results directory."""
    # Get meeting summaries from outputs
    outputs_pattern = os.path.join(OUTPUTS_PATH, 'summary_*.md')
    outputs_files = glob.glob(outputs_pattern)
    
    # Get Slack conversation summaries from part1/results
    results_pattern = os.path.join(RESULTS_PATH, 'summary_*.txt')
    results_files = glob.glob(results_pattern)
    
    # Combine both lists
    all_files = outputs_files + results_files
    return all_files

def process_summary(summary_path):
    """Process a single summary file and generate actions."""
    print(f"Processing: {os.path.basename(summary_path)}")
    
    # Read the summary
    with open(summary_path, 'r') as f:
        summary = f.read()

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

    return actions

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
    
    # Save all results to a single file
    if all_results:
        output_file = 'all_actions.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nAll actions saved to {output_file}")

if __name__ == '__main__':
    main() 