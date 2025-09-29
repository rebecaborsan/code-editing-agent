import sys
from file_tools import tools, tool_map

# -----------------------------------------------------------------------------
# Agent (Anthropic Tool Use) - minimal, readable flow.
#
# What this file does:
#  - Keeps a running "conversation" list of messages.
#  - Sends your message and tool definitions to Claude.
#  - If Claude asks to use a tool (tool_use), we run it locally.
#  - We send the tool_result back to Claude as a USER message.
#  - We call Claude again to get the final assistant text.
#
# Key rules (Anthropic):
#  - Allowed roles: "user" and "assistant". There is NO "tool" role.
#  - tool_result must be sent as a "user" message with a content block
#    { "type": "tool_result", "tool_use_id": "...", "content": "..." }.
#  - This implementation handles a single tool_use per turn (keeps code simple).
# -----------------------------------------------------------------------------

class Agent:
    def __init__(self, client, get_user_message):
        self.client = client
        self.get_user_message = get_user_message

    def run(self):
        conversation = []

        print("Chat with Claude (use Ctrl+C to quit)")

        while True:
            sys.stdout.write("\033[94mYou\033[0m: ")
            sys.stdout.flush()

            result = self.get_user_message()
            user_input = result[0]
            ok = result[1]
            if not ok:
                break

            # add user's message in conversation
            user_message = {"role": "user", "content": user_input}
            conversation.append(user_message)

            # send to API
            message = self.run_interface(conversation)
            conversation.append({"role": "assistant", "content": message})

            # print the result
            print(f"\033[93mClaude\033[0m: {message}")

    def run_interface(self, conversation):
        # 1) First API call: send the full conversation + tool definitions
        response  = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=2000,
            messages=conversation,
            tools =[
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema
                } for t in tools
            ]
        )

        # 2) Parse response blocks: gather assistant text and detect a tool_us
        tool_use = None
        parts = []

        for block in response.content:
            if block.type == "text":
                parts.append(block.text)

            elif block.type == "tool_use":
                tool_use = block

        # 3) If no tool requested, return assistant text as-is
        if tool_use is None:
            final_input = "\n\n".join(parts)
            return final_input

        # 4) Log what the assistant just said (text + tool_use) into conversation
        #    This preserves the assistant's intent and tool request for the next turn.
        conversation.append({
            "role": "assistant",
            "content": [
                {"type": "text", "text": "\n".join(parts)},
                {
                    "type": "tool_use",
                    "id": tool_use.id,
                    "name": tool_use.name,
                    "input": tool_use.input
                }
            ]
        })

        # 5) Execute the requested tool locally (Python handler)
        #    tool_map[name] -> ToolDefinition -> handler(**input)
        tool = tool_map[tool_use.name]
        result_text = tool.handler(**tool_use.input)

        # 6) Send the tool_result BACK TO CLAUDE as a USER message
        #    IMPORTANT: role must be "user", type must be "tool_result",
        #    and it must reference the exact tool_use_id.
        conversation.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result_text
            }]
        })

        # 7) Second API call (follow-up): Claude sees tool_result and replies
        follow_up = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=2000,
            messages=conversation,
            tools=[{
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema
            } for t in tools]
        )

        # 8) Return only the textual parts of the final assistant message
        texts = []
        for block in follow_up.content:
            if block.type == "text":
                texts.append(block.text)

        final_text = "\n\n".join(texts)
        return final_text