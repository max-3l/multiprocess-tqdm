import logging
from contextlib import contextmanager
from itertools import repeat
from multiprocessing import Manager, Pool, Queue
from threading import Thread
from typing import Any, Iterable, List, Optional, Tuple, Union

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

class WriteMessage(Message):
    def __init__(self, write: str):
        self.key = "WRITE"
        self.value = write

class MPLoggingHandler(logging.Handler):
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    def emit(self, record: logging.LogRecord) -> None:
        self.queue.put(WriteMessage(self.format(record)))

@contextmanager
def override_logging_stream_handler(queue: Queue, logger: Optional[Iterable[logging.Logger]] = None):
    if logger is None:
        logger = [logging.root]
    original_handler = [[handler for handler in log.handlers] for log in logger]
    try:
        for log in logger:
            filtered_handlers = list(filter(lambda handler: type(handler) != logging.StreamHandler, log.handlers))
            try:
                removed_handler = next(filter(lambda handler: type(handler) == logging.StreamHandler, log.handlers))
            except StopIteration:
                continue
            new_handler = MPLoggingHandler(queue)
            new_handler.setFormatter(removed_handler.formatter)
            new_handler.setLevel(removed_handler.level)
            new_handlers = [new_handler] + filtered_handlers
            log.handlers = new_handlers
        yield
    finally:
        for log, handlers in zip(logger, original_handler):
            log.handlers = handlers


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
        with override_logging_stream_handler(self.queue):
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
            args=[(arg,) for arg in args],
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
            elif isinstance(msg, WriteMessage):
                bar.write(msg.value)
            elif isinstance(msg, StopMessage):
                break

    def __enter__(self) -> MPBar:
        self.thread.start()
        return MPBar(self.queue)

    def __exit__(self, *args, **kwargs) -> None:
        self.queue.put(StopMessage())
        self.thread.join()
