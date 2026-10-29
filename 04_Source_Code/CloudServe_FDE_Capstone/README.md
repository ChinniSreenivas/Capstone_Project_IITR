# CloudServe Support Automation — Webpage

Responsive blue-and-white support portal for your existing FastAPI service.

Features:
- Ticket submission to `POST http://127.0.0.1:8000/tickets`
- Display of intent, confidence, routing action, suggested answer, and citations
- Session-only dashboard metrics and recent ticket activity
- API connection status from `GET /health`

## 1. Enable CORS in your backend

The webpage uses port 5500 and the API uses port 8000, so the browser needs CORS permission.

In your existing `src/api.py`, add this import with the other imports:

```python
from fastapi.middleware.cors import CORSMiddleware
```

Immediately after the `app = FastAPI(...)` line, add:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

Save the file and restart Uvicorn. This allowlist is for local development only.

## 2. Start the API

Open Command Prompt in your existing project folder and run:

```bat
.venv\Scripts\activate
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Keep this terminal open. Check `http://127.0.0.1:8000/health`.

## 3. Start the webpage

Open a second Command Prompt, change directory into this package's `frontend` folder, and run:

```bat
py -3.11 -m http.server 5500 --bind 127.0.0.1
```

Open `http://127.0.0.1:5500`.

## 4. Test

Fill out the subject and body and click **Submit ticket**. Review the returned classification, routing decision, answer, and citations. The dashboard metrics count only tickets submitted from this webpage during the current page session; they are not database-backed historical metrics.

This is a local capstone demo, not an authenticated production portal.
