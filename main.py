import os

from flask import Flask, request, render_template_string
from openai import OpenAI
import psycopg2

import utils


app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_WORDS_IN_CONTEXT = 30000
SYSTEM_PROMPT = "You are a helpful assistant named the Virtual Factory Platform. You are designed to help users answer any questions they may have regarding lithium-ion batteries and related topics. Provide the most accurate and helpful response you can."

HTML_FORM = """
    <!doctype html>
    <html>
        <head>
            <title>Virtual Factory Platform</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    width: 800px;
                    text-align: justify;
                }
                h1 {
                    text-align: center;
                }
                input[type="text"] {
                    width: 90%;
                    padding: 10px;
                    margin: 10px 0;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                button {
                    width: 100px;
                    padding: 10px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    display: block;
                    margin: 10px auto;
                }
                button:hover {
                    background-color: #0056b3;
                }
                #answer {
                    margin-top: 20px;
                    font-size: 1.2em;
                    color: #333;
                    background-color: #f9f9f9;
                    padding: 10px;
                    border-radius: 4px;
                    max-height: 200px;
                    overflow-y: scroll;
                    white-space: pre-wrap;
                }
                #loading {
                    display: none;
                    margin-top: 20px;
                    font-size: 1.2em;
                    color: #333;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Virtual Factory Platform</h1>
                <form action="/" method="post" onsubmit="showLoading()">
                    <input type="text" name="user_input" value="{{ question }}" placeholder="Ask a question..." required>
                    <br>
                    <button type="submit">Submit</button>
                </form>

                <p id="loading">Loading...</p>

                <script>
                    function showLoading() {
                        document.getElementById("loading").style.display = "block";
                        var answerText = document.querySelector("#answer");
                        answerText.innerText = "";
                    }
                </script>

                {% if loaded %}
                <p id="answer">{{ answer }}</p>
                {% endif %}
            </div>
        </body>
    </html>
    """


def prepare_context(title: str, authors: str, citation_count: int, content: str) -> str:
    return f"Title of the paper:{title}, Authors of the paper: {authors}, Citation count of the paper: {citation_count}, Content of the paper: {content}"


def retreive_relevant_docs(question_embed: list[float], n: int) -> list[str]:
    conn = psycopg2.connect(utils.create_conn_string())
    cur = conn.cursor()

    TABLE_NAME = os.getenv("GSCHOLAR_TABLE")

    cur.execute(
        f"SELECT title, authors, citation_count, content FROM {TABLE_NAME} ORDER BY embedding <#> '{question_embed}' LIMIT {n};"
    )
    docs_ = cur.fetchall()

    count_words = 0
    docs = []

    for doc in docs_:
        title, authors, citation_count, content = doc
        context_ = prepare_context(title, authors, citation_count, content)

        if count_words + len(context_.split(" ")) < MAX_WORDS_IN_CONTEXT:
            docs.append(context_)
            count_words += len(context_)
        else:
            break

    cur.close()
    conn.close()

    return docs


def get_embedding(question: str) -> list[float]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=[question],
        encoding_format="float",
    )

    return resp.data[0].embedding


@app.route("/", methods=["GET"])
def get():
    return render_template_string(HTML_FORM, loaded=False)


@app.route("/", methods=["POST"])
def post():
    question = request.form["user_input"]
    q_embed = get_embedding(question)

    docs = retreive_relevant_docs(q_embed, n=5)
    user_prompt = (
        "Relevant Documents: "
        + '"""'
        + '"""'.join(docs)
        + '"""'
        + f" \n\nQuestion: {question}"
    )

    client = OpenAI(api_key=OPENAI_API_KEY)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    answer = resp.choices[0].message.content

    return render_template_string(
        HTML_FORM, question=question, answer=answer, loaded=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
