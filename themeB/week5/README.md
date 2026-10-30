# 自分レビュー：第5週版

日々の出来事を星評価・文章・任意の画像で記録し、日別の評価と投稿数を振り返るアプリです。

## 起動

このフォルダを作業場所にし、Flaskを利用できるPythonで `python app.py` を実行します。表示された `http://127.0.0.1:5000/` をブラウザで開きます。

スレッドデータがない初回だけ、`python initialize_default_threads.py` で初期スレッドを作れます。既存の `threads.json` がある場合は変更しません。

## Pythonファイルの役割

| ファイル | 役割 |
| --- | --- |
| `app.py` | 起動入口。各URLで入力・確認・保存・表示をつなぐ |
| `json_data_storage.py` | 投稿・スレッドのJSON読み書きと検索 |
| `post_image_attachments.py` | 添付画像の条件確認、保存、不要画像の削除 |
| `daily_rating_statistics.py` | 日別平均、今日の評価・投稿数、グラフ用データの集計 |
| `initialize_default_threads.py` | 初期スレッドを必要な場合だけ作成 |

## 画面と表示ファイル

`templates/` のファイル名は、その画面の操作を表します。`base_layout.html` は共通のHTML枠、`_post_image_gallery.html` は画像の横並び表示です。

| 操作 | テンプレート |
| --- | --- |
| スレッド一覧と評価グラフ | `thread_list.html` |
| 選択したスレッドの投稿一覧 | `thread_posts.html` |
| 新規投稿の入力・確認 | `new_post_form.html`、`new_post_confirmation.html` |
| 編集する投稿の選択・入力・確認 | `post_edit_selection.html`、`post_edit_form.html`、`post_edit_confirmation.html` |
| 削除する投稿の選択・確認 | `post_delete_selection.html`、`post_delete_confirmation.html` |
| 新しいスレッドの入力 | `new_thread_form.html` |
| 削除するスレッドの選択・確認 | `thread_delete_selection.html`、`thread_delete_confirmation.html` |
| 入力エラー | `input_error.html` |

`static/diary_styles.css` が見た目、`static/image_attachment_preview.js` が選択画像のプレビュー、`static/daily_rating_chart.js` が評価・投稿数のグラフを担当します。

## 保存データと動作上の決まり

- `posts.json` に投稿、`threads.json` にスレッド、`static/uploads/` に添付画像を保存します。保存先は起動する場所にかかわらず、このフォルダを基準に決まります。
- 投稿の `id`、`thread_name`、`created_at`、`rating`、`headtext`、`bodytext`、`image_names` は、既存データとフォームで使っている名前です。読みやすい内部変数名とは分け、互換性のため保持しています。
- 本文と画像は任意です。画像はJPG／PNG、最大4枚、各5,000,000バイトまでです。
- 画像は確認画面に進む時点で保存します。画像を選び直さない編集では、保存済みの画像を保持します。
- 編集できるのは作成時刻から2時間以内です。最終保存時にも期限を確認します。
- 投稿・スレッドの削除や画像差し替えでは、JSONの保存が成功した後で、他の投稿が参照していない対象画像だけを削除します。
- 全体評価は日別平均の平均です。投稿数の多い日も少ない日も、日ごとを同じ重さで集計します。

第5週の日報は当日の記録としてそのまま残しています。

## 変更後の動作確認

`python tests/test_application_regression.py` で、投稿・編集・削除・画像管理・評価集計の26項目を確認できます。テストはコードだけを一時フォルダにコピーし、自作の投稿と画像を使います。実際の投稿データや写真は変更しません。
