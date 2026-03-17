# api.py  — Enhanced Flask API
import json
import functools
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from tutor_backend import get_relevant_context, generate_answer, chapters
import ollama

app = Flask(__name__)

LLM_MODEL          = "llama3.2:1b"
BASELINE_TOKENS    = 12000   # naive RAG — sends entire textbook
CHARS_PER_TOKEN    = 4       # rough estimate


# ─────────────────────────────────────────────────────────────
# LRU CACHE  (repeated questions get instant answers)
# ─────────────────────────────────────────────────────────────
@functools.lru_cache(maxsize=128)
def _cached_answer(question: str) -> str:
    """Run full RAG pipeline; result is cached per unique question."""
    chunks = get_relevant_context(question)
    if not chunks:
        return json.dumps({
            "answer": "I couldn't find relevant content for this question in the textbook.",
            "sources": [], "tokens_used": 0, "tokens_saved": BASELINE_TOKENS
        })
    sources      = list(dict.fromkeys(c["chapter_title"] for c in chunks))
    answer       = generate_answer(question, chunks)
    tokens_used  = max(100, sum(len(c["text"][:600]) for c in chunks) // CHARS_PER_TOKEN
                       + len(question.split()) + 80)
    tokens_saved = max(0, BASELINE_TOKENS - tokens_used)
    return json.dumps({
        "answer": answer, "sources": sources,
        "tokens_used": tokens_used, "tokens_saved": tokens_saved
    })


def _build_prompt(question: str, chunks: list) -> str:
    context = "\n\n---\n".join(
        [f"[Source: {c['chapter_title']}]\n{c['text'][:600]}" for c in chunks]
    )
    return f"""You are an expert CBSE Class 10 History teacher. Answer the student's question \
using ONLY the provided NCERT textbook excerpts.

INSTRUCTIONS:
1. Read ALL context carefully — it contains the answer.
2. Start with a direct 1-2 sentence answer.
3. Give supporting details, key names, dates, or events (3-4 sentences).
4. Format with bullet points where listing multiple items.
5. Do NOT say "not covered" if the context is clearly relevant.

Context:
{context}

Student's Question: {question}

Answer:"""


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chapters", methods=["GET"])
def get_chapters():
    return jsonify([{"id": i + 1, "title": ch["title"]} for i, ch in enumerate(chapters)])


@app.route("/ask", methods=["POST"])
def ask():
    """Non-streaming endpoint  (used for chip-click fallback, LRU-cached)."""
    data     = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400
    result = json.loads(_cached_answer(question))
    return jsonify(result)


@app.route("/ask/stream")
def ask_stream():
    """Streaming SSE endpoint  — word-by-word delivery like ChatGPT."""
    question = request.args.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    chunks = get_relevant_context(question)

    if not chunks:
        def _empty():
            msg = "I couldn't find relevant content for this question in the textbook."
            yield f"data: {json.dumps({'text': msg})}\n\n"
            yield f"data: {json.dumps({'done': True, 'sources': [], 'tokens_used': 0, 'tokens_saved': BASELINE_TOKENS})}\n\n"
        return Response(stream_with_context(_empty()), content_type="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    sources     = list(dict.fromkeys(c["chapter_title"] for c in chunks))
    tokens_used = max(100, sum(len(c["text"][:600]) for c in chunks) // CHARS_PER_TOKEN
                      + len(question.split()) + 80)
    tokens_saved = max(0, BASELINE_TOKENS - tokens_used)

    prompt = _build_prompt(question, chunks)

    def _stream():
        try:
            for part in ollama.chat(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                options={"num_predict": 400, "temperature": 0.2, "top_p": 0.85},
            ):
                text = part.get("message", {}).get("content", "")
                if text:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            done_payload = json.dumps({'done': True, 'sources': sources,
                                       'tokens_used': tokens_used, 'tokens_saved': tokens_saved})
            yield f"data: {done_payload}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(_stream()), content_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/quiz/<int:chapter_id>")
def get_quiz(chapter_id):
    """Generate 4 MCQs for the given chapter using the LLM."""
    if chapter_id < 1 or chapter_id > len(chapters):
        return jsonify({"error": "Invalid chapter ID"}), 400

    chap   = chapters[chapter_id - 1]
    sample = chap["text"][:3500]

    prompt = f"""You are a CBSE Class 10 History teacher creating a quiz on "{chap['title']}".

Based ONLY on the excerpt below, generate exactly 4 multiple-choice questions.
Return ONLY valid JSON — no markdown, no explanation, just JSON:

{{
  "questions": [
    {{
      "q": "Question text?",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",
      "explanation": "One sentence why A is correct."
    }}
  ]
}}

Textbook excerpt:
{sample}

JSON:"""

    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"num_predict": 900, "temperature": 0.25},
        )
        import re
        content = response["message"]["content"].strip()
        # Find the JSON array part
        match = re.search(r'\{.*"questions"\s*:\s*\[.*\].*\}', content, re.DOTALL)
        if match:
            quiz = json.loads(match.group(0))
            return jsonify({"chapter": chap["title"], **quiz})
        
        # Fallback parsing
        start = content.find("{")
        end   = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                quiz = json.loads(content[start:end])
                return jsonify({"chapter": chap["title"], **quiz})
            except Exception as json_e:
                pass # fall through to error
                
        return jsonify({"error": "LLM returned unparseable JSON — try again"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
