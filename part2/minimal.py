# suppress warnings
import warnings

warnings.filterwarnings("ignore")

# import libraries
import argparse
from together import Together
import textwrap
import os
from datetime import datetime


## prompt is
### python3 minimal.py --api_key <your_api_key>


## FUNCTION 1: This Allows Us to Prompt the AI MODEL
# -------------------------------------------------
def prompt_llm(prompt, with_linebreak=False):
    # This function allows us to prompt an LLM via the Together API

    # model
    model = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"

    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    output = response.choices[0].message.content

    if with_linebreak:
        # Wrap the output
        wrapped_output = textwrap.fill(output, width=50)

        return wrapped_output
    else:
        return output


if __name__ == "__main__":
    # args on which to run the script
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--api_key", type=str, default=None)
    args = parser.parse_args()

    # Get Client for your LLMs
    client = Together(api_key=args.api_key)

    # Example usage
    prompt = "write three responses to an unhappy customer that is using your software. make sure the responses are different escalation levels 1 acknowledge and acknowledge the issue, 2 apologize and offer a solution, 3 escalate the issue to a manager"
    response = prompt_llm(prompt)

    # Create results directory if it doesn't exist
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(results_dir, f"response_{timestamp}.txt")

    # Save prompt and response to file
    try:
        with open(filename, "w") as f:
            f.write("Prompt:\n")
            f.write("-" * 50 + "\n")
            f.write(prompt + "\n\n")
            f.write("Response:\n")
            f.write("-" * 50 + "\n")
            f.write(response)
        print(f"\nResponse saved to: {filename}")
    except Exception as e:
        print(f"Error saving response: {e}")

    print("\nResponse:\n")
    print(response)
    print("-" * 100)