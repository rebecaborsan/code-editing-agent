import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


client = Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

while True:
    message = client.messages.create(
        model="claude-3-7-sonnet-latest",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": input("Rebeca: ")}
        ]
    )
    print(f"Claude: {message.content[0].text}")