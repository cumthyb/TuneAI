# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TuneAI is a "printed simplified Chinese numeral notation (jianpu) intelligent transposition" tool. Users upload a jianpu score image, select a target key, and the backend uses Vision LLM + OCR + validation pipeline to transpose the score while preserving the original layout.

- **Frontend**: React + TypeScript + Tailwind CSS + Vite (SPA)
- **Backend**: FastAPI + Python, single-port deployment (serves both frontend and API)
- **Pipeline**: Image preprocessing → Vision LLM key detection + OCR (parallel) → filtering → transposition → validation → rendering

## Common Commands

```bash
# Install all dependencies (frontend npm + backend poetry)
make install

# Build frontend and start backend dev server (reload enabled)
make dev

# Build frontend and start backend prod server (reload disabled)
make prod

# Frontend dev server only (Vite on port from config.json)
make web

# Build frontend only (outputs to frontend/dist)
make build

# Run all unit tests (external engines mocked)
make test

# Run integration tests (requires real OCR model + LLM)
make test-int

# Run OCR integration test only (data/samples/匆匆那年.png → real OCR API)
make test-ocr

# Run preprocessing test only (no external services needed)
make test-preprocess

# Frontend lint
make lint
```

## Architecture

### Backend Structure

```
backend/tuneai/
├── main.py                    # FastAPI app entry, serves frontend/dist
├── api/routes.py              # GET /api/meta, POST /api/transpose
├── config.py                  # Loads config.json, env var overrides
├── logging_config.py          # loguru + request_id context
├── core/
│   ├── application/
│   │   └── pipeline.py        # Main pipeline orchestrator (run_pipeline)
│   ├── domain/                # Core business logic
│   │   ├── preprocess.py      # Image normalization, deskew
│   │   ├── filter.py          # Filter OCR results to notes 0-7
│   │   ├── music.py           # Key transposition, 12-TET
│   │   ├── render.py          # OpenCV/Pillow render new numerals
│   │   └── validate.py        # Rule → LLM text → VL visual validation
│   ├── adapters/              # External service adapters
│   │   ├── llm_client.py      # LangChain ChatOpenAI wrapper
│   │   ├── vision.py          # Vision LLM adapter
│   │   └── ocr/               # OCR providers (qwen, glm, minimax, etc.)
│   └── infra/
│       └── storage.py         # Temp file management
└── schemas/
    ├── request_response.py    # API request/response Pydantic models
    └── score_ir.py            # Score IR (measures, events, key)
```

### Pipeline Flow

```
preprocess (local)
       ↓
vision_llm + ocr (parallel, online)
       ↓
filter → music (transpose) → validate → render (local)
```

### Frontend Structure

```
frontend/src/
├── App.tsx                    # Root component
├── hooks/useTranspose.ts      # Main state machine: upload, /api/meta poll, /api/transpose
├── components/
│   ├── Upload.tsx             # Image upload, target key selection
│   ├── LoadingState.tsx        # Processing spinner, error display
│   ├── ResultViewer.tsx        # Before/after comparison, warnings
│   └── DownloadPanel.tsx       # Download image/JSON, request_id
└── types/api.ts               # TypeScript types for API contracts
```

## Configuration

- `config.json` at project root (gitignored) — copy from `config.example.json`
- Environment variables override config.json (e.g., `TUNEAI_LLM_API_KEY`, `TUNEAI_PROVIDER`)
- Backend Python path is `backend/` (set via `PYTHONPATH=backend` in Makefile)

## Testing

- Unit tests mock all external services (OCR, LLM, VL)
- `tests/` mirrors backend structure: `adapters/`, `application/`, `domain/`, `infra/`, `api/`, `config/`
- Run single test: `pytest tests/domain/test_music.py -v`

## Provider System

Providers are registered in `config.json` under `providers`. Each provider has:
- `llm`: Text LLM config
- `vision_llm`: Vision LLM config
- `ocr`: OCR config with dynamic `runner` (e.g., `tuneai.core.adapters.ocr.providers.qwen:run_qwen_ocr`)
