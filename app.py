from flask import Flask, request, jsonify
import difflib

app = Flask(__name__)

# Load the data
with open("about_me.txt", "r", encoding="utf-8") as f:
    data = f.read()


@app.route('/')
def home():
    return "<h2>✅ API is running!</h2>"


@app.route('/ask', methods=['POST'])
def ask():
    user_question = request.json.get("question", "")

    # Match user question with content
    best_sentences = difflib.get_close_matches(user_question, data.split('.'), n=3, cutoff=0.2)

    return jsonify({
        "question": user_question,
        "answers": best_sentences
    })


if __name__ == '__main__':
    app.run(debug=True)
