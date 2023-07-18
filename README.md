# multiprocess-tqdm
A tqdm wrapper for multiprocessing and multi-threading setups in python.

## Why

Were you ever in need to track process with a simple tqdm progress bar over multiple processes? Then you know the pain of creating a watcher thread or somehting similar that keeps track of processed items.

This small library implements this simple watcher thread and lets you focus on parallelizing your application!

## Usage

It is so easy that I think you will understand it with this one example.

```python3
import random
from multiprocess-tqdm import MPBar, MPtqdm
from time import sleep
from multiprocessing import Pool

# A function you want to parallize
def random_sleep(bar: MPBar):
    sleep(random.rand())
    bar.update(1)

# Create a multiprocessing pool
with Pool() as pool:
    num_iterations = 100
    # Create the progress bar within the pool context.
    with MPBar(description="Sleep Iteration", total=num_iterations, leave=True) as bar:
        # Pass the context object to the processes so that they can update the progress bar
        pool.map(random_sleep, (bar for _ in range(num_iterations)))
    # The progress bar is automatically closed
```
