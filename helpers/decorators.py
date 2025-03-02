import time
from logger import Logger as logger


def retry(max_retries: int, retry_delay: int):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            for retry in range(max_retries):
                try:
                    result = func(self, *args, **kwargs)
                    return result
                except Exception as e:
                    logger.error(f"Error connecting to the database: {str(e)}")
                    if retry < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error("Max retry attempts reached.")
                        raise e
        return wrapper
    return decorator


def calc_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"-> Execution time: {end - start} seconds")
        return result
    return wrapper
