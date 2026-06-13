# LEO 🐐 - Your AI Coding Agent

Welcome to LEO! This project is an AI coding assistant that uses a modern web stack to let you chat with the Google Gemini API.

## 🚀 Today's Progress (Day 1)

1. **Project Scaffolded:**
   - Created the root workspace.
   - Initialized a Git repository.
   - Created the `sandbox` folder for experiments.

2. **Frontend Setup (Next.js):**
   - Bootstrapped a new Next.js app with Tailwind CSS.
   - Built a sleek, dark-themed chat interface.
   - Wired up the UI to send requests to our backend API.

3. **Backend Setup (FastAPI):**
   - Created a Python virtual environment and installed dependencies (FastAPI, Uvicorn, Google Generative AI).
   - Created `main.py` with a `/chat` POST endpoint.
   - Integrated the `gemini-2.5-flash` model.
   - Configured CORS so the frontend (`localhost:3000` / `localhost:3001`) can seamlessly communicate with the backend (`localhost:8000`).

## 🛠️ Tech Stack

- **Frontend:** Next.js (App Router), React, Tailwind CSS
- **Backend:** Python, FastAPI, Uvicorn
- **AI Model:** Google Gemini (`gemini-2.5-flash`)

## 🏃‍♂️ How to Run Locally

### 1. Start the Backend
Open a terminal and run the following commands from the root of the project:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```
*Make sure you have a `.env` file inside the `backend/` folder containing your `GEMINI_API_KEY=...`*

### 2. Start the Frontend
Open a new terminal tab and run:
```bash
cd frontend
npm run dev
```
Navigate to `http://localhost:3000` (or `3001` if 3000 is occupied) in your browser to chat with LEO!
