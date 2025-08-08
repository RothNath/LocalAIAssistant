# AI Assistant CLI

## Overview

This is an interactive command-line interface (CLI) tool designed to act as a **junior developer and project manager AI assistant**. It leverages the Google Gemini API to understand natural language requests and perform various project management and file system operations on your local machine. The tool is designed to be conversational and flexible, asking for your approval before executing any actions that modify your files or project state.

## Features

* **Intelligent Request Interpretation**: Understands natural language commands and translates them into structured actions.

* **Approval Workflow**: Proposes file system changes and seeks user approval before execution, ensuring control and preventing unintended modifications.

* **Project State Persistence**: Remembers the current project directory and conversation history across sessions by saving state to `project_config.json`.

* **File Management**:

    * **Project Initialization**: Creates new project directories (`init_project` command).

    * **File & Directory Creation**: Creates new files (empty or with content) and subdirectories within a project (`create_files` command).

    * **File Listing**: Displays the current project's directory structure (`list_files` command).

* **Milestone Tracking**: Manages project milestones, their status, and notes, persisting this data in `milestones.json`.

* **Presentation Planning**: Generates structured Markdown outlines for presentations (`create_presentation_plan` command).

* **API Key Externalization**: Securely loads the API key from `api_key.txt`, making updates easier and preventing the key from being hardcoded in the main script.

## Setup

To get this AI Assistant CLI running on your machine, follow these steps:

### Prerequisites

* **Python 3.6 or higher**: This script utilizes modern Python features.

    * *For Debian/Ubuntu users, if `python3 -m venv` fails, install `python3.x-venv` (e.g., `sudo apt install python3.12-venv`).*

* **Google Gemini API Key**: Obtain a free API key from [Google AI Studio](https://aistudio.google.com/).

### Installation

1.  **Clone the Repository** (or download the `ai_project_cli.py` file):

    ```bash
    git clone <repository_url_here>
    cd <repository_directory_name>
    ```

2.  **Create a Virtual Environment**:

    ```bash
    python3 -m venv venv
    ```

3.  **Activate the Virtual Environment**:

    ```bash
    source venv/bin/activate
    ```

4.  **Install Dependencies**:

    ```bash
    pip install requests
    ```

5.  **Create API Key File**: In the same directory as `ai_project_cli.py`, create a file named `api_key.txt` and paste your Google Gemini API key into it (no extra spaces or lines).

    ```
    # Example content of api_key.txt
    YOUR_ACTUAL_GEMINI_API_KEY_GOES_HERE
    ```

## Usage

Once set up, run the script from your terminal:
python ai_project_cli.py

### Initial Interaction

* **Starting a new project**:

    ```
    You: Let's make a new project called MyAwesomeApp
    AI: Certainly!
    With your approval, I will create the project directory named 'MyAwesomeApp'.
    Do you approve this action? (y/n): y
    Project directory created at: /path/to/MyAwesomeApp
    ```

* **Resuming a project**: If `project_config.json` exists, it will load the previous state automatically.

---

### Commands & Examples

* **Create a file**:

    ```
    You: Make a Python file called 'main.py' with a 'hello world' print statement.
    AI: Absolutely!
    With your approval, I will create the following files: main.py.
    Do you approve this action? (y/n): y
    ```

* **Create a directory**:

    ```
    You: Can you make a new folder called 'src'?
    AI: Of course!
    With your approval, I will create the following directories: src.
    Do you approve this action? (y/n): y
    ```

* **List files**:

    ```
    You: What files are in this project?
    AI: I can list the directory structure for your project.
    With your approval, I will list the directory structure.
    Do you approve this action? (y/n): y
    ```

* **Track milestones**:

    ```
    You: Add a new milestone: 'Implement user login', status 'Not Started'.
    AI: Understood!
    With your approval, I will update the project milestones.
    Do you approve this action? (y/n): y
    ```

* **Generate a presentation plan**:

    ```
    You: Draft a presentation outline for management about our project progress.
    AI: Certainly!
    With your approval, I will create a Markdown file for the 'Project Progress' presentation.
    Do you approve this action? (y/n): y
    ```
