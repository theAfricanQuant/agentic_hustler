import asyncio
import copy
import logging
from typing import Any, Awaitable, Callable, Generic, TypeVar

from pydantic import ValidationError

# Configure basic logging for the library
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Generic type variables for the core components
TCapital = TypeVar("TCapital")
TChange = TypeVar("TChange")
TOutput = TypeVar("TOutput")
TFunc = TypeVar("TFunc", bound=Callable[..., Awaitable[Any]])


def no_gree(max_retries: int = 3, initial_delay: float = 1.0) -> Callable[[TFunc], TFunc]:
    """
    A decorator to add resilience to async functions with retries and exponential backoff.

    Args:
        max_retries: The maximum number of retry attempts.
        initial_delay: The initial delay in seconds before the first retry.

    Returns:
        The decorated async function.
    """
    def decorator(func: TFunc) -> TFunc:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after {max_retries} retries. "
                            f"Final exception: {e}"
                        )
                        raise
                    else:
                        delay = initial_delay * (2**attempt)
                        logger.warning(
                            f"Function '{func.__name__}' failed (attempt {attempt + 1}/{max_retries + 1}). "
                            f"Retrying in {delay:.2f} seconds... Error: {e}"
                        )
                        await asyncio.sleep(delay)
            # This part should theoretically not be reached due to the raise in the loop
            raise last_exception

        return wrapper  # type: ignore
    return decorator


class DockingStation(Generic[TCapital, TChange]):
    """
    A memory-efficient, immutable container for state passed between tasks.
    """
    __slots__ = ('capital', 'change')

    def __init__(self, capital: TCapital, change: TChange):
        self.capital = capital
        self.change = change

    def undock(self) -> "DockingStation[TCapital, TChange]":
        """
        Creates a deep copy of the DockingStation for parallel execution.
        The 'capital' is shallow-copied (shared reference), while 'change' is deep-copied.
        """
        new_change = copy.deepcopy(self.change)
        return DockingStation(capital=self.capital, change=new_change)


class Task(Generic[TCapital, TChange, TOutput]):
    """
    The fundamental unit of work, a self-contained, reusable piece of logic.
    """
    async def check_am(self, station: DockingStation[TCapital, TChange]) -> None:
        """
        Validates the input state. Must be implemented by subclasses.
        Raises pydantic.ValidationError on failure.
        """
        raise NotImplementedError

    @no_gree()
    async def run_am(self, specs: TChange) -> TOutput:
        """
        The core async execution logic. Must be implemented by subclasses.
        """
        raise NotImplementedError

    async def deliver_am(
        self,
        station: DockingStation[TCapital, TChange],
        specs: TChange,
        output: TOutput,
    ) -> DockingStation[TCapital, TChange]:
        """
        Post-processes the result and updates the DockingStation.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def __rshift__(self, other: "Task[Any, Any, Any]") -> "Hustle[Any, Any]":
        """
        Chains this task with another to create a Hustle (workflow).
        """
        if not isinstance(other, Task):
            raise TypeError("Can only chain a Task with another Task.")
        return Hustle(tasks=[self, other])


class Hustle(Generic[TCapital, TChange]):
    """
    The orchestrator that manages the execution of a sequence of tasks.
    """
    def __init__(self, tasks: list[Task[TCapital, Any, Any]]):
        if not tasks:
            raise ValueError("A Hustle cannot be created with an empty list of tasks.")
        self.tasks = tasks

    def __rshift__(self, other: Task[TCapital, Any, Any]) -> "Hustle[TCapital, Any]":
        """
        Appends another task to the end of this Hustle.
        """
        if not isinstance(other, Task):
            raise TypeError("Can only chain a Hustle with a Task.")
        return Hustle(tasks=self.tasks + [other])

    async def run(
        self, initial_station: DockingStation[TCapital, TChange]
    ) -> DockingStation[TCapital, Any]:
        """
        Executes the sequence of tasks.
        """
        current_station = initial_station
        for i, task in enumerate(self.tasks):
            logger.info(f"Running task {i+1}/{len(self.tasks)}: {task.__class__.__name__}")
            
            # 1. Check/Validate input
            await task.check_am(current_station)
            
            # 2. Run the core logic
            specs = current_station.change
            output = await task.run_am(specs)
            
            # 3. Deliver and update state
            current_station = await task.deliver_am(current_station, specs, output)
            
        return current_station
