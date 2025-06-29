# Part 2: Generate Action Items from Meeting Summaries

**This step should be executed after Part 1 (meeting summarization) is complete.**

## Instructions

1. **Ensure Part 1 is complete:**
   - Meeting summaries should be generated and saved as markdown files in the `../outputs/` directory (e.g., `summary_YYYYMMDD_HHMMSS.md`).

2. **Activate your conda environment:**
   ```bash
   conda activate nosyworker
   ```

3. **Navigate to the part2 directory:**
   ```bash
   cd NosyWorker/part2
   ```

4. **Generate action items from all summaries:**
   ```bash
   python generate_actions.py
   ```
   - This script will process all `summary_*.md` files in the `../outputs/` directory.
   - For each summary, it will use Together AI to generate three actionable items for the customer success team.
   - The results will be saved to `all_actions.json` in this directory.

5. **View action items in the dashboard:**
   - Start your Flask app if it is not already running:
     ```bash
     cd ../..
     python app.py
     ```
   - Open your browser to [http://localhost:5000](http://localhost:5000)
   - The dashboard will display the action items under the "Customer Success Action Items" section.

6. **Take action:**
   - Each action item has a "Take Action" button that allows you to send a follow-up email via Outlook.
   - If authentication is required, you will be prompted to authenticate with Microsoft.

---

**Note:**
- Make sure your Together AI API key is set in your environment or `.env` file.
- Make sure your Outlook MCP server and authentication server are running and properly configured.