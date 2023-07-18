import random
from multiprocessing import Pool
from time import sleep

from multiprocess_tqdm import MPBar, MPtqdm


# A function you want to parallize.
def random_sleep(bar: MPBar) -> None:
    "Sleep for a random amount, but maximum 100 ms."
    sleep(random.random() / 10)
    bar.update(1)

def main():
    # Create a multiprocessing pool.
    with Pool() as pool:
        num_iterations = 100
        # Create the progress bar within the pool context.
        with MPtqdm(description="Bars done", total=1, leave=True) as bar:
            # We can easily nest multiple progress bars.
            # However, keep in mind that one thread per progress bar is created.
            with MPtqdm(description="Sleep Iteration", total=num_iterations, leave=False) as bar2:
                # Pass the context object to the processes so that they can update the progress bar.
                pool.map(random_sleep, (bar2 for _ in range(num_iterations)))
            bar.update(1)
        # The progress bars are automatically closed and the threads are automatically stopped.

if __name__ == '__main__':
    main()
