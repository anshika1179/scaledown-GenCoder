# 📚 NCERT History AI Tutor — Context Pruning Edition

**🔴 LIVE DEMO:** [Try the Web App on Hugging Face](https://anshika1179-scaledown-gencoder.hf.space)  
*(Note: As this is hosted on a free tier, the space may take a moment to wake up from sleep mode, or occasionally return a 503 error during high load.)*

> **ScaleDown Session 3 Challenge** | Team: **GenCoder** | Track: **The Education Tutor for Remote India** | Technique: **Context Pruning**

---

## 📋 Problem Description

Personalized AI tutors are revolutionizing education, but they are expensive and resource-heavy. In rural India, where computing power is low and bandwidth is limited, students cannot afford the high latency and cost of pinging massive cloud models (like ChatGPT) for every question.

Our system solves this by:
- Ingesting entire **state-board textbooks** (large PDFs).
- Providing **personalized, curriculum-aligned answers**.
- Optimizing for **lowest cost and local execution** through aggressive data pruning.

---

## 🧠 Core Solution: 2-Stage Context Pruning

We built a 2-Stage Context Pruning RAG (Retrieval-Augmented Generation) pipeline that drastically cuts down the token payload sent to the LLM. Rather than passing thousands of tokens of textbook data, we selectively filter it down to exactly what the AI needs.

### 🔵 Offline Setup (Done Once)
1. **PDF Ingestion:** PyMuPDF (`fitz`) extracts raw text from 5 chapters of the NCERT History textbook.
2. **Chunking:** Text is split into 700-character chunks (with 120-character overlap).
3. **Embedding:** `SentenceTransformers` (`all-MiniLM-L6-v2`) converts these chunks into vector embeddings.
4. **Indexing:** All vectors are stored efficiently in a **FAISS Index**, persisted logically to disk so it loads instantly on startup.

### 🟣 Online Execution (Per Question)
```
Student Query → Embed → [Stage 1: Chapter Filter] → [Stage 2: Chunk Filter] → LLM → Answer
```
- **Stage 1 (Chapter-Level Pruning):** We use pre-computed chapter embeddings via cosine similarity to filter out irrelevant chapters immediately. Only the top-2 highest correlation chapters are kept.
- **Stage 2 (Chunk-Level Pruning):** We run a deeper FAISS nearest-neighbor search (`k=60` to avoid "zero-intersection" scenarios) but *only* keep chunks matching the top chapters.
- **Generation:** Only the top-5 most relevant chunks are fed into **Ollama (Llama 3.2:1B)** running locally, ensuring zero API costs!

---

## 📊 Performance Benchmarks (Measurable Results)

Our Context Pruning technique directly tackles the high-cost barrier of AI in remote areas.

| Metric | Without Pruning (Raw Context) | With 2-Stage Pruning | Impact |
|---|---|---|---|
| **Context Payload** | ~12,000+ Tokens | ~800 - 1,200 Tokens | **~90% Reduction** |
| **Inference Time** | 45s+ (on CPU) | 2s - 5s | **~10x Speedup** |
| **Local Memory** | High (Overflow common) | Low (< 2GB) | **Highly Stable** |
| **Cost per Query** | $0.005+ via Cloud API | **$0.00 (Local Llama 3.2)** | **100% Free** |

---

## 🎬 Demo

![AI Tutor Demo](demo_videos.webp)

---

## ✨ Key Features
- 🔪 **Aggressive Token Pruning** — Multi-stage FAISS retrieval cuts context by 90%.
- 🤖 **Local LLM Execution** — Driven entirely by Llama 3.2 (1B) locally. No internet needed after setup!
- 📝 **Interactive Quiz Engine** — Automatically generates challenging MCQs strictly from the chapter chunks.
- 🎨 **Premium Glassmorphism UI** — High-contrast dark theme optimized for readability and engagement.
- 🔤 **Robust Text Processing** — Advanced encoding resolution handles messy PDF extractions and ensures stable UTF-8 UI delivery.
- 📖 **Automatic Source Citation** — Transparently displays exactly which chapter the answer was pulled from.

---

## 🚀 Quick Start (Local Setup)

Want to run it on your own machine? It requires very little compute.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Local LLM (Ollama)
Download Ollama from [ollama.com](https://ollama.com/), then pull the Llama 3.2 model:
```bash
ollama pull llama3.2:1b
```

### 3. Run the API and UI
Ensure the Ollama service is running (`ollama serve`), then start the Flask app:
```bash
python api.py
```
> Open your browser to `http://localhost:5000`.

---
<div align="center">
  <sub>Built with ❤️ by Team GenCoder using Ollama · FAISS · SentenceTransformers · Flask</sub>
</div>
