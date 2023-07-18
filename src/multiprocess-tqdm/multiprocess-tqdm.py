from multiprocessing import Manager, Queue
from threading import Thread
from typing import Optional, Union

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

class MPtqdm:
    def __init__(self, description: str = "", total: Optional[int] = None, leave: Optional[bool] = True):
        self.manager = Manager()
        self.queue = Queue()
        self.description = description
        self.total = total
        self.leave = leave
        self.bar = tqdm(disable=True, description=description, total=total, leave=leave)
        self.thread = Thread(target=self.run)
    
    def run(self):
        self.bar.disable = False
        self.bar.refresh()
        while True:
            msg = self.queue.get()
            if isinstance(msg, UpdateMessage):
                self.bar.update(msg.value)
            if isinstance(msg, StopMessage):
                break

    def __enter__(self) -> None:
        self.thread.run()
        return MPBar(self.queue)

    def __exit__(self, *args, **kwargs) -> None:
        self.queue.put(StopMessage())
        self.thread.join()
