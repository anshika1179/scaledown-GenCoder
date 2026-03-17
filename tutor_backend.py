# tutor_backend.py
import os
import json
from typing import List, Dict
import fitz
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import ollama

# ── Config ────────────────────────────────────────────────────
CHAPTER_FOLDER = "ncert_history_chapters"
PDF_FILES = ["jess301.pdf", "jess302.pdf", "jess303.pdf", "jess304.pdf", "jess305.pdf"]
CHUNK_SIZE    = 700          # slightly larger chunks → more context per piece
CHUNK_OVERLAP = 120          # more overlap → fewer gaps between chunks
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_DB_PATH  = "faiss_index_ncert.bin"
METADATA_PATH   = "metadata_ncert.json"
LLM_MODEL = "llama3.2:1b"

# ── Load embedding model ONCE at startup ─────────────────────
print("Loading embedding model...")
_embed_model = SentenceTransformer(EMBEDDING_MODEL)
print("Embedding model loaded.")


def extract_chapters():
    chapters = []
    title_map = {
        "01": "The Rise of Nationalism in Europe",
        "02": "Nationalism in India",
        "03": "The Making of a Global World",
        "04": "The Age of Industrialisation",
        "05": "Print Culture and the Modern World",
    }
    for pdf_name in PDF_FILES:
        path = os.path.join(CHAPTER_FOLDER, pdf_name)
        if not os.path.exists(path):
            continue
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n\n"
        chap_num = pdf_name.replace("jess3", "").replace(".pdf", "")
        title = title_map.get(chap_num, f"Chapter {chap_num}")
        chapters.append({"title": title, "text": text.strip(), "filename": pdf_name})
        doc.close()
    return chapters


def chunk_text(text: str) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end].strip())
        start = end - CHUNK_OVERLAP if end < len(text) else end
    return [c for c in chunks if len(c) > 60]


def build_index():
    if os.path.exists(VECTOR_DB_PATH) and os.path.exists(METADATA_PATH):
        print("Index already exists, loading...")
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["chapters"]

    chapters = extract_chapters()
    if not chapters:
        raise FileNotFoundError("No PDFs found in folder!")

    all_chunks = []
    metadata   = []

    for chap_idx, chap in enumerate(chapters):
        chunks = chunk_text(chap["text"])
        for c_idx, c_text in enumerate(chunks):
            all_chunks.append(c_text)
            metadata.append({
                "chapter_idx":   chap_idx,
                "chapter_title": chap["title"],
                "chunk_idx":     c_idx,
                "text":          c_text
            })

    embeddings = _embed_model.encode(all_chunks, show_progress_bar=True).astype("float32")
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, VECTOR_DB_PATH)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump({"chapters": chapters, "chunks_metadata": metadata}, f, ensure_ascii=False)

    print(f"Built index with {len(chapters)} chapters, {len(all_chunks)} chunks")
    return chapters


# ── Load everything ONCE at startup ──────────────────────────
chapters = build_index()

print("Loading FAISS index into memory...")
_faiss_index = faiss.read_index(VECTOR_DB_PATH)
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    _metadata = json.load(f)["chunks_metadata"]

# FIX 1: Cache chapter embeddings at startup (not re-computed per query)
print("Pre-computing chapter embeddings...")
_chap_previews = [f"{c['title']}: {c['text'][:500]}" for c in chapters]
_chap_embs     = _embed_model.encode(_chap_previews, normalize_embeddings=True).astype("float32")
print("Ready!")


def get_relevant_context(question: str, top_k_chapters: int = 2, top_k_chunks: int = 5):
    """
    2-stage context pruning:
      Stage 1 — pick top_k_chapters most relevant chapters via cosine similarity
      Stage 2 — FAISS search with larger k, keep only chunks from selected chapters

    FIX 2: k=60 instead of k=20 → much less chance of zero-intersection
    FIX 3: top_k_chunks=5 for richer context
    """
    # Embed & normalize the query
    q_emb = _embed_model.encode(question, normalize_embeddings=True).astype("float32")

    # Stage 1 – chapter-level pruning (uses cached embeddings)
    scores  = np.dot(_chap_embs, q_emb)          # already normalized → cosine scores
    top_idx = np.argsort(scores)[-top_k_chapters:][::-1].tolist()

    # Stage 2 – chunk-level FAISS search (larger k for safety)
    q_emb_faiss = q_emb.reshape(1, -1)
    D, I = _faiss_index.search(q_emb_faiss, k=60)   # was 20 — now 60

    relevant = []
    for dist, idx in zip(D[0], I[0]):
        if idx == -1:
            continue
        m = _metadata[idx]
        if m["chapter_idx"] in top_idx:
            relevant.append({**m, "score": float(1 / (1 + dist))})

    relevant.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate consecutive near-identical chunks
    seen, deduped = set(), []
    for r in relevant:
        key = r["text"][:80]
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped[:top_k_chunks]


def generate_answer(question: str, context_chunks: List[Dict]) -> str:
    """
    Generate an accurate, curriculum-aligned answer.

    FIX 4: More context per chunk (600 chars → was 400)
    FIX 5: num_predict raised to 350 so answers don't truncate
    FIX 6: Rewritten prompt — tells the model to use EVERYTHING in context
    """
    # Use up to 600 chars per chunk for richer context
    context = "\n\n---\n".join(
        [f"[Source: {c['chapter_title']}]\n{c['text'][:600]}" for c in context_chunks]
    )

    prompt = f"""You are an expert CBSE Class 10 History teacher. The student is asking a question \
from the NCERT textbook "India and the Contemporary World – II" (Chapters 1–5).

INSTRUCTIONS:
1. Read ALL the provided context carefully — it contains relevant text from the textbook.
2. Write a clear, accurate answer using the context. DO NOT ignore information that is present.
3. Structure your answer well:
   - Start with a direct 1–2 sentence answer to the question.
   - Then give supporting details from the context (2–4 sentences).
   - If relevant, mention key names, dates, or events found in the context.
4. Do NOT say "the textbook does not cover this" if the context has relevant information.
5. Only say "not covered in detail" if the context is genuinely unrelated to the question.

Context from textbook:
{context}

Student's Question: {question}

Answer (write clearly and completely):"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={
            "num_predict": 350,    # was 200 — was cutting off answers
            "temperature": 0.2,    # lower = more factual, less hallucination
            "top_p": 0.85,
        }
    )
    return response['message']['content'].strip()