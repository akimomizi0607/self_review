import json
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from datetime import date, datetime
from uuid import uuid4
app = Flask(__name__)
THREADS_FILE = Path(__file__).resolve().parent / "threads.json"
POSTS_FILE = Path(__file__).resolve().parent / "posts.json"
def load_threads():
    if not THREADS_FILE.exists():
        return []
    with THREADS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)
def find_thread(thread_name):
    for thread in load_threads():
        if thread["name"] == thread_name:
            return thread
    return None

@app.route("/")
def index():
    today = date.today().strftime("%Y年%m月%d日")
    threads = load_threads()
    return render_template("index.html", today=today, threads=threads)
@app.route("/threads/<thread_name>", methods=["GET", "POST"])
def show_thread(thread_name):
    if find_thread(thread_name) is None:
        return render_template("input_error.html", message="スレッドが見つかりません。"), 404
    rating = None
    headtext = None
    bodytext = None
    if POSTS_FILE.exists():
        with POSTS_FILE.open("r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
            posts = []
    print("保存済み投稿数:", len(posts))
    if request.method == "POST":
        rating = request.form.get("rating")
        headtext = request.form.get("headtext", "").strip()
        bodytext = request.form.get("bodytext", "").strip()
        if not rating:
            return render_template("input_error.html", message="星評価を選択してください。"), 400
        if not headtext:
            return render_template("input_error.html", message="見出しを入力してください。"), 400
        if not bodytext:
            return render_template("input_error.html", message="内容を入力してください。"), 400
        print("受け取った星評価:", rating)
        print("受け取った見出し:", headtext)
        print("受け取った内容:", bodytext)
        post = {
            "id": str(uuid4()),
            "thread_name": thread_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rating": rating,
            "headtext": headtext,
            "bodytext": bodytext
        }
        print("保存する投稿:", post)

        posts.append(post)

        with POSTS_FILE.open("w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        return redirect(url_for("show_thread", thread_name=thread_name), code=303)
    thread_posts = []
    for post in posts:
        if post["thread_name"] == thread_name:
            thread_posts.append(post)
    return render_template(
        "thread.html",
        thread_name=thread_name,
        rating=rating,
        headtext=headtext,
        bodytext=bodytext,
        thread_posts=thread_posts
    )
@app.route("/threads/<thread_name>/new")
def new_post(thread_name):
    if find_thread(thread_name) is None:
        return render_template("input_error.html", message="スレッドが見つかりません。"), 404
    return render_template("post.html", thread_name=thread_name)
@app.route("/threads/<thread_name>/confirm", methods=["POST"])
def confirm_post(thread_name):
    if find_thread(thread_name) is None:
        return render_template("input_error.html", message="スレッドが見つかりません。"), 404
    rating = request.form.get("rating")
    headtext = request.form.get("headtext", "").strip()
    bodytext = request.form.get("bodytext", "").strip()
    if not rating:
        return render_template("input_error.html", message="星評価を選択してください。"), 400
    if not headtext:
        return render_template("input_error.html", message="見出しを入力してください。"), 400
    if not bodytext:
        return render_template("input_error.html", message="内容を入力してください。"), 400
    return render_template(
        "confirm.html",
        thread_name=thread_name,
        rating=rating,
        headtext=headtext,
        bodytext=bodytext
    )
@app.route("/threads/<thread_name>/delete")
def select_delete(thread_name):
    if POSTS_FILE.exists():
        with POSTS_FILE.open("r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = []

    thread_posts = []
    for post in posts:
        if post["thread_name"] == thread_name:
            thread_posts.append(post)

    return render_template(
        "delete_post.html",
        thread_name=thread_name,
        thread_posts=thread_posts
    )
@app.route("/threads/<thread_name>/delete/confirm", methods=["POST"])
def confirm_delete(thread_name):
    post_id = request.form.get("post_id")
    if not post_id:
        return render_template("input_error.html", message="削除する投稿を選択してください。"), 400

    posts = []
    if POSTS_FILE.exists():
        with POSTS_FILE.open("r", encoding="utf-8") as f:
            posts = json.load(f)

    for post in posts:
        if post.get("id") == post_id and post["thread_name"] == thread_name:
            return render_template(
                "delete_confirm.html",
                thread_name=thread_name,
                post=post
            )

    return render_template("input_error.html", message="選択した投稿が見つかりません。"), 404
@app.route("/threads/<thread_name>/delete/execute", methods=["POST"])
def execute_delete(thread_name):
    post_id = request.form.get("post_id")
    if not post_id:
        return render_template("input_error.html", message="削除する投稿を選択してください。"), 400

    posts = []
    if POSTS_FILE.exists():
        with POSTS_FILE.open("r", encoding="utf-8") as f:
            posts = json.load(f)

    for post in posts:
        if post.get("id") == post_id and post["thread_name"] == thread_name:
            posts.remove(post)
            with POSTS_FILE.open("w", encoding="utf-8") as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)
            return redirect(url_for("show_thread", thread_name=thread_name), code=303)

    return render_template("input_error.html", message="選択した投稿が見つかりません。"), 404

@app.route("/new-thread", methods=["GET", "POST"])
def new_thread():
    if request.method == "POST":
        thread_name = request.form.get("thread_name", "").strip()
        if not thread_name:
            return render_template("input_error.html", message="スレッド名を入力してください。"), 400
        if "/" in thread_name:
            return render_template("input_error.html", message="スレッド名に / は使えません。"), 400

        threads = load_threads()
        for thread in threads:
            if thread["name"] == thread_name:
                return render_template("input_error.html", message="同じ名前のスレッドが既にあります。"), 400

        threads.append({"id": str(uuid4()), "name": thread_name})
        with THREADS_FILE.open("w", encoding="utf-8") as f:
            json.dump(threads, f, ensure_ascii=False, indent=2)
        return redirect(url_for("index"), code=303)

    return render_template("new_thread.html")
@app.route("/delete-thread")
def select_thread_delete():
    threads = load_threads()
    return render_template("delete_thread.html", threads=threads)
@app.route("/delete-thread/confirm", methods=["POST"])
def confirm_thread_delete():
    threads = load_threads()
    if len(threads) <= 1:
        return render_template("input_error.html", message="最後の1件のスレッドは削除できません。"), 400

    thread_id = request.form.get("thread_id")
    if not thread_id:
        return render_template("input_error.html", message="削除するスレッドを選択してください。"), 400

    for thread in threads:
        if thread["id"] == thread_id:
            posts = []
            if POSTS_FILE.exists():
                with POSTS_FILE.open("r", encoding="utf-8") as f:
                    posts = json.load(f)

            post_count = 0
            for post in posts:
                if post["thread_name"] == thread["name"]:
                    post_count += 1

            return render_template(
                "delete_thread_confirm.html",
                thread=thread,
                post_count=post_count
            )

    return render_template("input_error.html", message="選択したスレッドが見つかりません。"), 404
@app.route("/delete-thread/execute", methods=["POST"])
def execute_thread_delete():
    threads = load_threads()
    if len(threads) <= 1:
        return render_template("input_error.html", message="最後の1件のスレッドは削除できません。"), 400

    thread_id = request.form.get("thread_id")
    if not thread_id:
        return render_template("input_error.html", message="削除するスレッドを選択してください。"), 400

    for thread in threads:
        if thread["id"] == thread_id:
            posts = []
            if POSTS_FILE.exists():
                with POSTS_FILE.open("r", encoding="utf-8") as f:
                    posts = json.load(f)

            remaining_posts = []
            for post in posts:
                if post["thread_name"] != thread["name"]:
                    remaining_posts.append(post)

            threads.remove(thread)
            with POSTS_FILE.open("w", encoding="utf-8") as f:
                json.dump(remaining_posts, f, ensure_ascii=False, indent=2)
            with THREADS_FILE.open("w", encoding="utf-8") as f:
                json.dump(threads, f, ensure_ascii=False, indent=2)
            return redirect(url_for("index"), code=303)

    return render_template("input_error.html", message="選択したスレッドが見つかりません。"), 404

if __name__ == "__main__":
    app.run(debug=True)
