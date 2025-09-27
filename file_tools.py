import os
from typing import Callable, Dict, Any
from dataclasses import dataclass

@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., str]

def read_file_handler(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"

def list_file_handler(directory: str) -> str:
    try:
        files = os.listdir(directory)
        return f"\n.join({files}"
    except Exception as e:
        return f"Error listening files in {directory}: {e} "

def edit_file_handler(path: str, content: str) -> str:
    try:
        with open (path, "w", encoding="utf-8") as f:
            f.write(content)
            return f"File {path} updated successfully"
    except Exception as e:
        return f"Error editing {path}: {e}"

read_file_tool = ToolDefinition(
    name= "read_file",
    description= "Read a file and return its contents as text.",
    input_schema= {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The relative path of a file in the working directory."
            }
        },
        "required": ["path"]
    },
    handler=read_file_handler
)

list_file_tool = ToolDefinition(
    name= "list_file",
    description= "Lists files in a directory",
    input_schema= {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Directory path"
            }
        },
        "required": ["directory"]
    },
    handler=list_file_handler
)

edit_file_tool = ToolDefinition(
    name= "edit_file",
    description= "Edits a file by replacing its contents",
    input_schema= {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
            },
            "content": {
                "type": "string",
                "description": "The content for editing the specific file."
            }
        },
        "required": ["path", "content"]
    },
    handler=edit_file_handler
)

tools = [read_file_tool, list_file_tool, edit_file_tool]
tool_map = {}
for t in tools:
    tool_map[t.name] = t

# import os
# from anthropic import Anthropic
# from file_tools import tools, tool_map  # <-- importăm clasa și tool-urile
#
# def main():
#     client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
#
#     response = client.messages.create(
#         model="claude-3-7-sonnet-latest",
#         max_tokens=512,
#         messages=[{"role": "user", "content": "List the files in the current directory"}],
#         tools=[{
#             "name": t.name,
#             "description": t.description,
#             "input_schema": t.input_schema
#         } for t in tools]
#     )
#
#     # procesează tool_use blocks
#     for block in response.content:
#         if block.type == "tool_use":
#             tool = tool_map[block.name]
#             result = tool.handler(**block.input)
#             print(f"Tool {tool.name} executed → {result}")
#
# if __name__ == "__main__":
#     main()
