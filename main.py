import os
from anthropic import Anthropic
from dotenv import load_dotenv
import sys
from file_tools import tools, tool_map

load_dotenv()

def get_user_message():
    line = sys.stdin.readline()
    if not line:
        return "", False
    return line.strip(), True


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
        response  = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=512,
            messages=conversation,
            tools =[
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema
                } for t in tools
            ]
        )

        # take only the text from the response
        # example of block:
        # {
        #   "type": "tool_use",
        #   "id": "toolu_abc123",
        #   "name": "read_file",
        #   "input": {
        #     "path": "main.py"
        #   }
        # }
        parts = []
        for block in response.content:
            if block.type == "text":
                parts.append(block.text)

            elif block.type == "tool_use":
                tool = tool_map[block.name]
                result = tool.handler(**block.input)
                print(f"Tool {tool.name} executed -> {result}")
                parts.append(result)

        final_input = "".join(parts)
        return final_input


def main():
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    agent = Agent(client, get_user_message)
    try:
        agent.run()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()