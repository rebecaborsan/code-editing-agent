import os
from anthropic import Anthropic
from dotenv import load_dotenv
import sys
from agent import Agent


load_dotenv()

def get_user_message():
    line = sys.stdin.readline()
    if not line:
        return "", False
    return line.strip(), True


def main():
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    agent = Agent(client, get_user_message)
    try:
        agent.run()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()