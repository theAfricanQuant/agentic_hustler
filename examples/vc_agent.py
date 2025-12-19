import asyncio
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from agentic_hustler import Task, Hustle, UniversalLLM, no_gree

# 1. Setup
load_dotenv()
MODEL_ID = os.getenv("DEFAULT_MODEL") 

# 2. Define the "Papers" (State)
class VCFirm(BaseModel):
    """The Capital: Global state of the firm."""
    portfolio: list[str] = []
    rejected: list[str] = []

class PitchDeck(BaseModel):
    """The Change: The startup moving through the pipeline."""
    startup_name: str
    idea: str
    analysis: str = ""
    decision: str = ""

# 3. Task 1: The Analyst (The Cynic)
class MarketAnalyst(Task[VCFirm, PitchDeck]):
    Requirements = PitchDeck # Auto-validates input

    @no_gree(retries=2)
    async def run_am(self, deck: PitchDeck):
        print(f"\n🧐 [Analyst] Reviewing '{deck.startup_name}' on {MODEL_ID}...")
        
        llm = UniversalLLM()
        return await llm.chat(
            messages=[{
                "role": "system", 
                "content": "You are a cynical VC analyst. Find 3 fatal flaws in this idea. Be brief."
            }, {
                "role": "user", 
                "content": f"Idea: {deck.idea}"
            }],
            model=MODEL_ID 
        )

    def deliver_am(self, station, deck, analysis):
        # Save analysis to the deck
        station.change.analysis = analysis
        print(f"📝 [Analyst] Report filed.")
        
        # Pass to the Investor
        self.next_task()

# 4. Task 2: The Investor (The Decision Maker)
class AngelInvestor(Task[VCFirm, PitchDeck]):
    
    async def run_am(self, deck: PitchDeck):
        print(f"💰 [Investor] Reading report...")
        
        llm = UniversalLLM()
        return await llm.chat(
            messages=[{
                "role": "system", 
                "content": "You are a VC. Based on the analysis, output ONLY 'FUND' or 'PASS'."
            }, {
                "role": "user", 
                "content": f"Idea: {deck.idea}\n\nAnalyst Report: {deck.analysis}"
            }],
            model=MODEL_ID
        )

    def deliver_am(self, station, deck, decision):
        station.change.decision = decision
        
        # Update Global Capital
        if "FUND" in decision.upper():
            station.capital.portfolio.append(deck.startup_name)
            print(f"🚀 [DECISION] {deck.startup_name} -> FUNDED!")
        else:
            station.capital.rejected.append(deck.startup_name)
            print(f"❌ [DECISION] {deck.startup_name} -> PASSED.")

# 5. The Hustle (Execution)
async def main():
    # A. Wire the Graph
    analyst = MarketAnalyst()
    investor = AngelInvestor()
    
    # "Analyst passes work to Investor"
    analyst >> investor
    
    # B. Initialize
    pipeline = Hustle(start_task=analyst)
    firm = VCFirm() # Empty portfolio
    
    # C. Run Pitch #1
    # ✅ CORRECT (Wrap it in the Class)
    pitch1 = PitchDeck(
        startup_name="UberForCats",
        idea="A ride-sharing app where cats drive the cars."
    )
    await pipeline.start(firm, pitch1)

    # Do the same for pitch2
    pitch2 = PitchDeck(
        startup_name="CureAI",
        idea="AI that cures baldness using quantum computing."
    )
    await pipeline.start(firm, pitch2)

    print(f"\n📂 Final Portfolio: {firm.portfolio}")

if __name__ == "__main__":
    asyncio.run(main())