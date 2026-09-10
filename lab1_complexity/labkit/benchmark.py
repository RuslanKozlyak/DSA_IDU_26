"""Uninstrumented adaptive timing; a warm-up and seven retained batches."""
import gc
from time import perf_counter
import numpy as np


def time_samples(call, repeats=7):
    """Return seconds per call; calibration and setup are not retained."""
    def batch(number):
        enabled = gc.isenabled()
        gc.disable()
        try:
            start = perf_counter()
            for _ in range(number):
                call()
            return perf_counter() - start
        finally:
            if enabled:
                gc.enable()
    call()  # warm-up
    pilot = batch(1)
    number = min(4096, max(1, int(.002 / max(pilot, 1e-9))))
    batch(number)  # warm-up at the selected batch size
    return [batch(number) / number for _ in range(repeats)]


def summarize(samples):
    median, q1, q3 = np.quantile(samples, [.5, .25, .75])
    return {"Время, с": float(median), "Время Q1, с": float(q1),
            "Время Q3, с": float(q3)}
