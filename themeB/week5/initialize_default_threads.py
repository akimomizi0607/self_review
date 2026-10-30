"""threads.jsonがないときだけ、最初の3つのスレッドを作る。"""

import json
from pathlib import Path
from uuid import uuid4

THREADS_DATA_FILE = Path(__file__).resolve().parent / "threads.json"
DEFAULT_THREAD_NAMES = ("日誌", "今日の食事", "ネガティブノート")


def initialize_default_threads_if_missing():
    if THREADS_DATA_FILE.exists():
        print("threads.jsonは既にあります。")
        return

    default_threads = [
        {"id": str(uuid4()), "name": default_thread_name}
        for default_thread_name in DEFAULT_THREAD_NAMES
    ]
    with THREADS_DATA_FILE.open("w", encoding="utf-8") as threads_data_file:
        json.dump(default_threads, threads_data_file, ensure_ascii=False, indent=2)
    print("保存したスレッド数:", len(default_threads))


if __name__ == "__main__":
    initialize_default_threads_if_missing()
