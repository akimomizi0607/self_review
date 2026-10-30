"""Check existing observable behavior without opening or modifying real user data.

Usage: python test_application_regression.py [--app-dir PATH_TO_WEEK5]
The default application directory is the parent of this script's tests directory.
Only Python source, HTML templates, styles, and scripts are copied to a temporary
directory. Every JSON record and uploaded image used here is a synthetic fixture.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timedelta
import importlib.util
from io import BytesIO, StringIO
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from flask import template_rendered


APPLICATION_DIRECTORY: Path
REFERENCE_TIME = datetime.now().replace(microsecond=0)


def copy_application_source(source_directory: Path, target_directory: Path) -> None:
    """Exclude JSON data, uploaded media, and generated cache directories."""
    target_directory.mkdir(parents=True)
    for source_file in source_directory.glob("*.py"):
        shutil.copyfile(source_file, target_directory / source_file.name)
    for directory_name, extensions in (
        ("templates", {".html"}),
        ("static", {".css", ".js"}),
    ):
        original_directory = source_directory / directory_name
        if not original_directory.exists():
            continue
        # Deliberately do not walk uploads, even to inspect file metadata.
        pending_directories = [original_directory]
        while pending_directories:
            current_directory = pending_directories.pop()
            for child in current_directory.iterdir():
                if child.is_dir():
                    if child.name != "uploads":
                        pending_directories.append(child)
                elif child.suffix in extensions:
                    destination = target_directory / child.relative_to(source_directory)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(child, destination)
    (target_directory / "static" / "uploads").mkdir(parents=True, exist_ok=True)


@contextmanager
def captured_templates(application):
    rendered = []

    def collect(sender, template, context, **extra):
        rendered.append((template.name, context))

    template_rendered.connect(collect, application)
    try:
        yield rendered
    finally:
        template_rendered.disconnect(collect, application)


class ApplicationRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="self-review-regression-")
        cls.application_directory = Path(cls.workspace.name) / "application"
        copy_application_source(APPLICATION_DIRECTORY, cls.application_directory)
        cls.module_name = f"self_review_regression_{uuid4().hex}"
        specification = importlib.util.spec_from_file_location(
            cls.module_name, cls.application_directory / "app.py"
        )
        cls.module = importlib.util.module_from_spec(specification)
        sys.modules[cls.module_name] = cls.module
        sys.path.insert(0, str(cls.application_directory))
        specification.loader.exec_module(cls.module)
        cls.application = cls.module.app
        cls.application.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(str(cls.application_directory))
        sys.modules.pop(cls.module_name, None)
        cls.workspace.cleanup()

    def setUp(self):
        self.fixture_directory = Path(tempfile.mkdtemp(dir=self.workspace.name))
        self.threads_file = self.fixture_directory / "threads.json"
        self.posts_file = self.fixture_directory / "posts.json"
        self.upload_directory = self.fixture_directory / "uploads"
        self.upload_directory.mkdir()
        self.application.config.update(
            THREADS_DATA_FILE=self.threads_file,
            POSTS_DATA_FILE=self.posts_file,
            UPLOADED_IMAGES_DIRECTORY=self.upload_directory,
        )
        # Original code reads globals; refactored code reads app.config at request
        # time. Setting both makes one suite compare the two implementations.
        for original_name, isolated_path in (
            ("THREADS_FILE", self.threads_file),
            ("POSTS_FILE", self.posts_file),
            ("UPLOAD_FOLDER", self.upload_directory),
        ):
            if hasattr(self.module, original_name):
                setattr(self.module, original_name, isolated_path)
        self.write_threads([
            {"id": "thread-one", "name": "日記"},
            {"id": "thread-two", "name": "散歩"},
        ])
        self.write_posts([])
        self.client = self.application.test_client()

    def tearDown(self):
        shutil.rmtree(self.fixture_directory)

    def write_threads(self, threads):
        self.threads_file.write_text(json.dumps(threads, ensure_ascii=False), encoding="utf-8")

    def write_posts(self, posts):
        self.posts_file.write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")

    def posts(self):
        return json.loads(self.posts_file.read_text(encoding="utf-8"))

    def new_fixture_post(self, identifier="post-one", **overrides):
        post = {
            "id": identifier,
            "thread_name": "日記",
            "created_at": (REFERENCE_TIME - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
            "rating": "3",
            "headtext": "テストの思い出",
            "bodytext": "これは隔離したテスト投稿です。",
            "image_names": [],
        }
        post.update(overrides)
        return post

    def write_fixture_image(self, digit="a"):
        image_name = digit * 32 + ".png"
        (self.upload_directory / image_name).write_bytes(b"synthetic fixture image")
        return image_name

    def request_with_context(self, method, url, **options):
        with captured_templates(self.application) as templates:
            response = self.client.open(url, method=method, **options)
        self.assertTrue(templates, response.get_data(as_text=True))
        return response, templates[-1][1]

    def assert_error(self, response, status=400, message=None):
        self.assertEqual(response.status_code, status)
        if message:
            self.assertIn(message, response.get_data(as_text=True))

    def edit_fields(self, **overrides):
        fields = {
            "post_id": "post-one", "rating": "4", "headtext": " 更新した見出し ",
            "bodytext": " 更新した本文 ", "replace_images": "0",
        }
        fields.update(overrides)
        return fields

    def test_get_pages_keep_existing_urls_and_form_fields(self):
        self.write_posts([self.new_fixture_post()])
        for url in (
            "/", "/new-thread", "/delete-thread", "/threads/日記",
            "/threads/日記/new", "/threads/日記/delete", "/threads/日記/edit",
            "/threads/日記/edit/input?post_id=post-one",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        create_form = self.client.get("/threads/日記/new").get_data(as_text=True)
        for field_name in ("rating", "headtext", "bodytext", "images"):
            self.assertIn(f'name="{field_name}"', create_form)

    def test_head_new_thread_displays_form_without_creating_a_thread(self):
        original_threads = self.threads_file.read_bytes()
        response, _ = self.request_with_context(
            "HEAD", "/new-thread", data={"thread_name": "保存されてはいけないスレッド"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")
        self.assertEqual(self.threads_file.read_bytes(), original_threads)
        self.assertEqual(self.posts(), [])
        self.assertEqual(list(self.upload_directory.iterdir()), [])

    def test_head_edit_displays_original_form_without_saving_data_or_images(self):
        original = self.new_fixture_post()
        self.write_posts([original])
        response, context = self.request_with_context(
            "HEAD", "/threads/日記/edit/input?post_id=post-one",
            data=self.edit_fields(images=[(BytesIO(b"must not be saved"), "unexpected.png")]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")
        self.assertEqual(context["post"], original)
        self.assertEqual(self.posts(), [original])
        self.assertEqual(list(self.upload_directory.iterdir()), [])

    def test_new_thread_validation_and_json_keys(self):
        for invalid_name in ("", "   ", "a/b", "日記"):
            with self.subTest(name=invalid_name):
                self.assert_error(self.client.post("/new-thread", data={"thread_name": invalid_name}))
        response = self.client.post("/new-thread", data={"thread_name": "  新しい記録  "})
        self.assertEqual(response.status_code, 303)
        thread = json.loads(self.threads_file.read_text(encoding="utf-8"))[-1]
        self.assertEqual(set(thread), {"id", "name"})
        self.assertEqual(thread["name"], "新しい記録")

    def test_missing_thread_and_missing_post_errors(self):
        for url in ("/threads/なし", "/threads/なし/new", "/threads/なし/edit/input"):
            with self.subTest(url=url):
                self.assert_error(self.client.get(url), 404)
        self.assert_error(self.client.post("/threads/なし/confirm"), 404)
        self.assert_error(self.client.get("/threads/日記/edit/input"), 400)
        self.assert_error(self.client.get("/threads/日記/edit/input?post_id=missing"), 404)
        self.assert_error(self.client.post("/threads/日記/delete/execute", data={"post_id": "missing"}), 404)

    def test_new_post_confirmation_and_persistence(self):
        response, context = self.request_with_context(
            "POST", "/threads/日記/confirm",
            data={"rating": "4", "headtext": "  ピクニック  ", "bodytext": "  晴れた日に散歩  ",
                  "images": [(BytesIO(b"fake-png"), "walk.PNG")]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["headtext"], "ピクニック")
        self.assertEqual(context["bodytext"], "晴れた日に散歩")
        self.assertEqual(self.posts(), [])
        saved_images = context["image_names"]
        self.assertEqual(len(saved_images), 1)
        self.assertTrue((self.upload_directory / saved_images[0]).exists())
        self.assertTrue(saved_images[0].endswith(".png"))
        response = self.client.post("/threads/日記", data={
            "rating": "4", "headtext": "  ピクニック  ", "bodytext": "  晴れた日に散歩  ",
            "image_names": saved_images,
        })
        self.assertEqual(response.status_code, 303)
        post = self.posts()[0]
        self.assertEqual(set(post), {"id", "thread_name", "created_at", "rating", "headtext", "bodytext", "image_names"})
        self.assertEqual(post["thread_name"], "日記")
        self.assertEqual(post["rating"], "4")
        self.assertEqual(post["headtext"], "ピクニック")
        self.assertEqual(post["bodytext"], "晴れた日に散歩")
        self.assertEqual(post["image_names"], saved_images)
        datetime.strptime(post["created_at"], "%Y-%m-%d %H:%M:%S")

    def test_new_post_required_fields_and_optional_body_and_images(self):
        for fields in ({"headtext": "見出し"}, {"rating": "3"}, {"rating": "3", "headtext": "  "}):
            for url in ("/threads/日記/confirm", "/threads/日記"):
                with self.subTest(url=url, fields=fields):
                    self.assert_error(self.client.post(url, data=fields))
        response = self.client.post("/threads/日記", data={"rating": "3", "headtext": "本文なし"})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.posts()[0]["bodytext"], "")
        self.assertEqual(self.posts()[0]["image_names"], [])

    def test_upload_accepts_four_images_and_exact_size_limit(self):
        response = self.client.post("/threads/日記/confirm", data={
            "rating": "3", "headtext": "最大枚数",
            "images": [(BytesIO(b"x" * 5_000_000), "a.jpg"),
                       (BytesIO(b"x"), "b.jpeg"), (BytesIO(b"x"), "c.png"), (BytesIO(b"x"), "d.JPG")],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list(self.upload_directory.iterdir())), 4)

    def test_upload_rejects_too_many_invalid_type_and_oversized_images(self):
        image_batches = (
            [(BytesIO(b"x"), f"image-{index}.png") for index in range(5)],
            [(BytesIO(b"x"), "image.gif")],
            [(BytesIO(b"x" * 5_000_001), "image.png")],
        )
        for images in image_batches:
            with self.subTest(filenames=[name for _, name in images]):
                response = self.client.post("/threads/日記/confirm", data={
                    "rating": "3", "headtext": "画像テスト", "images": images,
                })
                self.assert_error(response)
                self.assertEqual(list(self.upload_directory.iterdir()), [])

    def test_thread_listing_filters_other_threads(self):
        self.write_posts([self.new_fixture_post(), self.new_fixture_post("other", thread_name="散歩")])
        response, context = self.request_with_context("GET", "/threads/日記")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([post["id"] for post in context["thread_posts"]], ["post-one"])

    def test_edit_window_rejects_future_and_expired_posts(self):
        for offset in (timedelta(hours=-3), timedelta(hours=1)):
            created_at = (REFERENCE_TIME + offset).strftime("%Y-%m-%d %H:%M:%S")
            self.write_posts([self.new_fixture_post(created_at=created_at)])
            with self.subTest(offset=offset):
                self.assert_error(self.client.get("/threads/日記/edit/input?post_id=post-one"))
                self.assert_error(self.client.post("/threads/日記/edit/execute", data=self.edit_fields()))
                _, context = self.request_with_context("GET", "/threads/日記/edit")
                self.assertEqual(context["thread_posts"], [])

    def test_edit_window_includes_exactly_two_hours_and_excludes_one_second_later(self):
        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return REFERENCE_TIME

        with patch.object(self.module, "datetime", FrozenDateTime):
            for elapsed, expected_status in (
                (timedelta(0), 200), (timedelta(hours=2), 200),
                (timedelta(hours=2, seconds=1), 400), (timedelta(seconds=-1), 400),
            ):
                self.write_posts([self.new_fixture_post(
                    created_at=(REFERENCE_TIME - elapsed).strftime("%Y-%m-%d %H:%M:%S")
                )])
                with self.subTest(elapsed=elapsed):
                    response = self.client.get("/threads/日記/edit/input?post_id=post-one")
                    self.assertEqual(response.status_code, expected_status)

    def test_edit_confirmation_and_text_update_preserve_identity_and_images(self):
        original_image = self.write_fixture_image()
        original = self.new_fixture_post(image_names=[original_image])
        self.write_posts([original])
        response, context = self.request_with_context(
            "POST", "/threads/日記/edit/input", data=self.edit_fields()
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(context["replace_images"])
        self.assertEqual(context["image_names"], [original_image])
        self.assertEqual(self.posts(), [original])
        response = self.client.post("/threads/日記/edit/execute", data=self.edit_fields(image_names=["untrusted.png"]))
        self.assertEqual(response.status_code, 303)
        updated = self.posts()[0]
        for key in ("id", "thread_name", "created_at", "image_names"):
            self.assertEqual(updated[key], original[key])
        self.assertEqual(updated["headtext"], "更新した見出し")
        self.assertEqual(updated["bodytext"], "更新した本文")
        self.assertTrue((self.upload_directory / original_image).exists())

    def test_edit_rejects_rating_outside_one_to_five_and_missing_headline(self):
        original = self.new_fixture_post()
        self.write_posts([original])
        for fields in ({"rating": "0"}, {"rating": "6"}, {"rating": "x"}, {"headtext": " "}):
            for url in ("/threads/日記/edit/input", "/threads/日記/edit/execute"):
                with self.subTest(url=url, fields=fields):
                    self.assert_error(self.client.post(url, data=self.edit_fields(**fields)))
                    self.assertEqual(self.posts(), [original])

    def test_edit_upload_reuses_new_post_image_constraints(self):
        original = self.new_fixture_post()
        self.write_posts([original])
        for image_count, filename, byte_count in (
            (5, "image.png", 1), (1, "image.gif", 1), (1, "image.png", 5_000_001),
        ):
            with self.subTest(image_count=image_count, filename=filename, byte_count=byte_count):
                response = self.client.post("/threads/日記/edit/input", data=self.edit_fields(
                    images=[(BytesIO(b"x" * byte_count), filename) for _ in range(image_count)]
                ))
                self.assert_error(response)
                self.assertEqual(self.posts(), [original])
                self.assertEqual(list(self.upload_directory.iterdir()), [])

    def test_edit_image_replacement_deletes_only_unshared_old_images(self):
        old_image = self.write_fixture_image("a")
        shared_image = self.write_fixture_image("b")
        unrelated_image = self.write_fixture_image("d")
        original_posts = [
            self.new_fixture_post(image_names=[old_image, shared_image]),
            self.new_fixture_post("other", thread_name="散歩", image_names=[shared_image]),
        ]
        self.write_posts(original_posts)
        response, context = self.request_with_context(
            "POST", "/threads/日記/edit/input",
            data=self.edit_fields(images=[(BytesIO(b"new fake image"), "replacement.png")]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(context["replace_images"])
        self.assertEqual(len(context["image_names"]), 1)
        replacement_image = context["image_names"][0]
        self.assertTrue((self.upload_directory / replacement_image).exists())
        self.assertEqual(self.posts(), original_posts)
        response = self.client.post("/threads/日記/edit/execute", data=self.edit_fields(
            replace_images="1", image_names=[replacement_image],
        ))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.posts()[0]["image_names"], [replacement_image])
        self.assertFalse((self.upload_directory / old_image).exists())
        for retained in (shared_image, replacement_image, unrelated_image):
            self.assertTrue((self.upload_directory / retained).exists())

    def test_edit_replacement_requires_existing_safe_image_names(self):
        self.write_posts([self.new_fixture_post()])
        for image_names in ([], ["../escape.png"], ["a" * 32 + ".png"], ["bad.png"], ["a" * 32 + ".gif"]):
            with self.subTest(image_names=image_names):
                self.assert_error(self.client.post("/threads/日記/edit/execute", data=self.edit_fields(
                    replace_images="1", image_names=image_names,
                )))
        self.assert_error(self.client.post("/threads/日記/edit/execute", data=self.edit_fields(replace_images="yes")))

    def test_delete_post_preserves_shared_and_unrelated_images(self):
        old_image = self.write_fixture_image("a")
        shared_image = self.write_fixture_image("b")
        unrelated_image = self.write_fixture_image("c")
        self.write_posts([
            self.new_fixture_post(image_names=[old_image, shared_image]),
            self.new_fixture_post("other", thread_name="散歩", image_names=[shared_image]),
        ])
        self.assertEqual(self.client.post("/threads/日記/delete/confirm", data={"post_id": "post-one"}).status_code, 200)
        response = self.client.post("/threads/日記/delete/execute", data={"post_id": "post-one"})
        self.assertEqual(response.status_code, 303)
        self.assertEqual([post["id"] for post in self.posts()], ["other"])
        self.assertFalse((self.upload_directory / old_image).exists())
        self.assertTrue((self.upload_directory / shared_image).exists())
        self.assertTrue((self.upload_directory / unrelated_image).exists())

    def test_delete_avoids_images_when_remaining_references_are_malformed(self):
        candidate_image = self.write_fixture_image()
        for malformed_references in ("not a list", [123]):
            self.write_posts([
                self.new_fixture_post(image_names=[candidate_image]),
                self.new_fixture_post("other", thread_name="散歩", image_names=malformed_references),
            ])
            with self.subTest(references=malformed_references):
                response = self.client.post("/threads/日記/delete/execute", data={"post_id": "post-one"})
                self.assertEqual(response.status_code, 303)
                self.assertTrue((self.upload_directory / candidate_image).exists())

    def test_delete_does_not_follow_unsafe_image_paths(self):
        outside_image = self.fixture_directory / "outside.png"
        outside_image.write_bytes(b"not an uploaded image")
        self.write_posts([self.new_fixture_post(image_names=["../outside.png"])])
        response = self.client.post("/threads/日記/delete/execute", data={"post_id": "post-one"})
        self.assertEqual(response.status_code, 303)
        self.assertTrue(outside_image.exists())

    def test_failed_post_save_does_not_delete_images(self):
        original_image = self.write_fixture_image("a")
        replacement_image = self.write_fixture_image("b")
        original = self.new_fixture_post(image_names=[original_image])
        for action in ("delete", "edit"):
            self.write_posts([original])
            original_open = Path.open

            def fail_posts_writes(path, mode="r", *arguments, **keywords):
                if path == self.posts_file and "w" in mode:
                    raise OSError("Synthetic save failure")
                return original_open(path, mode, *arguments, **keywords)

            fields = {"post_id": "post-one"} if action == "delete" else self.edit_fields(
                replace_images="1", image_names=[replacement_image],
            )
            with self.subTest(action=action), patch.object(Path, "open", fail_posts_writes):
                try:
                    response = self.client.post(f"/threads/日記/{action}/execute", data=fields)
                except OSError:
                    pass
                else:
                    self.assertGreaterEqual(response.status_code, 500)
            self.assertEqual(self.posts(), [original])
            self.assertTrue((self.upload_directory / original_image).exists())
            self.assertTrue((self.upload_directory / replacement_image).exists())

    def test_thread_delete_counts_posts_and_removes_only_its_records(self):
        removed_image = self.write_fixture_image("a")
        shared_image = self.write_fixture_image("b")
        self.write_posts([
            self.new_fixture_post(image_names=[removed_image, shared_image]),
            self.new_fixture_post("same-thread"),
            self.new_fixture_post("other", thread_name="散歩", image_names=[shared_image]),
        ])
        response, context = self.request_with_context(
            "POST", "/delete-thread/confirm", data={"thread_id": "thread-one"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["post_count"], 2)
        response = self.client.post("/delete-thread/execute", data={"thread_id": "thread-one"})
        self.assertEqual(response.status_code, 303)
        self.assertEqual([post["id"] for post in self.posts()], ["other"])
        self.assertEqual(json.loads(self.threads_file.read_text(encoding="utf-8")), [{"id": "thread-two", "name": "散歩"}])
        self.assertFalse((self.upload_directory / removed_image).exists())
        self.assertTrue((self.upload_directory / shared_image).exists())

    def test_thread_delete_save_failure_does_not_delete_images(self):
        candidate_image = self.write_fixture_image()
        original = self.new_fixture_post(image_names=[candidate_image])
        for failed_file in (self.posts_file, self.threads_file):
            self.write_posts([original])
            original_open = Path.open

            def fail_data_writes(path, mode="r", *arguments, **keywords):
                if path == failed_file and "w" in mode:
                    raise OSError("Synthetic thread save failure")
                return original_open(path, mode, *arguments, **keywords)

            with self.subTest(failed_file=failed_file.name), patch.object(Path, "open", fail_data_writes):
                try:
                    response = self.client.post("/delete-thread/execute", data={"thread_id": "thread-one"})
                except OSError:
                    pass
                else:
                    self.assertGreaterEqual(response.status_code, 500)
            self.assertTrue((self.upload_directory / candidate_image).exists())

    def test_last_thread_cannot_be_deleted(self):
        self.write_threads([{"id": "thread-one", "name": "日記"}])
        for url in ("/delete-thread/confirm", "/delete-thread/execute"):
            self.assert_error(self.client.post(url, data={"thread_id": "thread-one"}))

    def test_homepage_averages_daily_averages_and_counts_today_posts(self):
        today = datetime.now().strftime("%Y-%m-%d")
        past_day = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.write_posts([
            self.new_fixture_post("today-one", created_at=today + " 09:00:00", rating="1"),
            self.new_fixture_post("today-two", created_at=today + " 10:00:00", rating="3"),
            self.new_fixture_post("yesterday", created_at=past_day + " 12:00:00", rating="5"),
        ])
        response, context = self.request_with_context("GET", "/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["today_count"], 2)
        self.assertEqual(context["today_average"], 2.0)
        # Mean of the two daily means (5 + 2) / 2; not all-post mean 3.
        self.assertEqual(context["overall_average"], 3.5)
        self.assertEqual(context["chart_dates"], [past_day, today])
        self.assertEqual(context["chart_averages"], [5.0, 2.0])
        self.assertEqual(context["chart_counts"], [1, 2])

    def test_empty_data_files_produce_empty_pages(self):
        self.threads_file.unlink()
        self.posts_file.unlink()
        response, context = self.request_with_context("GET", "/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["threads"], [])
        self.assertEqual(context["today_count"], 0)
        self.assertIsNone(context["today_average"])
        self.assertIsNone(context["overall_average"])
        self.assertEqual(context["chart_dates"], [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--app-dir", type=Path, default=Path(__file__).resolve().parents[1],
        help="Application folder (default: the parent of this script's tests folder).",
    )
    arguments, unittest_arguments = parser.parse_known_args()
    APPLICATION_DIRECTORY = arguments.app_dir.resolve(strict=True)
    if not (APPLICATION_DIRECTORY / "app.py").is_file():
        parser.error("--app-dir must contain app.py")
    # Existing implementation prints complete posts; keep test results concise.
    with redirect_stdout(StringIO()):
        unittest.main(argv=[sys.argv[0], *unittest_arguments], verbosity=2)
