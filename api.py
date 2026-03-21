# api.py  — Enhanced Flask API (HuggingFace Spaces Edition)
import json
import functools
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
import os
from tutor_backend import get_relevant_context, generate_answer, chapters, HAS_API_KEY

app = Flask(__name__)

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
    return f"""<|im_start|>system\nYou are an expert CBSE Class 10 History teacher. Answer the student's question using ONLY the provided NCERT textbook excerpts.

INSTRUCTIONS:
1. Read ALL context carefully — it contains the answer.
2. Start with a direct 1-2 sentence answer.
3. Give supporting details, key names, dates, or events (3-4 sentences).
4. Format with bullet points where listing multiple items.
5. Do NOT say "not covered" if the context is clearly relevant.<|im_end|>
<|im_start|>user\nContext:
{context}

Student's Question: {question}<|im_end|>
<|im_start|>assistant\n"""


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "api_mode": "huggingface_inference"})


@app.route("/chapters", methods=["GET"])
def get_chapters():
    return jsonify([{"id": i + 1, "title": ch["title"]} for i, ch in enumerate(chapters)])


@app.route("/ask", methods=["POST"])
def ask():
    """Non-streaming endpoint (LRU-cached)."""
    data     = request.get_json()
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400
    result = json.loads(_cached_answer(question))
    return jsonify(result)


@app.route("/ask/stream")
def ask_stream():
    """Streaming SSE endpoint — delivers full answer as a single event."""
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

    def _stream():
        try:
            answer = generate_answer(question, chunks)
            # Send word by word for streaming effect
            words = answer.split(" ")
            for word in words:
                yield f"data: {json.dumps({'text': word + ' '})}\n\n"

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
    from tutor_backend import _hf_client
    import re

    if chapter_id < 1 or chapter_id > len(chapters):
        return jsonify({"error": "Invalid chapter ID"}), 400

    chap   = chapters[chapter_id - 1]
    sample = chap["text"][:3500]

    prompt = f"""<|im_start|>system\nYou are a CBSE Class 10 History teacher creating a quiz on "{chap['title']}".

Based ONLY on the excerpt below, generate exactly 4 multiple-choice questions.
Return ONLY valid JSON — no markdown, no explanation, just JSON:

{{
  "questions": [
    {{
      "q": "What year did the French Revolution begin?",
      "options": ["A. 1789", "B. 1792", "C. 1776", "D. 1804"],
      "answer": "A",
      "explanation": "The French Revolution began in 1789 with the storming of the Bastille."
    }}
  ]
}}<|im_end|>
<|im_start|>user\nTextbook excerpt:
{sample}<|im_end|>
<|im_start|>assistant\n"""

    try:
        content = _hf_client.text_generation(
            prompt,
            max_new_tokens=900,
            temperature=0.25,
            do_sample=True,
        ).strip()

        match = re.search(r'\{.*"questions"\s*:\s*\[.*\].*\}', content, re.DOTALL)
        if match:
            quiz = json.loads(match.group(0))
            return jsonify({"chapter": chap["title"], **quiz})

        start = content.find("{")
        end   = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                quiz = json.loads(content[start:end])
                return jsonify({"chapter": chap["title"], **quiz})
            except Exception:
                pass

        return jsonify({"error": "LLM returned unparseable JSON — please try again"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(debug=False, host='0.0.0.0', port=port)
