import json
from pathlib import Path
from uuid import uuid4

THREADS_FILE = Path(__file__).resolve().parent / "threads.json"

if THREADS_FILE.exists():
    print("threads.jsonは既にあります。")
else:
    threads = []
    for name in ["日誌", "今日の食事", "ネガティブノート"]:
        threads.append({
            "id": str(uuid4()),
            "name": name
        })

    with THREADS_FILE.open("w", encoding="utf-8") as f:
        json.dump(threads, f, ensure_ascii=False, indent=2)

    print("保存したスレッド数:", len(threads))