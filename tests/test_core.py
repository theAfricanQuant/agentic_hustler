import pytest
import asyncio
import agentic_hustler
import pydantic
import pathlib
import toml

def test_docking_station_init_and_slots():
    """
    Tests that DockingStation initializes correctly and uses __slots__.
    """
    capital_data = {"user_id": "user-123"}
    change_data = {"task_input": "process this"}

    station = agentic_hustler.DockingStation(capital=capital_data, change=change_data)

    # 1. Verify attributes are set correctly
    assert station.capital == capital_data
    assert station.change == change_data

    # 2. Verify that __slots__ is used (i.e., no __dict__)
    with pytest.raises(AttributeError):
        _ = station.__dict__

def test_docking_station_undock():
    """
    Tests that DockingStation.undock() creates a deep copy of 'change'
    and a shallow copy of 'capital'.
    """
    capital_data = {"user_id": "user-123"}
    change_data = {"items": [1, 2, 3]}

    original_station = agentic_hustler.DockingStation(capital=capital_data, change=change_data)
    
    # Create a new station by undocking
    new_station = original_station.undock()

    # 1. Verify 'capital' is the same object (shallow copy)
    assert new_station.capital is original_station.capital

    # 2. Verify 'change' is a different object (deep copy)
    assert new_station.change is not original_station.change
    assert new_station.change == original_station.change

    # 3. Modify the 'change' in the new station and ensure the original is unaffected
    new_station.change["items"].append(4)
    assert original_station.change["items"] == [1, 2, 3]
    assert new_station.change["items"] == [1, 2, 3, 4]

def test_hustle_init_and_rshift():
    """
    Tests Hustle initialization and chaining with the >> operator.
    """
    class DummyTask1(agentic_hustler.Task):
        async def check_am(self, station): pass
        async def run_am(self, specs): return "output1"
        async def deliver_am(self, station, specs, output): return station

    class DummyTask2(agentic_hustler.Task):
        async def check_am(self, station): pass
        async def run_am(self, specs): return "output2"
        async def deliver_am(self, station, specs, output): return station

    class DummyTask3(agentic_hustler.Task):
        async def check_am(self, station): pass
        async def run_am(self, specs): return "output3"
        async def deliver_am(self, station, specs, output): return station

    task1 = DummyTask1()
    task2 = DummyTask2()
    task3 = DummyTask3()

    # Test initialization with a list of tasks
    hustle = agentic_hustler.Hustle(tasks=[task1, task2])
    assert len(hustle.tasks) == 2
    assert hustle.tasks[0] is task1
    assert hustle.tasks[1] is task2

    # Test chaining a third task
    new_hustle = hustle >> task3
    assert isinstance(new_hustle, agentic_hustler.Hustle)
    assert len(new_hustle.tasks) == 3
    assert new_hustle.tasks[2] is task3

def test_hustle_init_with_empty_list_raises_error():
    """
    Tests that initializing a Hustle with an empty list of tasks raises a ValueError.
    """
    with pytest.raises(ValueError, match="A Hustle cannot be created with an empty list of tasks."):
        agentic_hustler.Hustle(tasks=[])

async def test_hustle_run_with_single_task():
    """
    Tests that Hustle.run() can execute a single, simple task.
    """
    class SimpleTask(agentic_hustler.Task):
        async def check_am(self, station):
            # For this simple test, we don't need validation.
            pass

        async def run_am(self, specs):
            # The core logic just returns a static value.
            return "task_complete"

        async def deliver_am(self, station, specs, output):
            # The delivery step doesn't change the station.
            return station

    # Setup
    initial_station = agentic_hustler.DockingStation(
        capital={"session_id": "abc-123"},
        change={"query": "hello world"}
    )
    task = SimpleTask()
    hustle = agentic_hustler.Hustle(tasks=[task])

    # Execute
    final_station = await hustle.run(initial_station)

    # Assert
    assert final_station is initial_station
    assert final_station.capital == {"session_id": "abc-123"}
    assert final_station.change == {"query": "hello world"}

