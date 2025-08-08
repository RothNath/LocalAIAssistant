# ai_project_cli.py
# This script creates an AI-powered, interactive command-line tool
# that acts as a junior developer and project manager. It can create
# files, read existing files, track milestones, generate presentation plans,
# and send their contents to an LLM for tasks like code review and bug hunting.

import os
import json
import requests
import time
from pathlib import Path

# --- Configuration ---
# You must provide a valid API key for the script to work.
# Get one for free at https://aistudio.google.com/
# It is recommended to use environment variables in a real application.
# The API key will now be loaded from a separate file.
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
MILESTONE_FILE = "milestones.json"
STATE_FILE = "project_config.json"
API_KEY_FILE = "api_key.txt"

# --- Globals and State Management ---
# The conversation history is crucial for the LLM to maintain context.
chat_history = []
# The root directory for the current project.
root_dir = None
# The API key will be stored here after being loaded from the file.
API_KEY = None

def get_base_prompt():
    """
    Returns the initial system prompt to set the context for the LLM.
    This prompt instructs the LLM to act as a junior developer and
    project manager assistant.
    """
    return f"""
You are a junior developer and project manager AI assistant. Your purpose is to assist a user in
creating, managing, and improving their projects on their local machine. You are conversational and helpful,
but your primary function is to provide structured JSON responses that the user's CLI tool can
understand and act upon.

Your responses MUST be a single JSON object with three keys:
- "message": A conversational, friendly string that briefly acknowledges the user's request. It should not contain a detailed description of the action, as the client application will handle that.
- "requires_approval": A boolean value. Set to 'true' if the action will modify the file system (e.g., creating a file). Set to 'false' for read-only actions (e.g., listing files or simple conversation).
- "action": An object describing the file system operations to perform or a plan to follow.

The "action" object MUST have the following structure:
- "command": A string. Valid commands are "init_project", "create_files", "list_files", "no_action", "milestones", or "create_presentation_plan".
    - "init_project": Sets up the new project directory and any initial files. This command should only be used as the very first action for a new project.
    - "create_files": Creates new files/directories and updates existing ones within the current project.
    - "list_files": Lists the contents of the project directory.
    - "no_action": The conversation continues without any file system changes.
    - "milestones": Acknowledges a request to manage milestones.
    - "create_presentation_plan": Creates a Markdown file with a presentation plan.
- "payload": An object containing the details for the command.
    - If "command" is "init_project", the payload is an object with a "project_name" key (e.g., "new_app").
    - If "command" is "create_files", the payload is an object where keys are file paths (e.g., "src/main.py")
      and values are the content to be written. To explicitly create a directory, the value for the path should be the string "__CREATE_DIR__". For an empty file, the value should be an empty string "".
    - If "command" is "list_files", the payload is an object with a "directory" key (e.g., ".").
    - If "command" is "no_action", the payload is an empty object `{{}}`.
    - If "command" is "milestones", the payload is an object with a "milestones" key, which is a list of milestone objects.
      Each milestone object should have "name", "status" (e.g., "Not Started", "In Progress", "Complete"), and "notes".
      The CLI will update a file named "{MILESTONE_FILE}" with this payload.
    - If "command" is "create_presentation_plan", the payload is an object with a "title", "audience", and "slides" key. The "slides"
      key is an array of slide objects, each having a "heading" and "content" key.

The user will provide you with file contents in the prompt when they ask you to review or test code.
You can assume the existence of files named "{MILESTONE_FILE}" and a state file named "{STATE_FILE}" for tracking state.
You can generate a README.md or CHANGELOG.md file by responding with a "create_files" command and a markdown payload when the user asks for project documentation.
Start the conversation by greeting the user and asking them what they'd like to work on today.
"""

