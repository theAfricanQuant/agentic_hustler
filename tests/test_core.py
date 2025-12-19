import asyncio
from agentic_hustler import Task, Hustle
from pydantic import BaseModel

class Capital(BaseModel):
    logs: list[str] = []

class Payload(BaseModel):
    msg: str

# Note: Strictly 2 arguments [Capital, Payload]
class Echo(Task[Capital, Payload]):
    Requirements = Payload
    
    async def run_am(self, payload):
        return f"Echo: {payload.msg}"
        
    def deliver_am(self, station, payload, result):
        print(f"✅ {result}")

async def main():
    hustle = Hustle(start_task=Echo())
    await hustle.start(Capital(), {"msg": "We Move!"})

if __name__ == "__main__":
    asyncio.run(main())