import datetime
import time
import random
import hashlib
import os


def log(value):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} INFO: {str(value)}\n"
        with open(
            "/Users/jeevanpillay/Code/@usr/lib/vedya/src/v1/api-vedya-draw/logfile.txt",
            "a",
        ) as file:
            file.write(log_message)
        print("Values written to logfile.txt successfully.")
    except Exception as e:
        print("An error occurred while writing to logfile.txt:", str(e))


def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        log(f"TIMER '{func.__name__}' took {end_time - start_time} seconds to run.")
        return result

    return wrapper


def create_random_string(length: int = 8) -> str:
    return "".join(
        random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=length)
    )


def create_array_random_unique_multiples(
    size: int, multiple: int = 8, min_multiple: int = 1, max_multiple: int = 10
):
    values = set()
    while len(values) < size:
        value = multiple * random.randint(min_multiple, max_multiple)
        values.add(value)
    return sorted(list(values))


def create_seed():
    """
    Generates a unique seed value based on the current time, process ID, and a random number.

    Returns:
        str: A unique seed value.
    """
    base_string = str(time.time()) + str(os.getpid()) + str(random.random())
    hash_object = hashlib.sha256(base_string.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig[:64]


def create_power_series_multiples(n):
    """
    Generate the first n multiples of 1, 2, 4, 8, 16...

    Args:
        n (int): The number of multiples to generate.

    Returns:
        list: A list of the first n multiples.
    """
    # Base multiplier
    multiplier = 1

    # List to hold the multiples
    multiples = []

    # Generate multiples
    for _ in range(n):
        multiples.append(multiplier)
        multiplier *= 2  # Update the multiplier for the next iteration

    return multiples
