# agentic_hustler Specification

A minimalist, resilient, async-first workflow engine for AI agents, built with strict typing and safety in mind.

## 0. Prieme Directive

You will not proceed with building any TASK if you have questions. Ask when you have any concerns. Only proceed when you are clear as to what you need to do.

## 1. Core Philosophy

The library is built on three non-negotiable principles:

- **"No Gree" (Resilience):** The system must be inherently resilient. All async operations, especially external calls like those to LLMs, must be automatically wrapped in a retry mechanism with exponential backoff. Failure is an expected condition, and the system must handle it gracefully.
- **"Strict Papers" (Safety):** All data entering a task must be validated. Pydantic models are the single source of truth for data schemas. No task processes raw, untyped data.
- **"Docking Station" (Isolation):** State is managed in isolated, immutable containers. This design allows for safe parallel execution and branching of workflows without state corruption or race conditions.

## 2. Architecture & Core Components

The system is composed of three primary components that interact to form a workflow.

### 2.1 `Task` (The Worker)

The fundamental unit of work. A `Task` is a self-contained, reusable piece of logic.

- **Class Signature:** `class Task(Generic[TCapital, TChange, TOutput]):`
  - `TCapital`: The type for the global, shared state.
  - `TChange`: The type for the local, task-specific context.
  - `TOutput`: The type for the result of the task's execution.

- **Lifecycle Methods:**
  1.  `check_am(self, station: DockingStation[TCapital, TChange]) -> None`:
      - An async method responsible for validating the input state.
      - Must use a Pydantic model to validate `station.change`.
      - Raises `pydantic.ValidationError` if the input is invalid.
  2.  `run_am(self, specs: TChange) -> TOutput`:
      - The core async execution logic of the task.
      - Receives the validated local context (`specs`).
      - **MUST** be compatible with the `@no_gree` decorator for automatic retries.
  3.  `deliver_am(self, station: DockingStation[TCapital, TChange], specs: TChange, output: TOutput) -> DockingStation[TCapital, TChange]`:
      - An async method responsible for post-processing.
      - Updates the `DockingStation`'s state (`capital` or `change`) based on the `output`.
      - Returns the (potentially modified) `DockingStation` to be passed to the next task.

- **Operator Overloading:**
  - Implements `__rshift__(self, other: "Task") -> "Hustle"` to enable intuitive workflow chaining: `task1 >> task2`.

### 2.2 `DockingStation` (The State Container)

A memory-efficient, immutable container that holds the state passed between tasks.

- **Class Signature:** `class DockingStation(Generic[TCapital, TChange]):`
- **Memory Efficiency:** Must use `__slots__ = ('capital', 'change')` to prevent the creation of `__dict__`.
- **Attributes:**
  - `capital: TCapital`: Global, shared state accessible by all tasks in a flow.
  - `change: TChange`: Local, task-specific context that is validated and consumed by a single task.
- **Branching Method:**
  - `undock(self) -> "DockingStation[TCapital, TChange]":`
      - Creates a deep copy of the `DockingStation`.
      - The `capital` attribute is a shallow copy (as it's shared).
      - The `change` attribute is a deep copy, ensuring complete isolation for parallel branches.

### 2.3 `Hustle` (The Flow)

The orchestrator that manages the execution of a sequence of tasks.

- **Creation:** Instantiated by chaining `Task` objects with the `>>` operator.
- **Core Method:** `async def run(self, initial_station: DockingStation[TCapital, TChange]) -> DockingStation[TCapital, TChange]:`
  - Takes an initial `DockingStation`.
  - Iterates through its internal queue of `Task` objects.
  - For each task, it calls the lifecycle methods in order: `check_am`, `run_am`, `deliver_am`.
  - The output `DockingStation` of one task becomes the input for the next.
  - Returns the final `DockingStation` after all tasks have completed.

## 3. The Universal LLM Adapter

A standardized, async adapter for interacting with various Large Language Model providers.

- **File:** `src/agentic_hustler/llm.py`
- **Class:** `class UniversalLLM:`
- **Implementation:**
  - A thin, robust wrapper around `openai.AsyncOpenAI`.
  - **Default Provider:** OpenRouter. The default `base_url` must be `https://openrouter.ai/api/v1`.
  - **API Key:** Must check for the `OPENROUTER_API_KEY` environment variable if no `api_key` is provided during instantiation.
  - **Flexibility:** Must support other providers (e.g., OpenAI, Ollama) by allowing a custom `base_url` to be passed.
- **Primary Method:** `async def acreate(self, messages: list[dict], **kwargs) -> ChatCompletion:`
  - Directly proxies the call to `self.client.chat.completions.create(...)`.

## 4. Project Structure

The project will use a standard `src` layout.

