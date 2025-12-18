# agentic_hustler Development Tasks

This document outlines the concrete, test-driven development (TDD) tasks required to complete the `agentic_hustler` library according to its specification.

Each task will follow the TDD cycle:
1.  **Write a failing test** that defines a specific piece of functionality.
2.  **Implement the minimal code** required to make the test pass.
3.  **Refactor** the code while ensuring the test still passes.

---

### Core Engine (`src/agentic_hustler/core.py`)

-   `[x] 1. Implement `DockingStation.__init__` and `__slots__`**
    -   **Test:** Create a `DockingStation` instance and verify `capital` and `change` attributes are set correctly. Verify that `__dict__` is not present on the instance.

-   `[x] 2. Implement `DockingStation.undock()`**
    -   **Test:** Create a `DockingStation` with a mutable `change` (e.g., a list). Call `undock()` to create a new station. Modify the `change` in the new station and assert the original station's `change` is unaffected. Assert that `capital` is the same object (shallow copy).

-   `[x] 3. Implement `no_gree` decorator for successful calls**
    -   **Test:** Create a simple async function decorated with `@no_gree()`. Call it and assert it returns the expected value without any retries.

-   `[x] 4. Implement `no_gree` decorator for retries and eventual failure**
    -   **Test:** Create an async function that fails 3 times with a `ValueError` before succeeding. Decorate it with `@no_gree(max_retries=3)`. Assert that the function eventually succeeds and the test logs show retry attempts.
    -   **Test:** Create an async function that always fails. Decorate it with `@no_gree(max_retries=2)`. Assert that it raises the final exception after exhausting retries.

-   `[x] 5. Implement `Task` base class and `__rshift__` operator**
    -   **Test:** Create two dummy subclasses of `Task`. Use the `>>` operator to chain them. Assert that the result is an instance of `Hustle` and that its internal `tasks` list contains the two task instances in the correct order.

-   `[x] 6. Implement `Hustle.__init__` and `__rshift__`**
    -   **Test:** Create a `Hustle` with a list of tasks. Use `>>` to append a third task. Assert the new `Hustle` instance contains all three tasks.
    -   **Test:** Assert that `Hustle([])` raises a `ValueError`.

-   `[x] 7. Implement `Hustle.run()` with a single, simple task**
    -   **Test:** Create a concrete `Task` where `check_am` and `deliver_am` simply pass, and `run_am` returns a value. Create a `Hustle` with this task. Run the hustle and assert that the final `DockingStation` is returned.

-   `[x] 8. Implement `Hustle.run()` with a sequence of tasks**
    -   **Test:** Create two concrete tasks. The first task's `deliver_am` should update the `change` for the next task. The second task's `run_am` should use this updated `change`. Run the `Hustle` and assert the final state is correct.

-   `[x] 9. Implement `Task.check_am()` with Pydantic validation**
    -   **Test:** Create a `Task` that expects a Pydantic model in `check_am`. Provide a valid `DockingStation` and assert no exception is raised.
    -   **Test:** Provide an invalid `DockingStation` (e.g., missing a required field in `change`) and assert that `pydantic.ValidationError` is raised.

-   `[x] 10. Implement `Task.run_am()` with `@no_gree`**
    -   **Test:** Create a `Task` where `run_am` is designed to fail twice before succeeding. Run the `Hustle` and assert it completes successfully, verifying the `no_gree` decorator is active.

### LLM Adapter (`src/agentic_hustler/llm.py`)

-   `[x] 11. Implement `UniversalLLM.__init__()` with default OpenRouter settings**
    -   **Test:** Instantiate `UniversalLLM` without arguments. Mock `os.environ.get` to return a fake API key. Assert the internal `AsyncOpenAI` client is configured with the OpenRouter `base_url` and the mocked key.

-   `[x] 12. Implement `UniversalLLM.__init__()` with custom settings**
    -   **Test:** Instantiate `UniversalLLM` with a custom `api_key` and `base_url` (e.g., for Ollama). Assert the internal client is configured with these custom values.

-   `[x] 13. Implement `UniversalLLM.__init__()` error handling**
    -   **Test:** Mock `os.environ.get` to return `None`. Attempt to instantiate `UniversalLLM` without an `api_key`. Assert that a `ValueError` is raised with the correct message.

-   `[x] 14. Implement `UniversalLLM.acreate()`**
    -   **Test:** Create a `UniversalLLM` instance. Mock its internal `self.client.chat.completions.create` method to return a predefined `ChatCompletion` object. Call `acreate` with sample messages and assert it returns the mocked object and that the mock was called with the correct arguments.

### Project Structure and Exports

-   `[x] 15. Verify `__init__.py` exports**
    -   **Test:** Write a test that imports `Hustle`, `Task`, `DockingStation`, `UniversalLLM`, and `no_gree` directly from the `agentic_hustler` package (e.g., `from agentic_hustler import Hustle`). The test passes if the imports succeed.

-   `[x] 16. Verify `py.typed` presence**
    -   **Test:** Write a simple script that programmatically checks for the existence of the file `src/agentic_hustler/py.typed`. The test passes if the file is found.

-   `[x] 17. Verify `pyproject.toml` dependencies**
    -   **Test:** Write a test that reads `pyproject.toml` and asserts that `pydantic` and `openai` are listed in the `[project.dependencies]` array.
