"""自分レビューの起動入口。URLごとに入力・確認・保存・表示をつなぐ。"""

from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from flask import Flask, redirect, render_template, request, url_for

from daily_rating_statistics import calculate_daily_rating_statistics
from json_data_storage import (
    find_saved_post_in_thread,
    find_saved_thread_by_name,
    load_saved_posts,
    load_saved_threads,
    save_posts,
    save_threads,
)
from post_image_attachments import (
    are_saved_image_files_available,
    delete_images_no_longer_referenced,
    get_selected_image_files,
    save_selected_image_files,
    validate_selected_image_files,
)

APPLICATION_DIRECTORY = Path(__file__).resolve().parent
POST_CREATED_AT_FORMAT = "%Y-%m-%d %H:%M:%S"
POST_EDIT_TIME_LIMIT = timedelta(hours=2)
ALLOWED_STAR_RATING_VALUES = {"1", "2", "3", "4", "5"}

app = Flask(__name__)
app.config.update(
    THREADS_DATA_FILE=APPLICATION_DIRECTORY / "threads.json",
    POSTS_DATA_FILE=APPLICATION_DIRECTORY / "posts.json",
    UPLOADED_IMAGES_DIRECTORY=APPLICATION_DIRECTORY / "static" / "uploads",
)
app.config["UPLOADED_IMAGES_DIRECTORY"].mkdir(exist_ok=True)


def render_input_error_page(message, status_code=400):
    return render_template("input_error.html", message=message), status_code


def read_submitted_post_fields():
    star_rating = request.form.get("rating")
    post_heading = request.form.get("headtext", "").strip()
    post_content = request.form.get("bodytext", "").strip()
    return star_rating, post_heading, post_content


def is_post_editable_within_time_limit(saved_post):
    post_created_at = datetime.strptime(saved_post["created_at"], POST_CREATED_AT_FORMAT)
    elapsed_time_since_creation = datetime.now() - post_created_at
    return timedelta(0) <= elapsed_time_since_creation <= POST_EDIT_TIME_LIMIT


# endpoint名は既存のurl_forと互換にし、関数名で処理の役割を説明する。
@app.route("/", endpoint="index")
def show_thread_list_and_rating_statistics():
    saved_threads = load_saved_threads()
    saved_posts = load_saved_posts()
    rating_statistics = calculate_daily_rating_statistics(saved_posts, date.today())
    return render_template("thread_list.html", threads=saved_threads, **rating_statistics)


@app.route("/threads/<thread_name>", methods=["GET", "POST"], endpoint="show_thread")
def show_thread_posts_or_save_new_post(thread_name):
    if find_saved_thread_by_name(thread_name) is None:
        return render_input_error_page("スレッドが見つかりません。", 404)
    saved_posts = load_saved_posts()

    if request.method == "POST":
        star_rating, post_heading, post_content = read_submitted_post_fields()
        attached_image_file_names = request.form.getlist("image_names")
        if not star_rating:
            return render_input_error_page("星評価を選択してください。")
        if not post_heading:
            return render_input_error_page("見出しを入力してください。")

        saved_posts.append({
            "id": str(uuid4()),
            "thread_name": thread_name,
            "created_at": datetime.now().strftime(POST_CREATED_AT_FORMAT),
            "rating": star_rating,
            "headtext": post_heading,
            "bodytext": post_content,
            "image_names": attached_image_file_names,
        })
        save_posts(saved_posts)
        return redirect(url_for("show_thread", thread_name=thread_name), code=303)

    posts_in_selected_thread = [
        saved_post for saved_post in saved_posts
        if saved_post["thread_name"] == thread_name
    ]
    return render_template(
        "thread_posts.html",
        thread_name=thread_name,
        rating=None,
        headtext=None,
        bodytext=None,
        thread_posts=posts_in_selected_thread,
    )


@app.route("/threads/<thread_name>/new", endpoint="new_post")
def show_new_post_form(thread_name):
    if find_saved_thread_by_name(thread_name) is None:
        return render_input_error_page("スレッドが見つかりません。", 404)
    return render_template("new_post_form.html", thread_name=thread_name)


@app.route("/threads/<thread_name>/confirm", methods=["POST"], endpoint="confirm_post")
def confirm_new_post_and_save_attached_images(thread_name):
    if find_saved_thread_by_name(thread_name) is None:
        return render_input_error_page("スレッドが見つかりません。", 404)

    star_rating, post_heading, post_content = read_submitted_post_fields()
    selected_image_files = get_selected_image_files(request.files.getlist("images"))
    image_validation_error = validate_selected_image_files(selected_image_files)
    if image_validation_error:
        return render_input_error_page(image_validation_error)
    if not star_rating:
        return render_input_error_page("星評価を選択してください。")
    if not post_heading:
        return render_input_error_page("見出しを入力してください。")

    # 投稿の最終保存まで画像名を引き継ぐため、確認画面へ進む時点で保存する。
    saved_image_file_names = save_selected_image_files(selected_image_files)
    return render_template(
        "new_post_confirmation.html",
        thread_name=thread_name,
        rating=star_rating,
        headtext=post_heading,
        bodytext=post_content,
        image_names=saved_image_file_names,
    )


