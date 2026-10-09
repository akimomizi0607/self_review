# 第1週：PC環境の確認とインストール

第1週の3コマ目に、先生の合図で始めます。設計と発表を終えてから、自分のPCで授業に必要な環境が使えるか確認します。
すでに入っているものは再インストールする必要はありません。
入っていないものだけ、先生とChatGPTに確認しながら準備します。

> この資料は「環境をそろえるためのチェックリスト」です。
> Webアプリがどのような技術で動いているかという全体像は、別の授業資料で扱います。

## 1. 確認するもの

授業では主に次のものを使います。

- ChatGPT Plusのアカウント
- ChatGPTデスクトップアプリ
- Codex
- Webブラウザ
- PowerShell
- Python 3.12以上
- pip
- Git
- Pythonの仮想環境（venv）
- Flask

## 2. ChatGPTの確認

1. ChatGPT Plusのアカウントでサインインできることを確認する。
2. ChatGPTデスクトップアプリを起動する。
3. ChatGPTの中で `Chat` と `Codex` を利用できることを確認する。
4. 1コマ目に作成した「専門ユニット」プロジェクトを確認する。
5. 1コマ目に追加した4つのソースと、プロジェクトの指示欄の参照文を確認する。
6. Codexで、この `web_app` フォルダを開けることを確認する。

ChatGPTデスクトップアプリが入っていない場合は、先生の指示に従って公式の配布元からインストールします。

## 3. Pythonの確認

PowerShellを開き、次のどちらかを実行します。

```powershell
py --version
```

または

```powershell
python --version
```

Python 3.12以上が表示されれば、そのまま使います。

表示されない、または古いバージョンしか入っていない場合は、先生と確認してPythonをインストールします。

## 4. pipの確認

```powershell
py -m pip --version
```

`py` が使えない場合は、

```powershell
python -m pip --version
```

を試します。

## 5. Gitの確認

```powershell
git --version
```

バージョンが表示されればインストール済みです。

`git` が見つからない場合は、先生の指示に従ってGitをインストールします。

## 6. 仮想環境を作る

`web_app` フォルダをPowerShellで開き、授業用の仮想環境を作ります。

```powershell
py -m venv .venv
```

`py` が使えない場合は、

```powershell
python -m venv .venv
```

を使います。

仮想環境は、学生ごとのPC上に作成します。
`.venv` フォルダは提出物やGitには含めません。

## 7. Flaskをインストールする

仮想環境を有効化しなくても、次の方法でインストールできます。

```powershell
.\.venv\Scripts\python.exe -m pip install Flask
```

インストール後、次で確認します。

```powershell
.\.venv\Scripts\python.exe -c "import flask; print(flask.__version__)"
```

エラーが出なければ準備完了です。

## 8. 最終チェック

次を確認します。

- [ ] ChatGPT Plusでサインインできる
- [ ] ChatGPTデスクトップアプリを起動できる
- [ ] Codexを開ける
- [ ] Codexで `web_app` フォルダを開ける
- [ ] Python 3.12以上が使える
- [ ] pipが使える
- [ ] Gitが使える
- [ ] `.venv` を作成できた
- [ ] Flaskをインストールできた

うまくいかない場合は、エラーメッセージを消さずにChatGPTまたは先生へ見せてください。
