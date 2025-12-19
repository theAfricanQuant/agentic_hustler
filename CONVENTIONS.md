# Agentic Hustler Coding Conventions

You are an expert using the `agentic_hustler` framework. Follow these rules strictly.

## 1. Architecture Patterns
* **Tasks:** Must inherit from `Task[TCapital, TChange]`.
    * **CRITICAL:** Only use 2 Generic arguments (Capital, Change). DO NOT add a 3rd argument for return type.
* **State:**
    * `TCapital` (Global): Must be a Pydantic Model. Shared across the whole Hustle.
    * `TChange` (Local): Must be a Pydantic Model. Passed between Tasks.
* **Logic:**
    * Implement `async def run_am(self, context)` for logic.
    * Implement `def deliver_am(self, station, context, result)` for state updates.
    * Use `self.next_task()` to move forward.
    * Use `>>` syntax for linear linking (e.g., `task_a >> task_b`).

## 2. Resilience
* **Network Calls:** Any Task performing I/O (LLM, API, DB) MUST use the `@no_gree` decorator.
    * Example: `@no_gree(retries=3, base_delay=1.0)`
* **Validation:** Use `Requirements = PydanticModel` in the Task class to enforce strict contracts.

## 3. LLM Usage
* **Adapter:** Always use `agentic_hustler.llm.UniversalLLM`.
* **Model Selection:**
    * Load the model ID from `os.getenv("AGENT_MODEL")`.
    * Do NOT hardcode model strings unless strictly necessary.
    * For OpenRouter, use the clean ID (e.g., `z-ai/glm-4.6`), NOT the `openrouter/` prefix.

## 4. Example Skeleton
```python
class MyTask(Task[GlobalState, LocalPayload]):
    Requirements = LocalPayload

    @no_gree(retries=2)
    async def run_am(self, payload: LocalPayload):
        llm = UniversalLLM()
        return await llm.chat(..., model=os.getenv("AGENT_MODEL"))

    def deliver_am(self, station, payload, result):
        station.capital.log.append(result)
        self.next_task()