def save_project_state():
    """
    Saves the current project root and chat history to a JSON file.
    This allows the CLI to resume the conversation and project state
    across multiple sessions.
    """
    global root_dir, chat_history
    if root_dir:
        state = {
            "root_dir": str(root_dir),
            "chat_history": chat_history
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

def load_project_state():
    """
    Loads the project root and chat history from the state file.
    """
    global root_dir, chat_history
    if Path(STATE_FILE).exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            root_dir_str = state.get("root_dir")
            if root_dir_str:
                root_dir = Path(root_dir_str)
            chat_history = state.get("chat_history", [])
        print(f"Loaded project state from '{STATE_FILE}'. Current project directory is: {root_dir}")
        print("Resuming previous conversation...")
        return True
    return False

def load_api_key():
    """
    Reads the API key from a local file.
    """
    try:
        with open(API_KEY_FILE, 'r') as f:
            key = f.read().strip()
            if not key or len(key) < 30:
                print(f"Error: The API key in '{API_KEY_FILE}' is invalid or incomplete.")
                return None
            return key
    except FileNotFoundError:
        print(f"Error: The API key file '{API_KEY_FILE}' was not found.")
        print(f"Please create a file named '{API_KEY_FILE}' in this directory and paste your API key inside.")
        return None

def chat_with_ai(user_input):
    """
    Sends the full conversation history, including file content if requested,
    to the Gemini API and returns the structured JSON response.
    """
    global chat_history, root_dir
    
    prompt_parts = [{"text": user_input}]

    # Append the user's new message to the history
    chat_history.append({"role": "user", "parts": prompt_parts})

    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    # Exponential backoff for API calls
    retries = 0
    while retries < 5:
        try:
            response = requests.post(
                f"{API_URL}?key={API_KEY}",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            response_json = response.json()
            raw_content = response_json['candidates'][0]['content']['parts'][0]['text']
            parsed_json = json.loads(raw_content)

            # Append the AI's response to the history for context
            chat_history.append({"role": "model", "parts": [{"text": raw_content}]})
            return parsed_json

        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"API communication error (attempt {retries}/5): {e}")
            if response is not None and response.content:
                print(f"Server response content: {response.content.decode()}")
            time.sleep(2 ** retries)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing API response: {e}")
            # If the response is not valid JSON, tell the AI to re-format it.
            retry_prompt = f"The previous response was not a valid JSON object. Please re-format your response into a single JSON object with 'message' and 'action' keys. The error was: {e}"
            chat_history.append({"role": "user", "parts": [{"text": retry_prompt}]})
            # Try again with the corrective prompt
            continue
    
    print("Failed to get a valid response after multiple retries.")
    return None

def execute_action(action):
    """
    Parses the 'action' from the LLM's response and performs the
    corresponding file system operations.
    """
    global root_dir
    command = action.get('command')
    payload = action.get('payload', {})

    if command == "init_project":
        project_name = payload.get("project_name")
        if not project_name:
            project_name = input("What's the name of the new project? ")
        
        root_dir = Path.cwd() / project_name
        root_dir.mkdir(parents=True, exist_ok=True)
        print(f"Project directory created at: {root_dir}")
        save_project_state()
        
    elif command == "create_files":
        if not root_dir:
            print("Error: You must first initialize a project. Please ask me to 'init_project' with a name.")
            return

        for path, content in payload.items():
            item_path = root_dir / path
            
            # Create directories if the content is the special marker
            if content == "__CREATE_DIR__":
                item_path.mkdir(parents=True, exist_ok=True)
                print(f"  - Created directory: {item_path}")
            # Create and write to files otherwise
            else:
                item_path.parent.mkdir(parents=True, exist_ok=True)
                with open(item_path, 'w') as f:
                    f.write(content)
                print(f"  - Created file: {item_path}")
    
    elif command == "list_files":
        if not root_dir:
            print("Please create a project first.")
            return

        print(f"Directory structure for '{root_dir.name}':")
        for item in sorted(os.walk(root_dir)):
            root, dirs, files = item
            level = root.replace(str(root_dir), '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 4 * (level + 1)
            for f in sorted(files):
                print(f'{subindent}{f}')
    
    elif command == "milestones":
        if not root_dir:
            print("Please create a project first.")
            return

        milestone_path = root_dir / MILESTONE_FILE
        try:
            with open(milestone_path, 'w') as f:
                json.dump(payload, f, indent=2)
            print(f"  - Updated milestones in '{milestone_path}'")
        except Exception as e:
            print(f"Error writing to milestone file: {e}")
    
    elif command == "create_presentation_plan":
        if not root_dir:
            print("Please create a project first.")
            return

        # Generate a filename based on the presentation title
        title_slug = payload.get("title", "presentation-plan").replace(" ", "-").lower()
        presentation_path = root_dir / f"{title_slug}.md"
        
        try:
            with open(presentation_path, 'w') as f:
                f.write(f"# {payload.get('title', 'Presentation Title')}\n")
                f.write(f"**Audience:** {payload.get('audience', 'General')}\n\n---\n\n")
                
                for i, slide in enumerate(payload.get('slides', [])):
                    f.write(f"## Slide {i+1}: {slide.get('heading', 'Slide Heading')}\n\n")
                    f.write(f"{slide.get('content', 'Slide content here.')}\n\n---\n\n")
            
            print(f"  - Created presentation plan at: '{presentation_path}'")
        except Exception as e:
            print(f"Error writing presentation plan: {e}")

    elif command == "no_action":
        # Do nothing, the AI's message is the full response
        pass
    
    else:
        print(f"Unknown command received from AI: {command}")


def main():
    """
    Main interactive loop for the CLI tool. This loop handles
    all conversation, file operations, and milestone tracking.
    """
    global chat_history, root_dir, API_KEY

    # Load the API key from a file first
    API_KEY = load_api_key()
    if not API_KEY:
        return # Exit if the key is not found or is invalid

    # Load state from previous session
    if not load_project_state():
        print("Welcome to the AI Dev Assistant! Type 'exit' to quit.")
        # Initialize the chat with the system prompt if no state was loaded
        base_prompt = get_base_prompt()
        chat_history.append({"role": "user", "parts": [{"text": base_prompt}]})
        
        # Send the first message to the AI
        first_response = chat_with_ai("Greet me.")
        
        if first_response:
            print(f"\nAI: {first_response['message']}")
    
    # Main conversational loop
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        response = chat_with_ai(user_input)
        
        if response:
            print(f"\nAI: {response['message']}")
            action = response.get('action')
            requires_approval = response.get('requires_approval', False)
            
            if action and requires_approval:
                command = action.get('command')
                payload = action.get('payload', {})
                
                action_description = ""
                if command == "init_project":
                    project_name = payload.get("project_name")
                    action_description = f"create the project directory named '{project_name}'."
                elif command == "create_files":
                    files_to_create = [path for path, content in payload.items() if content != "__CREATE_DIR__"]
                    dirs_to_create = [path for path, content in payload.items() if content == "__CREATE_DIR__"]
                    if files_to_create and dirs_to_create:
                        action_description = f"create the following directories: {', '.join(dirs_to_create)} and files: {', '.join(files_to_create)}."
                    elif files_to_create:
                        action_description = f"create the following files: {', '.join(files_to_create)}."
                    elif dirs_to_create:
                        action_description = f"create the following directories: {', '.join(dirs_to_create)}."
                elif command == "milestones":
                    action_description = "update the project milestones."
                elif command == "create_presentation_plan":
                    title = payload.get("title", "presentation plan")
                    action_description = f"create a Markdown file for the '{title}' presentation."

                if action_description:
                    print(f"\nWith your approval, I will {action_description}")
                
                approval = input("Do you approve this action? (y/n): ")
                if approval.lower() == 'y':
                    execute_action(action)
                    save_project_state()
                else:
                    print("Action cancelled. Please provide new instructions.")
                    # Let the AI know the user declined the action
                    chat_history.append({"role": "user", "parts": [{"text": "I did not approve the previous action. Let's try something else."}]})
            elif action:
                execute_action(action)
                save_project_state()
        else:
            print("Sorry, I encountered an error. Please try again.")

if __name__ == "__main__":
    main()
