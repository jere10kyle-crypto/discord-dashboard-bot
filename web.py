from flask import Flask, request, render_template_string, redirect
import json

app = Flask(__name__)
PASSWORD = "1234"  # change this later

TEMPLATE = """
<h2>Login</h2>
<form method="POST">
  Password: <input type="password" name="password">
  <input type="submit" value="Login">
</form>

{% if logged_in %}
  <h3>Banned Words</h3>
  <form method="POST" action="/add_word">
    Add word: <input type="text" name="word">
    <input type="submit" value="Add">
  </form>
  <form method="POST" action="/remove_word">
    Remove word: <input type="text" name="word">
    <input type="submit" value="Remove">
  </form>
  <p>Current words: {{ words }}</p>
{% endif %}
"""

logged_in = False

@app.route("/", methods=["GET", "POST"])
def login():
    global logged_in
    if request.method == "POST":
        if request.form["password"] == PASSWORD:
            logged_in = True
    data = json.load(open("banned_words.json"))
    return render_template_string(TEMPLATE, logged_in=logged_in, words=data["words"])

@app.route("/add_word", methods=["POST"])
def add_word():
    word = request.form["word"].lower()
    data = json.load(open("banned_words.json"))
    if word not in data["words"]:
        data["words"].append(word)
    with open("banned_words.json", "w") as f:
        json.dump(data, f)
    return redirect("/")

@app.route("/remove_word", methods=["POST"])
def remove_word():
    word = request.form["word"].lower()
    data = json.load(open("banned_words.json"))
    if word in data["words"]:
        data["words"].remove(word)
    with open("banned_words.json", "w") as f:
        json.dump(data, f)
    return redirect("/")
