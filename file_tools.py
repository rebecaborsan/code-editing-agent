import os
from typing import Callable, Dict, Any
from dataclasses import dataclass


# -----------------------------------------------------------------------------
# This module defines 3 filesystem tools (read_file_tool, list_file_tool, create_or_edit_file_tool)
# that your Agent can call via Anthropic Tool Use.
#
# Design goals:
#  - Always resolve paths relative to the project root (not the current CWD)
#  - Simple, predictable behavior
#  - Clear error messages
# -----------------------------------------------------------------------------

@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., str]

# 1) Anchor everything to the project root so behavior is CWD-independent.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 2) Small, focused helpers ---------------------------------------------------

def ensure_parent_dir(path: str) -> None:
    """Create parent directory/ies for 'path' if they don't exist (mkdir -p)."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

def resolve_path(path: str) -> str:
    """Resolve a relative project path into an absolute path under PROJECT_ROOT."""
    return os.path.join(PROJECT_ROOT, path)

# 3) Directory traversal (used by list_files_handler) ---------------------------------
def walk_directory(current_path: str, base_path: str, out: list[str]) -> None:
    """
    Recursively collect relative paths under current_path into 'out'.
   - Directories end with '/'.
   - Uses os.path.relpath(...) so output is relative to base_path.
    """
    for entry in os.listdir(current_path):
        full_path = os.path.join(current_path, entry)
        rel = os.path.relpath(full_path, base_path)

        # Skip the base directory itself; we only list children.
        if rel == ".":
            continue
        if os.path.isdir(full_path):
            out.append(rel + "/")
            walk_directory(full_path, base_path, out)
        else:
            out.append(rel)

# 4) Tool handlers ------------------------------------------------------------

def read_file_handler(path: str) -> str:
    """
    Read an entire text file (UTF-8) and return its contents, or an error message.
    STEP A: Resolve path relative to project root.
    STEP B: Try to open+read; on failure, return a friendly error string.

    """

    try:
        abs_path = resolve_path(path)
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"


def list_files_handler(directory: str = ".") -> str:

    """
    List all files/folders under 'directory' (relative to project root), recursively.
    Behavior:
      - If 'directory' equals the project folder name, list the root itself.
      - If directory doesn't exist, return a clear message.
      - Returns '(empty)' if nothing is found.
    """
    try:
        if directory == os.path.basename(PROJECT_ROOT):
            abs_dir = PROJECT_ROOT
        else:
            if directory:
                abs_dir = resolve_path(directory)
            else:
                abs_dir = resolve_path(".")

        if not os.path.exists(abs_dir):
            return f"Directory not found: {directory}"

        files: list[str] = []
        walk_directory(abs_dir, abs_dir, files)

        if files:
            return "\n".join(files)
        else:
            return "(empty)"
    except Exception as e:
        return f"Error listing files in {directory}: {e}"


def create_or_edit_file_handler(path: str, new_str: str, old_str: str = "") -> str:
    """
   Create/overwrite or edit a file, with predictable rules:
     MODE 1 (Create): If the file does NOT exist -> create it with 'new_str'.
                      (Parent dirs are auto-created.)
     MODE 2 (Overwrite): If the file exists AND 'old_str' is empty -> overwrite file with 'new_str'.
     MODE 3 (Single replace): If the file exists AND 'old_str' is provided:
                              - replace EXACTLY ONE occurrence of 'old_str' with 'new_str'
                              - if 0 matches -> error
                              - if >1 matches -> error
   """

    abs_path = resolve_path(path)

    # MODE 1: Create new file (ignores old_str)
    if not os.path.exists(abs_path):
        ensure_parent_dir(abs_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_str)
        return f"Created {path}"

    # MODE 2: Overwrite existing file when old_str is empty/missing
    if old_str == "":
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_str)
        return f"File {path} overwritten."

    # MODE 3: Replace exactly one occurrence in an existing file
    else:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        count = content.count(old_str)
        if count == 0:
            return "Error: old_str not found in file."
        if count > 1:
            return "Error: old_str matches multiple times; be explicit or narrow it down."

        new_content = content.replace(old_str, new_str, 1)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return "OK"


# 5) Tool definitions (metadata + schema used by the LLM) --------------------
# NOTE:
#  - The Agent passes these definitions to Anthropic so the model knows:
#      * the tool's name/description
#      * the expected JSON input schema (keys, required fields)
#  - At runtime the Agent maps tool_use.name -> ToolDefinition.handler and calls it
#    with handler(**tool_use.input).

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

list_files_tool = ToolDefinition(
    name= "list_files",
    description= "Lists files in a directory",
    input_schema= {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Directory path"
            }
        },
        "required": []
    },
    handler=list_files_handler
)

create_or_edit_file_tool = ToolDefinition(
    name= "edit_file",
    description=("Create/overwrite or edit a text file.\n"
                "- If the file does not exist: create it with new_str (old_str is ignored).\n"
                "- If the file exists and old_str is empty/missing: overwrite with new_str.\n"
                "- If the file exists and old_str is provided: replace exactly ONE occurrence."),
    input_schema= {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path from project root."},
            "old_str": {"type": "string", "description": "Text to replace (optional, only needed if editing)"},
            "new_str": {"type": "string", "description": "Text to replace old_str with"},
        },
        "required": ["path", "new_str"],
    },
    handler=create_or_edit_file_handler
)

# 6) Registration: expose tools and a name→definition lookup -----------------
tools = [read_file_tool, list_files_tool, create_or_edit_file_tool]

# tool_map lets the Agent do: tool_map[tool_use.name].handler(**tool_use.input)
tool_map = {}
for t in tools:
    tool_map[t.name] = t

