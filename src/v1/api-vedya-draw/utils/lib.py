import datetime
import time
import random


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
