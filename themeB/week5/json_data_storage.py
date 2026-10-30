"""投稿・スレッドをUTF-8のJSONファイルに保存し、読み出す。"""

import json
from pathlib import Path

from flask import current_app


def load_records_from_json_file(data_file_path):
    """初回起動でファイルがない場合は空の一覧を返す。読込エラーは隠さない。"""
    data_file_path = Path(data_file_path)
    if not data_file_path.exists():
        return []

    with data_file_path.open("r", encoding="utf-8") as data_file:
        return json.load(data_file)


def save_records_to_json_file(data_file_path, records_to_save):
    with Path(data_file_path).open("w", encoding="utf-8") as data_file:
        json.dump(records_to_save, data_file, ensure_ascii=False, indent=2)


def load_saved_posts():
    return load_records_from_json_file(current_app.config["POSTS_DATA_FILE"])


def save_posts(saved_posts):
    save_records_to_json_file(current_app.config["POSTS_DATA_FILE"], saved_posts)


def load_saved_threads():
    return load_records_from_json_file(current_app.config["THREADS_DATA_FILE"])


def save_threads(saved_threads):
    save_records_to_json_file(current_app.config["THREADS_DATA_FILE"], saved_threads)


def find_saved_thread_by_name(requested_thread_name):
    for saved_thread in load_saved_threads():
        if saved_thread["name"] == requested_thread_name:
            return saved_thread
    return None


def find_saved_post_in_thread(saved_posts, requested_post_id, requested_thread_name):
    for saved_post in saved_posts:
        if (
            saved_post.get("id") == requested_post_id
            and saved_post["thread_name"] == requested_thread_name
        ):
            return saved_post
    return None
