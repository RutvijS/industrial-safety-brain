# Industrial Safety Brain — Phase 1

AI-powered Industrial Safety Intelligence platform. This is the **Phase 1** foundation: a FastAPI backend integrated with Google Gemini and a React + Vite frontend with a chat interface.

---

## Project Structure

```
industrial-safety-brain/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Environment variable configuration
│   │   ├── models/
│   │   │   └── chat_models.py   # Pydantic request/response models
│   │   ├── routes/
│   │   │   └── chat.py          # POST /chat endpoint
│   │   └── services/
│   │       └── gemini_service.py # Gemini API integration
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                     # Your local env (not committed)
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── ChatBox.jsx      # Chat UI component
    │   ├── pages/
    │   │   └── Home.jsx         # Home page wrapper
    │   ├── services/
    │   │   └── api.js           # Axios HTTP client
    │   ├── App.jsx              # Root component
    │   ├── App.css              # Component styles
    │   ├── index.css            # Global styles
    │   └── main.jsx             # React entry point
    ├── index.html
    └── package.json
```

---

## File Explanations

| File | Purpose |
|------|---------|
| `backend/app/main.py` | Creates the FastAPI app, configures CORS, mounts the chat router, and exposes a health-check endpoint at `GET /`. |
| `backend/app/config.py` | Loads `GEMINI_API_KEY` from `.env` using `python-dotenv`. Provides a `Settings` class with validation. |
| `backend/app/models/chat_models.py` | Defines `ChatRequest` and `ChatResponse` Pydantic models used by the `/chat` endpoint. |
| `backend/app/routes/chat.py` | Defines the `POST /chat` route. Delegates to `GeminiService` and returns the AI response. |
| `backend/app/services/gemini_service.py` | Wraps the Google Gemini SDK. Initializes the model with a safety-expert system prompt and exposes `generate_response()`. |
| `frontend/src/services/api.js` | Axios instance pointed at `localhost:8000`. Exports a `sendMessage()` helper. |
| `frontend/src/components/ChatBox.jsx` | Text input + Send button + conversation display with typing indicator and error handling. |
| `frontend/src/pages/Home.jsx` | Page wrapper that renders the header and `ChatBox`. |
| `frontend/src/App.jsx` | Root React component — renders `Home`. |

---

## Installation

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **npm 9+**
- A **Google Gemini API key** — get one at [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example .env
# Then edit .env and add your GEMINI_API_KEY
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

---

## Running the Application

### Start Backend (Terminal 1)

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**.

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

The UI will be available at **http://localhost:5173**.

---

## API Reference

### Health Check

```
GET /
```

Response:
```json
{
  "status": "ok",
  "service": "Industrial Safety Brain API"
}
```

### Chat

```
POST /chat
Content-Type: application/json

{
  "message": "What PPE is required for welding?"
}
```

Response:
```json
{
  "response": "For welding operations, the following PPE is required..."
}
```

---

## Testing Steps

1. **Health check** — Open http://localhost:8000 in a browser. You should see the JSON health response.
2. **API docs** — Open http://localhost:8000/docs to see the interactive Swagger UI.
3. **Frontend loads** — Open http://localhost:5173. You should see the SafetyBrain chat interface.
4. **Send a message** — Type a safety question and click Send. The AI response should appear below.
5. **Empty message** — Try sending an empty message. The Send button should be disabled.
6. **Backend down** — Stop the backend and send a message. An error message should appear.

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `GEMINI_API_KEY is not set` | Missing `.env` file or empty key | Copy `.env.example` to `.env` and add your API key |
| `ModuleNotFoundError: No module named 'fastapi'` | Dependencies not installed | Run `pip install -r requirements.txt` inside the virtual environment |
| `CORS error` in browser console | Backend not running or wrong port | Ensure the backend is running on port 8000 |
| `Network Error` on Send | Backend not reachable | Start the backend with `uvicorn app.main:app --reload` |
| `429 Resource Exhausted` | Gemini API rate limit | Wait a minute and retry, or check your API quota |
| Port 8000 already in use | Another process on that port | Use `uvicorn app.main:app --reload --port 8001` and update `api.js` accordingly |
