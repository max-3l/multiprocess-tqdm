# multiprocess-tqdm
A tqdm wrapper for multiprocessing and multi-threading setups in python.

## Why

Were you ever in need to track process with a simple tqdm progress bar over multiple processes? Then you know the pain of creating a watcher thread or somehting similar that keeps track of processed items.

This small library implements this simple watcher thread and lets you focus on parallelizing your application!

## Usage

It is so easy that I think you will understand it with this one example.

```python
import random
from multiprocessing import Pool
from time import sleep

from multiprocess_tqdm import MPBar, MPtqdm


# A function you want to parallize
def random_sleep(bar: MPBar) -> None:
    "Sleep for a random amount, but maximum 100 ms."
    sleep(random.random() / 10)
    bar.update(1)

def main():
    # Create a multiprocessing pool
    with Pool() as pool:
        num_iterations = 100
        # Create the progress bar within the pool context.
        with MPtqdm(description="Bars done", total=1, leave=True) as bar:
            # We can easily nest multiple burs.
            # However, keep in mind that one thread per progress bar is created.
            with MPtqdm(description="Sleep Iteration", total=num_iterations, leave=False) as bar2:
                # Pass the context object to the processes so that they can update the progress bar
                pool.map(random_sleep, (bar2 for _ in range(num_iterations)))
            bar.update(1)
        # The progress bar is automatically closed

if __name__ == '__main__':
    main()
```

## Installation

This library is currently not published anywhere but a t GitHub. Therefore you need to install it from source.

### From Source

You can either clone and install the library locally

```bash
git clone https://github.com/max-3l/multiprocess-tqdm
python -m pip install -e multiprocess-tqdm
```

or you can directly instruct pip to install from git

```bash
pip install git+https://github.com/max-3l/multiprocess-tqdm
```
