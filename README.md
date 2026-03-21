# 📚 NCERT History AI Tutor — Education Tutor for Remote India
[![Space](https://img.shields.io/badge/Status-Deployed_on_Hugging_Face-blue?style=for-the-badge&logo=huggingface)](https://anshika1179-scaledown-gencoder.hf.space)

**🔴 LIVE DEMO:** [Click here to try the App!](https://anshika1179-scaledown-gencoder.hf.space)  
*(Note: Hosted on a free Hugging Face Space. It may take a minute to wake up from sleep mode, or return transient errors during heavy load if Hugging Face Inference Providers are busy.)*

> **GenCoder Challenge · Session 3** | Track: AI/ML · Technique: **Context Pruning**

---

## 🏷️ Topic

**The Education Tutor for Remote India**

Personalized AI tutors are revolutionizing education, but they are expensive to run. In rural India, where internet is spotty and computing power is low, students cannot afford high-latency, high-cost queries to massive models like GPT-4 for every question.

---

## 📋 Problem Description

Build an intelligent tutoring system capable of:

- Ingesting entire **state-board textbooks** (large PDFs)
- Providing **personalized, curriculum-aligned answers**
- Optimizing for **lowest cost per query** and **minimal data transfer**

### Key Constraints

| Constraint | Solution |
|---|---|
| Must ingest large PDFs without re-processing every time | FAISS index built **once**, loaded from disk on startup |
| Must provide interactive ways to test knowledge | **Quiz Mode** generates chapter-specific MCQs using Qwen2.5/DeepSeek |
| Must work on low-bandwidth / low-compute devices | Multi-provider cloud LLM via HuggingFace Inference Providers — zero local GPU needed |

---

## 🧠 Proposed Solution — Context Pruning RAG

### Architecture Diagram

![System Architecture](architecture.png)

### How It Works

The system uses a **2-Stage Context Pruning** pipeline to drastically reduce the number of tokens sent to the LLM per query, drastically reducing API costs and latency:

#### 🔵 Offline Phase (One-Time Setup)

```
PDF Textbooks → PyMuPDF Extraction → Text Chunking → Sentence Embeddings → FAISS Index
```

1. **PDF Ingestion** — `PyMuPDF (fitz)` extracts raw text from 5 NCERT History chapters
2. **Chunking** — Text split into 600-character chunks with 100-char overlap for context continuity
3. **Embedding** — `all-MiniLM-L6-v2` encodes every chunk into a 384-dim vector
4. **Indexing** — All vectors stored in a `FAISS IndexFlatL2` index, persisted to disk

#### 🟣 Online Phase (Per Query — Context Pruning)

```
Student Query → Embed → [Stage 1: Chapter Filter] → [Stage 2: Chunk Filter] → LLM → Answer
```

**Stage 1 — Chapter-Level Pruning:**
- Encode the question and compute cosine similarity against each chapter's summary embedding.
- **Select only Top-2 most relevant chapters** (out of 5) → eliminates 60% of the corpus immediately.
- **Optimisation**: Chapter embeddings are **cached at startup** for near-instant filtering.

**Stage 2 — Chunk-Level Pruning:**
- Run FAISS nearest-neighbor search across **60 candidates** (expanded from 20 for better grounding).
- **Keep only chunks from the Top-2 chapters** → further filters irrelevant content.
- Pass **Top-5 final chunks** to the LLM.

> *Multi-provider HuggingFace Inference (novita / sambanova) makes it free to run — no paid API needed. The system handles "zero-intersection" scenarios with a deeper search pool and automatic provider fallback.*


---

## 📊 Performance Benchmarks (Measurable Results)

The **2-Stage Context Pruning** technique directly addresses the high cost and latency of AI in remote areas.

| Metric | Without Pruning | With 2-Stage Pruning | Improvement |
|---|---|---|---|
| **Context Tokens** | ~12,000+ (Entire Book) | ~800 - 1,200 | **~90% Reduction** |
| **Inference Time** | 45s+ (on low-end CPU) | 2s - 5s | **~10x Speedup** |
| **Memory Profile** | High (Context overflow) | Low (< 2GB) | **Rock-solid Stability** |
| **Cost per Query** | $0.005+ (Cloud API) | **$0.00 (HF Free Tier)** | **100% Cost Savings** |
| **Answer Quality** | Prone to hallucinations | Grounded in exact passages | **High Quality Preservation** |

---

## 🎬 Demo Video

![AI Tutor Demo](demo_videos.webp)

---

## 🏗️ Project Structure

```
session 3 project/
├── tutor_backend.py          # Core RAG + Context Pruning logic
├── api.py                    # Flask REST API (GET /chapters, POST /ask)
├── app.py                    # Streamlit UI (alternative frontend)
├── templates/
│   └── index.html            # Premium HTML/JS chat frontend
├── ncert_history_chapters/   # NCERT PDF textbooks (Ch. 1–5)
│   ├── jess301.pdf
│   ├── jess302.pdf
│   ├── jess303.pdf
│   ├── jess304.pdf
│   └── jess305.pdf
├── faiss_index_ncert.bin     # Pre-built FAISS vector index (auto-generated)
├── metadata_ncert.json       # Chunk metadata + chapter text (auto-generated)
└── architecture.png          # System architecture diagram
```

---

## 🚀 Deployment (Hugging Face Spaces)

This project is fully containerized and currently deployed on **Hugging Face Spaces** using Docker.

### Steps to Host your own copy:
1.  Create a new **Docker Space** on [Hugging Face](https://huggingface.co/spaces).
2.  Connect your GitHub repository to the Space (or upload the files directly).
3.  **Important**: In the Space Settings > Variables and Secrets, add:
    -   `HF_TOKEN`: Your free Hugging Face API token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). Create a **Fine-grained** token with **"Make calls to Inference Providers"** permission enabled.
4.  Hugging Face will automatically use the provided `Dockerfile` to build the environment, download the FAISS index, and launch the `gunicorn` server!
5.  The app uses a **multi-provider fallback system** — it automatically tries multiple AI providers (novita, sambanova) until one responds, ensuring maximum uptime.

---

## ⚙️ Tech Stack & Dependencies

| Component | Technology |
|---|---|
| **LLM (Inference)** | Multi-provider: [Qwen2.5-Coder-32B](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct) via novita, [DeepSeek-R1](https://huggingface.co/deepseek-ai/DeepSeek-R1) via sambanova — automatic fallback |
| **Inference Router** | HuggingFace Inference Providers (`provider="novita"` / `"sambanova"`) |
| **Embeddings** | `sentence-transformers` · `all-MiniLM-L6-v2` |
| **Vector Search** | `faiss-cpu` |
| **PDF Parsing** | `PyMuPDF (fitz)` & `pypdf` |
| **Backend API** | `Flask` & `numpy` |
| **Production Server** | `gunicorn` |
| **Frontend UI** | Vanilla HTML · CSS (Glassmorphism) · JavaScript |

### Install Dependencies

```bash
pip install flask huggingface_hub sentence-transformers faiss-cpu pymupdf pypdf numpy gunicorn
```

---

## 🚀 Quick Start (Local)

```bash
python api.py
# Open http://localhost:7860
```

> **First run** takes ~30–60 seconds to build the FAISS index from PDFs.  
> Subsequent runs load the cached index instantly.

---

## 📚 Textbook Coverage

| # | Chapter | NCERT PDF |
|---|---|---|
| 1 | The Rise of Nationalism in Europe | `jess301.pdf` |
| 2 | Nationalism in India | `jess302.pdf` |
| 3 | The Making of a Global World | `jess303.pdf` |
| 4 | The Age of Industrialisation | `jess304.pdf` |
| 5 | Print Culture and the Modern World | `jess305.pdf` |

---

## ✨ Key Features

- 🔪 **2-Stage Context Pruning** — Drastically reduces token context by ~90%, enabling fast inference
- 📝 **Interactive Quiz Mode** — Automatically generates challenging MCQs for any chapter using strict JSON parsing
- 💾 **Pre-built FAISS Index** — Built once at startup, loaded instantly on every subsequent run
- 🤖 **Free LLM Inference** — Multi-provider fallback (Qwen2.5 via novita, DeepSeek-R1 via sambanova) through HuggingFace Inference Providers — zero cost
- 🎨 **Premium UI & Theming** — Dark-themed, glassmorphism design with improved contrast and accessibility
- 🔤 **Robust Text Processing** — Advanced encoding resolution ensures stable UTF-8 rendering, eliminating garbled characters from PDF sources
- 📖 **Source Citation** — Every answer shows exactly which chapter it came from
- 📱 **Mobile-responsive** — Works on low-end devices and small screens

---

## 👩‍💻 Built For
**ScaleDown Session 3 Challenge**

**Team name-GenCoder **  
Track: *The Education Tutor for Remote India*  
Required Technique: **Context Pruning**
---

<div align="center">
  <sub>Built with ❤️ using HuggingFace · FAISS · SentenceTransformers · Flask</sub>
</div>