async def test_hustle_run_with_sequence_of_tasks():
    """
    Tests that Hustle.run() can execute a sequence of tasks, passing state
    correctly from one to the next.
    """
    class TaskOne(agentic_hustler.Task):
        async def check_am(self, station):
            pass

        async def run_am(self, specs):
            # The core logic returns a value that will be used in deliver_am
            return {"processed_by": "TaskOne"}

        async def deliver_am(self, station, specs, output):
            # Create a new station with updated 'change' for the next task
            new_change = {
                "original_query": specs.get("query"),
                "result": output
            }
            return agentic_hustler.DockingStation(capital=station.capital, change=new_change)

    class TaskTwo(agentic_hustler.Task):
        async def check_am(self, station):
            pass

        async def run_am(self, specs):
            # This task uses the 'change' prepared by TaskOne
            assert specs["result"]["processed_by"] == "TaskOne"
            return {"final_status": "complete"}

        async def deliver_am(self, station, specs, output):
            # Update the 'change' one last time
            new_change = {
                **specs,
                "final_output": output
            }
            return agentic_hustler.DockingStation(capital=station.capital, change=new_change)

    # Setup
    initial_station = agentic_hustler.DockingStation(
        capital={"session_id": "xyz-789"},
        change={"query": "test sequence"}
    )
    task1 = TaskOne()
    task2 = TaskTwo()
    hustle = agentic_hustler.Hustle(tasks=[task1, task2])

    # Execute
    final_station = await hustle.run(initial_station)

    # Assert the final state
    assert final_station.capital == {"session_id": "xyz-789"}
    assert final_station.change == {
        "original_query": "test sequence",
        "result": {"processed_by": "TaskOne"},
        "final_output": {"final_status": "complete"},
    }

async def test_task_check_am_with_valid_pydantic_model():
    """
    Tests that check_am passes when station.change matches the Pydantic model.
    """
    class InputModel(pydantic.BaseModel):
        query: str
        limit: int = 10

    class ValidatingTask(agentic_hustler.Task):
        async def check_am(self, station):
            # This should not raise an exception
            InputModel.model_validate(station.change)

        async def run_am(self, specs):
            return "ok"

        async def deliver_am(self, station, specs, output):
            return station

    # Setup with valid data
    station = agentic_hustler.DockingStation(
        capital={},
        change={"query": "test", "limit": 5}
    )
    task = ValidatingTask()
    hustle = agentic_hustler.Hustle(tasks=[task])

    # This should run without error
    await hustle.run(station)


async def test_task_check_am_with_invalid_pydantic_model():
    """
    Tests that check_am raises pydantic.ValidationError for invalid data.
    """
    class InputModel(pydantic.BaseModel):
        query: str
        limit: int

    class ValidatingTask(agentic_hustler.Task):
        async def check_am(self, station):
            # This will raise a ValidationError
            InputModel.model_validate(station.change)

        async def run_am(self, specs):
            return "ok"

        async def deliver_am(self, station, specs, output):
            return station

    # Setup with invalid data (missing 'query', wrong type for 'limit')
    station = agentic_hustler.DockingStation(
        capital={},
        change={"limit": "not-an-int"}
    )
    task = ValidatingTask()
    hustle = agentic_hustler.Hustle(tasks=[task])

    # Assert that the ValidationError is raised during the run
    with pytest.raises(pydantic.ValidationError):
        await hustle.run(station)

async def test_task_run_am_with_no_gree_decorator():
    """
    Tests that the @no_gree decorator on run_am retries a failing task
    and allows it to eventually succeed.
    """
    class FlakyTask(agentic_hustler.Task):
        def __init__(self):
            self.call_count = 0

        async def check_am(self, station):
            pass

        @agentic_hustler.no_gree(max_retries=3, initial_delay=0.01)
        async def run_am(self, specs):
            self.call_count += 1
            if self.call_count < 3:
                raise ConnectionError("Temporary network failure")
            return {"status": "success"}

        async def deliver_am(self, station, specs, output):
            return station

    # Setup
    station = agentic_hustler.DockingStation(capital={}, change={})
    task = FlakyTask()
    hustle = agentic_hustler.Hustle(tasks=[task])

    # Execute
    final_station = await hustle.run(station)

    # Assert
    assert task.call_count == 3
    assert final_station is station

def test_public_api_exports():
    """
    Tests that all required components are exported from the top-level package.
    """
    from agentic_hustler import (
        Hustle,
        Task,
        DockingStation,
        UniversalLLM,
        no_gree,
    )

    assert Hustle is not None
    assert Task is not None
    assert DockingStation is not None
    assert UniversalLLM is not None
    assert no_gree is not None

def test_py_typed_file_exists():
    """
    Tests that the py.typed marker file exists in the package directory.
    """
    project_root = pathlib.Path(__file__).parent.parent
    py_typed_path = project_root / "src" / "agentic_hustler" / "py.typed"
    assert py_typed_path.is_file()

def test_pyproject_dependencies():
    """
    Tests that pyproject.toml contains the required dependencies.
    """
    project_root = pathlib.Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    data = toml.load(pyproject_path)
    dependencies = data.get("project", {}).get("dependencies", [])
    
    assert "pydantic>=2.0" in dependencies
    assert "openai>=1.0" in dependencies
