# Flaskアプリの動かし方（Windows / PowerShell）

## 1. 作業する週のフォルダへ移動

例：テーマBの第3週

```powershell
cd "自分のweb_appフォルダ\themeB\week3"
```

## 2. 仮想環境を作る（初回だけ）

```powershell
python -m venv venv
```

## 3. 仮想環境を有効化

```powershell
venv\Scripts\activate
```

先頭に `(venv)` と表示されればOKです。

## 4. Flaskをインストール

```powershell
pip install flask
```

`requirements.txt` がある場合は次でも構いません。

```powershell
pip install -r requirements.txt
```

## 5. アプリを起動

```powershell
python app.py
```

`Running on http://127.0.0.1:5000` のように表示されたら、ブラウザでそのURLを開きます。

## 6. 終了

PowerShellで `Ctrl + C`。

仮想環境を解除するときは：

```powershell
deactivate
```

## 注意

`venv` は配布ファイルには含めていません。PCごとに自分で作成します。
