import asyncio
import os
from dotenv import load_dotenv
from agentic_hustler.llm import UniversalLLM

# Load environment variables
load_dotenv()

async def main():
    print(f"--- Testing LLM Connection ---")
    
    # 1. Check Key
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        print("❌ Error: OPENROUTER_API_KEY is missing in .env")
        return
    print(f"🔑 Key found: {key[:5]}...{key[-4:]}")

    # 2. Check Model
    # We use the clean ID from your .env
    model = os.getenv("DEFAULT_MODEL", "z-ai/glm-4.6")
    print(f"🤖 Target Model: {model}")
    
    # 3. Initialize Adapter
    llm = UniversalLLM() 
    
    print(f"📡 Sending request to OpenRouter...")
    try:
        response = await llm.chat(
            messages=[{"role": "user", "content": "Say 'Agentic Hustler is Online' in 3 words."}],
            model=model
        )
        print(f"\n✨ Success! Model says: {response}")
    except Exception as e:
        print(f"\n❌ Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())