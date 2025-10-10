# Command-Line AI Agent (Claude API Integration)

## Overview
This project is a **command-line agent** that connects to **Anthropic’s Claude API** and executes local tools.  
It’s designed to interact naturally through conversation while being able to read, create, edit, and list files directly in your local project directory.

The system is modular and can easily be extended with new tools, such as database operations or custom automation functionalities.

## Objectives
- Integrate with **Claude API** to process user instructions via the command line.
- Allow local file system operations:
  - Read and display file contents  
  - Create and edit files  
  - List files in the working directory
- Manage tool requests and responses inside the ongoing chat flow.
- Make it easy to add new tools (database access, APIs, or other local commands).

## Features
✅ Connects to Claude API  
✅ Executes local file operations (read, create, edit, list)  
✅ Keeps tool use and results within the chat context  
✅ Modular and extensible design for adding new functionalities  
