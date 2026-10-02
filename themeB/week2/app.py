from flask import Flask, render_template
from datetime import date
app = Flask(__name__)

@app.route("/")
def index():
    today = date.today().strftime("%Y年%m月%d日")
    threads = ["日誌","今日の食事","ネガティブノート"]
    return render_template("index.html", today=today, threads=threads)
@app.route("/threads/<thread_name>")
def show_thread(thread_name):
    return render_template("thread.html", thread_name=thread_name)

if __name__ == "__main__":
    app.run(debug=True)