@app.route("/threads/<thread_name>/delete", endpoint="select_delete")
def show_post_deletion_selection(thread_name):
    posts_in_selected_thread = [
        saved_post for saved_post in load_saved_posts()
        if saved_post["thread_name"] == thread_name
    ]
    return render_template(
        "post_delete_selection.html", thread_name=thread_name, thread_posts=posts_in_selected_thread
    )


@app.route("/threads/<thread_name>/edit", endpoint="select_edit")
def show_editable_post_selection(thread_name):
    editable_posts_in_thread = [
        saved_post for saved_post in load_saved_posts()
        if saved_post["thread_name"] == thread_name and is_post_editable_within_time_limit(saved_post)
    ]
    return render_template(
        "post_edit_selection.html", thread_name=thread_name, thread_posts=editable_posts_in_thread
    )


@app.route("/threads/<thread_name>/edit/input", methods=["GET", "POST"], endpoint="edit_post")
def show_post_edit_form_or_confirm_changes(thread_name):
    if find_saved_thread_by_name(thread_name) is None:
        return render_input_error_page("スレッドが見つかりません。", 404)
    requested_post_id = (
        request.form.get("post_id") if request.method == "POST" else request.args.get("post_id")
    )
    if not requested_post_id:
        return render_input_error_page("編集する投稿を選択してください。")

    selected_post = find_saved_post_in_thread(load_saved_posts(), requested_post_id, thread_name)
    if selected_post is None:
        return render_input_error_page("投稿が見つかりません。", 404)
    if not is_post_editable_within_time_limit(selected_post):
        return render_input_error_page("編集できる時間を過ぎています。")
    if request.method != "POST":
        return render_template("post_edit_form.html", thread_name=thread_name, post=selected_post)

    star_rating, post_heading, post_content = read_submitted_post_fields()
    if star_rating not in ALLOWED_STAR_RATING_VALUES or not post_heading:
        return render_input_error_page("星評価と見出しを入力してください。")
    selected_image_files = get_selected_image_files(request.files.getlist("images"))
    image_validation_error = validate_selected_image_files(selected_image_files)
    if image_validation_error:
        return render_input_error_page(image_validation_error)

    should_replace_images = bool(selected_image_files)
    confirmed_image_file_names = (
        save_selected_image_files(selected_image_files)
        if should_replace_images
        else selected_post.get("image_names", [])
    )
    return render_template(
        "post_edit_confirmation.html",
        thread_name=thread_name,
        post_id=selected_post["id"],
        rating=star_rating,
        headtext=post_heading,
        bodytext=post_content,
        image_names=confirmed_image_file_names,
        replace_images=should_replace_images,
    )


@app.route("/threads/<thread_name>/edit/execute", methods=["POST"], endpoint="execute_edit")
def save_confirmed_post_changes(thread_name):
    if find_saved_thread_by_name(thread_name) is None:
        return render_input_error_page("スレッドが見つかりません。", 404)
    requested_post_id = request.form.get("post_id")
    if not requested_post_id:
        return render_input_error_page("編集する投稿を選択してください。")
    star_rating, post_heading, post_content = read_submitted_post_fields()
    if star_rating not in ALLOWED_STAR_RATING_VALUES or not post_heading:
        return render_input_error_page("星評価と見出しを入力してください。")

    saved_posts = load_saved_posts()
    selected_post = find_saved_post_in_thread(saved_posts, requested_post_id, thread_name)
    if selected_post is None:
        return render_input_error_page("選択した投稿が見つかりません。", 404)
    if not is_post_editable_within_time_limit(selected_post):
        return render_input_error_page("編集できる時間を過ぎています。")

    image_replacement_flag = request.form.get("replace_images", "0")
    if image_replacement_flag not in {"0", "1"}:
        return render_input_error_page("画像の変更内容を確認してください。")
    should_replace_images = image_replacement_flag == "1"
    if should_replace_images:
        confirmed_image_file_names = request.form.getlist("image_names")
        if not are_saved_image_files_available(confirmed_image_file_names):
            return render_input_error_page("画像を選び直して、変更内容を確認してください。")

    previous_image_file_names = selected_post.get("image_names", [])
    selected_post["rating"] = star_rating
    selected_post["headtext"] = post_heading
    selected_post["bodytext"] = post_content
    # 画像未選択時は、フォームの画像名で上書きせず保存済みの画像を保持する。
    if should_replace_images:
        selected_post["image_names"] = confirmed_image_file_names
    save_posts(saved_posts)
    if should_replace_images:
        delete_images_no_longer_referenced(previous_image_file_names, saved_posts)
    return redirect(url_for("show_thread", thread_name=thread_name), code=303)


