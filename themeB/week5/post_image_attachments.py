"""添付画像の入力確認・保存・不要になった画像の削除を扱う。"""

from pathlib import Path
from uuid import uuid4

from flask import current_app

MAXIMUM_ATTACHED_IMAGE_COUNT = 4
MAXIMUM_IMAGE_FILE_SIZE_BYTES = 5_000_000
ALLOWED_IMAGE_FILE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SAVED_IMAGE_FILE_NAME_HEXADECIMAL_LENGTH = 32


def get_selected_image_files(uploaded_files):
    """ファイル未選択時に送信される、名前が空の項目を取り除く。"""
    return [image_file for image_file in uploaded_files if image_file.filename]


def validate_selected_image_files(selected_image_files):
    if len(selected_image_files) > MAXIMUM_ATTACHED_IMAGE_COUNT:
        return "画像は4枚まで選択できます。"

    for selected_image_file in selected_image_files:
        file_extension = Path(selected_image_file.filename).suffix.lower()
        if file_extension not in ALLOWED_IMAGE_FILE_EXTENSIONS:
            return "画像はJPGまたはPNGを選択してください。"

        selected_image_file.stream.seek(0, 2)
        image_file_size_bytes = selected_image_file.stream.tell()
        selected_image_file.stream.seek(0)
        if image_file_size_bytes > MAXIMUM_IMAGE_FILE_SIZE_BYTES:
            return "画像は1枚あたり5MBまでです。"
    return None


def get_uploaded_images_directory():
    return Path(current_app.config["UPLOADED_IMAGES_DIRECTORY"])


def save_selected_image_files(selected_image_files):
    saved_image_file_names = []
    for selected_image_file in selected_image_files:
        file_extension = Path(selected_image_file.filename).suffix.lower()
        saved_image_file_name = f"{uuid4().hex}{file_extension}"
        selected_image_file.save(get_uploaded_images_directory() / saved_image_file_name)
        saved_image_file_names.append(saved_image_file_name)
    return saved_image_file_names


def is_generated_image_file_name(image_file_name):
    if not isinstance(image_file_name, str):
        return False

    image_file_path = Path(image_file_name)
    return (
        image_file_path.name == image_file_name
        and image_file_path.suffix in ALLOWED_IMAGE_FILE_EXTENSIONS
        and len(image_file_path.stem) == SAVED_IMAGE_FILE_NAME_HEXADECIMAL_LENGTH
        and all(character in "0123456789abcdef" for character in image_file_path.stem)
    )


def are_saved_image_files_available(saved_image_file_names):
    """差し替え確認後の画像名が正しく、保存先に実在するか確かめる。"""
    if not 1 <= len(saved_image_file_names) <= MAXIMUM_ATTACHED_IMAGE_COUNT:
        return False

    for saved_image_file_name in saved_image_file_names:
        if not is_generated_image_file_name(saved_image_file_name):
            return False
        if not (get_uploaded_images_directory() / saved_image_file_name).is_file():
            return False
    return True


def delete_images_no_longer_referenced(candidate_image_file_names, remaining_posts):
    """保存成功後に呼び出し、対象画像のうち全投稿で未使用のものだけ削除する。"""
    if not isinstance(candidate_image_file_names, list) or not isinstance(remaining_posts, list):
        return 0

    referenced_image_file_names = set()
    for remaining_post in remaining_posts:
        if not isinstance(remaining_post, dict):
            return 0
        post_image_file_names = remaining_post.get("image_names", [])
        if (
            not isinstance(post_image_file_names, list)
            or any(not isinstance(image_file_name, str) for image_file_name in post_image_file_names)
        ):
            current_app.logger.warning("画像の使用状況を確認できないため、画像の削除を見送りました。")
            return 0
        referenced_image_file_names.update(post_image_file_names)

    deleted_image_count = 0
    for candidate_image_file_name in candidate_image_file_names:
        if (
            not is_generated_image_file_name(candidate_image_file_name)
            or candidate_image_file_name in referenced_image_file_names
        ):
            continue
        try:
            uploaded_images_directory = get_uploaded_images_directory().absolute()
            # 別の場所へのリンクなら、誤ってその先の画像を消さない。
            if uploaded_images_directory.resolve() != uploaded_images_directory:
                continue
            candidate_image_path = uploaded_images_directory / candidate_image_file_name
            if (
                candidate_image_path.is_symlink()
                or candidate_image_path.resolve().parent != uploaded_images_directory
            ):
                continue
            if candidate_image_path.is_file():
                candidate_image_path.unlink()
                deleted_image_count += 1
        except OSError:
            current_app.logger.warning("画像ファイルを削除できませんでした: %s", candidate_image_file_name)
    return deleted_image_count
