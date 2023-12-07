from multiprocessing import Manager, Queue, Pool
from threading import Thread
from typing import Optional, Union, List, Any, Iterable, Tuple
from itertools import repeat

from tqdm import tqdm


class Message:
    key: str
    value: Union[str, int]

class UpdateMessage(Message):
    def __init__(self, update_by=1):
        self.key = "UPDATE"
        self.value = update_by

class StopMessage(Message):
    def __init__(self):
        self.key = "STOP"
        self.value = "STOP"

class PostfixMessage(Message):
    def __init__(self, postfix: dict):
        self.key = "POSTFIX"
        self.value = postfix

class NewTotalMessage(Message):
    def __init__(self, new_total: int):
        self.key = "NEW_TOTAL"
        self.value = new_total

class AddTotalMessage(Message):
    def __init__(self, add_total: int):
        self.key = "ADD_TOTAL"
        self.value = add_total

class MPBar:
    """A progress bar client that communicates with a multiprocess progress bar
    to track process over multiple processes.
    """
    def __init__(self, queue: Queue):
        """
        Args:
            queue (Queue): The communcation queue to the progress bar.
        """
        self.queue = queue
    
    def update_total(self, new_total: int):
        self.queue.put(NewTotalMessage(new_total))
    
    def add_total(self, add_total: int):
        self.queue.put(AddTotalMessage(add_total))

    def update(self, update_by=1):
        """Update the progress bar.

        Args:
            update_by (int, optional): The number of steps to advance. Defaults to 1.
        """
        self.queue.put(UpdateMessage(update_by))

    def postfix(self, postfix: dict):
        """Set the postfix of the progress bar.

        Args:
            postfix (dict): A dictionary of key - value pairs that are converted 
            to the postfix string.
        """
        self.queue.put(PostfixMessage(postfix))

    def run_and_update(self, call: callable, args: Tuple[Any]) -> Any:
        result = call(*args)
        self.update(1)
        return result

class MPtqdm:
    def __init__(self, description: str = "", total: Optional[int] = None, leave: Optional[bool] = True, postfix: Optional[dict] = None):
        self.manager = Manager()
        self.queue = self.manager.Queue()
        self.description = description
        self.total = total
        self.leave = leave
        self.postfix = postfix
        self.thread = Thread(target=self.run)

    @staticmethod
    def map(pool: Pool, call: callable, args: Iterable[Any], description: str = "", total: Optional[int] = None, leave: Optional[bool] = True, postfix: Optional[dict] = None) -> List[Any]:
        return MPtqdm.starmap(
            pool=pool,
            call=call,
            args=((arg,) for arg in args),
            description=description,
            total=total,
            leave=leave,
            postfix=postfix
        )
    
    @staticmethod
    def starmap(pool: Pool, call: callable, args: Iterable[Tuple[Any]], description: str = "", total: Optional[int] = None, leave: Optional[bool] = True, postfix: Optional[dict] = None) -> List[Any]:
        try:
            total = len(args)
        except:
            pass
        manager = MPtqdm(description=description, total=total, postfix=postfix, leave=leave)
        with manager as pbar:
            return pool.starmap(pbar.run_and_update, zip(repeat(call), args))

    def run(self):
        bar = tqdm(desc=self.description, total=self.total, leave=self.leave, postfix=self.postfix)
        while True:
            msg = self.queue.get()
            if isinstance(msg, UpdateMessage):
                bar.update(msg.value)
            elif isinstance(msg, PostfixMessage):
                bar.set_postfix(msg.value)
            elif isinstance(msg, NewTotalMessage):
                bar.total = msg.value
                bar.refresh()
            elif isinstance(msg, AddTotalMessage):
                bar.total += msg.value
                bar.refresh()
            elif isinstance(msg, StopMessage):
                break

    def __enter__(self) -> MPBar:
        self.thread.start()
        return MPBar(self.queue)

    def __exit__(self, *args, **kwargs) -> None:
        self.queue.put(StopMessage())
        self.thread.join()