@app.route("/threads/<thread_name>/delete/confirm", methods=["POST"], endpoint="confirm_delete")
def confirm_selected_post_deletion(thread_name):
    requested_post_id = request.form.get("post_id")
    if not requested_post_id:
        return render_input_error_page("削除する投稿を選択してください。")
    selected_post = find_saved_post_in_thread(load_saved_posts(), requested_post_id, thread_name)
    if selected_post is None:
        return render_input_error_page("選択した投稿が見つかりません。", 404)
    return render_template("post_delete_confirmation.html", thread_name=thread_name, post=selected_post)


@app.route("/threads/<thread_name>/delete/execute", methods=["POST"], endpoint="execute_delete")
def delete_confirmed_post(thread_name):
    requested_post_id = request.form.get("post_id")
    if not requested_post_id:
        return render_input_error_page("削除する投稿を選択してください。")
    saved_posts = load_saved_posts()
    selected_post = find_saved_post_in_thread(saved_posts, requested_post_id, thread_name)
    if selected_post is None:
        return render_input_error_page("選択した投稿が見つかりません。", 404)

    candidate_image_file_names = selected_post.get("image_names", [])
    saved_posts.remove(selected_post)
    save_posts(saved_posts)
    delete_images_no_longer_referenced(candidate_image_file_names, saved_posts)
    return redirect(url_for("show_thread", thread_name=thread_name), code=303)


@app.route("/new-thread", methods=["GET", "POST"], endpoint="new_thread")
def show_new_thread_form_or_save_thread():
    if request.method != "POST":
        return render_template("new_thread_form.html")

    requested_thread_name = request.form.get("thread_name", "").strip()
    if not requested_thread_name:
        return render_input_error_page("スレッド名を入力してください。")
    if "/" in requested_thread_name:
        return render_input_error_page("スレッド名に / は使えません。")

    saved_threads = load_saved_threads()
    if any(saved_thread["name"] == requested_thread_name for saved_thread in saved_threads):
        return render_input_error_page("同じ名前のスレッドが既にあります。")
    saved_threads.append({"id": str(uuid4()), "name": requested_thread_name})
    save_threads(saved_threads)
    return redirect(url_for("index"), code=303)


@app.route("/delete-thread", endpoint="select_thread_delete")
def show_thread_deletion_selection():
    return render_template("thread_delete_selection.html", threads=load_saved_threads())


@app.route("/delete-thread/confirm", methods=["POST"], endpoint="confirm_thread_delete")
def confirm_selected_thread_deletion():
    saved_threads = load_saved_threads()
    if len(saved_threads) <= 1:
        return render_input_error_page("最後の1件のスレッドは削除できません。")
    requested_thread_id = request.form.get("thread_id")
    if not requested_thread_id:
        return render_input_error_page("削除するスレッドを選択してください。")

    for selected_thread in saved_threads:
        if selected_thread["id"] == requested_thread_id:
            posts_in_selected_thread_count = sum(
                saved_post["thread_name"] == selected_thread["name"] for saved_post in load_saved_posts()
            )
            return render_template(
                "thread_delete_confirmation.html",
                thread=selected_thread,
                post_count=posts_in_selected_thread_count,
            )
    return render_input_error_page("選択したスレッドが見つかりません。", 404)


@app.route("/delete-thread/execute", methods=["POST"], endpoint="execute_thread_delete")
def delete_confirmed_thread_and_its_posts():
    saved_threads = load_saved_threads()
    if len(saved_threads) <= 1:
        return render_input_error_page("最後の1件のスレッドは削除できません。")
    requested_thread_id = request.form.get("thread_id")
    if not requested_thread_id:
        return render_input_error_page("削除するスレッドを選択してください。")

    for selected_thread in saved_threads:
        if selected_thread["id"] != requested_thread_id:
            continue
        posts_to_keep = []
        candidate_image_file_names = []
        for saved_post in load_saved_posts():
            if saved_post["thread_name"] != selected_thread["name"]:
                posts_to_keep.append(saved_post)
            elif isinstance(saved_post.get("image_names", []), list):
                candidate_image_file_names.extend(saved_post.get("image_names", []))

        saved_threads.remove(selected_thread)
        # 両方のJSONを保存し終えてから、削除した投稿の画像を整理する。
        save_posts(posts_to_keep)
        save_threads(saved_threads)
        delete_images_no_longer_referenced(candidate_image_file_names, posts_to_keep)
        return redirect(url_for("index"), code=303)
    return render_input_error_page("選択したスレッドが見つかりません。", 404)


if __name__ == "__main__":
    app.run(debug=True)
