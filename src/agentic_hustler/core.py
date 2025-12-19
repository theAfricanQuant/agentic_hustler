import copy
import asyncio
import logging
import random
from typing import TypeVar, Generic, Dict, List, Optional, NamedTuple, Any, Type
from functools import wraps
from pydantic import BaseModel, ValidationError

# --- Telemetry ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("AgenticHustler")

def log_gist(event, **kwargs):
    msg = f"[{event}] " + " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(msg)

# --- Resilience ---
def no_gree(retries=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        log_gist("WAHALA", task=self.__class__.__name__, error=str(e))
                        raise e
                    wait = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                    log_gist("RETRY", task=self.__class__.__name__, attempt=attempt+1, wait=f"{wait:.2f}s")
                    await asyncio.sleep(wait)
        return wrapper
    return decorator

# --- Types ---
TCapital = TypeVar("TCapital") 
TChange = TypeVar("TChange")   

class DockingStation(Generic[TCapital, TChange]):
    __slots__ = ['capital', 'change', 'tag']

    def __init__(self, capital: TCapital, change: TChange, tag: str = "Root"):
        self.capital = capital
        self.change = change
        self.tag = tag

    def undock(self, new_change_data: Optional[Dict] = None) -> 'DockingStation[TCapital, TChange]':
        new_change = copy.deepcopy(self.change)
        if isinstance(new_change, dict) and new_change_data:
            new_change.update(new_change_data) # type: ignore
        elif isinstance(new_change, BaseModel) and new_change_data:
            new_change = new_change.model_copy(update=new_change_data)
        new_tag = f"{self.tag}.{random.randint(100,999)}"
        return DockingStation(self.capital, new_change, tag=new_tag)

class NextMove(NamedTuple):
    route: str
    payload: Optional[Dict[str, Any]] = None

# --- The Task (Strictly 2 Generics) ---
class Task(Generic[TCapital, TChange]):
    Requirements: Optional[Type[BaseModel]] = None

    def __init__(self):
        self._connections: Dict[str, 'Task'] = {}
        self._moves: List[NextMove] = []

    def check_am(self, station: DockingStation[TCapital, TChange]) -> Any:
        if self.Requirements and isinstance(station.change, dict):
            try:
                return self.Requirements(**station.change)
            except ValidationError as e:
                log_gist("BAD_PAYLOAD", tag=station.tag, error=str(e))
                raise e
        return station.change

    @no_gree(retries=3)
    async def run_am(self, specs: Any) -> Any:
        return specs

    def deliver_am(self, station: DockingStation[TCapital, TChange], specs: Any, output: Any) -> None:
        pass

    def next_task(self, route_name="forward", payload=None):
        self._moves.append(NextMove(route_name, payload))

    def link(self, route_name, next_task_instance):
        self._connections[route_name] = next_task_instance
        return next_task_instance

    def __rshift__(self, other_task):
        return self.link("forward", other_task)

    async def _execute(self, station: DockingStation[TCapital, TChange]) -> List[NextMove]:
        self._moves = []
        specs = self.check_am(station)
        log_gist("START_OP", task=self.__class__.__name__, tag=station.tag)
        output = await self.run_am(specs)
        self.deliver_am(station, specs, output)
        log_gist("OP_COMPLETE", task=self.__class__.__name__, tag=station.tag)
        if not self._moves:
            return [NextMove("forward", None)]
        return self._moves

class Hustle(Generic[TCapital, TChange]):
    def __init__(self, start_task: Task[TCapital, TChange]):
        # 🔴 WAS: self.start = start_task  (This caused the bug)
        # 🟢 CHANGE TO:
        self.entry_task = start_task

    async def start(self, initial_capital: TCapital, initial_change: TChange):
        first_station = DockingStation(initial_capital, initial_change)
        
        # 🔴 WAS: queue = [(self.start, first_station)]
        # 🟢 CHANGE TO:
        queue = [(self.entry_task, first_station)]
        
        while queue:
            current_task, current_station = queue.pop(0)
            moves = await current_task._execute(current_station)
            for m in moves:
                if m.route in current_task._connections:
                    next_task_instance = current_task._connections[m.route]
                    new_station = current_station.undock(m.payload)
                    queue.append((next_task_instance, new_station))
