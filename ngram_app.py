"""N-gram Calculator: run with `python3 ngram_app.py`, then open http://localhost:8000"""
import re
import webbrowser
from collections import Counter
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8000
START, END = "<s>", "</s>"

# Built-in training corpus (one sentence per line)
CORPUS = """i love natural language processing
i love machine learning
i love python programming
natural language processing is fun
machine learning is fun
python programming is fun
we study natural language processing
we study machine learning models
language models predict the next word
a language model assigns a probability to a sentence
n gram models count words in a corpus
the model learns from a corpus of text"""


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


sentences = [words(line) for line in CORPUS.split("\n") if words(line)]
vocab = {w for s in sentences for w in s} | {END}

# grams[n] counts n-grams, contexts[n] counts the (n-1)-word contexts
grams = {n: Counter() for n in (1, 2, 3)}
contexts = {n: Counter() for n in (1, 2, 3)}
for s in sentences:
    for n in (1, 2, 3):
        seq = [START] * (n - 1) + s + [END]
        for i in range(n - 1, len(seq)):
            ctx = tuple(seq[i - n + 1:i])
            grams[n][ctx + (seq[i],)] += 1
            contexts[n][ctx] += 1


def analyze(sentence, n, smooth):
    """Return table rows and the sentence probability for an n-gram model."""
    seq = [START] * (n - 1) + words(sentence) + [END]
    rows, product = [], 1.0
    for i in range(n - 1, len(seq)):
        ctx = tuple(seq[i - n + 1:i])
        count, ctx_count = grams[n][ctx + (seq[i],)], contexts[n][ctx]
        if smooth:
            prob = (count + 1) / (ctx_count + len(vocab) + 1)
        else:
            prob = count / ctx_count if ctx_count else 0.0
        product *= prob
        rows.append((" ".join(ctx + (seq[i],)), count, ctx_count, prob))
    return rows, product


def render(sentence, smooth):
    page = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>N-gram Calculator</title>
<style>
 body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; padding: 0 16px; color: #1b2733; }}
 input[type=text] {{ width: 70%; padding: 10px; font-size: 16px; }}
 button {{ padding: 10px 18px; font-size: 16px; }}
 table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
 th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
 th {{ background: #e0e8ff; }}
 .zero {{ color: #b4400f; font-weight: bold; }}
</style></head><body>
<h1>N-gram Calculator</h1>
<form method="get">
  <input type="text" name="sentence" value="{escape(sentence)}" placeholder="Type a sentence">
  <button type="submit">Calculate</button><br><br>
  <label><input type="checkbox" name="smooth" value="1" {"checked" if smooth else ""}> Add-one smoothing</label>
</form>"""
    if words(sentence):
        for n, name in ((1, "Unigram"), (2, "Bigram"), (3, "Trigram")):
            rows, product = analyze(sentence, n, smooth)
            page += f"<h2>{name}s</h2><p>Sentence probability: <b>{product:.6g}</b></p>"
            page += "<table><tr><th>Sequence</th><th>Count</th><th>Context count</th><th>Probability</th></tr>"
            for seq, count, ctx_count, prob in rows:
                css = ' class="zero"' if prob == 0 else ""
                page += (f"<tr{css}><td>{escape(seq)}</td><td>{count}</td>"
                         f"<td>{ctx_count}</td><td>{prob:.6f}</td></tr>")
            page += "</table>"
    else:
        page += "<p>Enter a sentence to see its n-gram results.</p>"
    return page + "</body></html>"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        sentence = query.get("sentence", ["i love natural language processing"])[0]
        body = render(sentence, "smooth" in query).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    print(f"Running at http://localhost:{PORT}  (press Ctrl+C to stop)")
    webbrowser.open(f"http://localhost:{PORT}")
    HTTPServer(("localhost", PORT), Handler).serve_forever()