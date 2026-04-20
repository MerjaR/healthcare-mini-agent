# verify_setup.py
# Run this to confirm your environment is ready before starting the agent.

from utils.helpers import get_api_key
import anthropic

def verify():
    print("Verifying setup...")

    # Check API key
    key = get_api_key()
    print(f"✅ API key loaded: {key[:8]}...")

    # Check SDK connectivity
    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=32,
    messages=[{"role": "user", "content": "Reply with: Setup OK"}]
)
    print(f"✅ Claude responds: {response.content[0].text}")
    print("\nAll good — ready to run the agent.")

if __name__ == "__main__":
    verify()