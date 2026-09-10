"""Small deterministic performance smoke suite for core raster operations.

Run manually with: python benchmarks/benchmark_canvas.py
It intentionally uses modest defaults so CI and developer machines are not
forced to allocate an 8000x8000 image just to run the benchmark.
"""

from __future__ import annotations

import statistics
import time

from ordpaint.core.document import Document


CASES = ((512, 512), (2048, 2048), (4096, 4096))
RUNS = 3


def measure(width: int, height: int) -> float:
    samples = []
    for _ in range(RUNS):
        start = time.perf_counter()
        document = Document(width, height)
        document.scale_image(max(1, width // 2), max(1, height // 2))
        samples.append(time.perf_counter() - start)
    return statistics.median(samples)


def main() -> None:
    print("OrdPaint benchmark: Document creation + image scaling")
    for width, height in CASES:
        seconds = measure(width, height)
        print(f"{width}x{height}: {seconds:.4f}s median over {RUNS} runs")


if __name__ == "__main__":
    main()
