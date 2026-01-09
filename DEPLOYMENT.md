
# TrueVail Production Deployment Guide

## Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

## Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TrueVail
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements_prod.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. Start the application:
   ```bash
   cd backend
   python app.py
   ```

## Environment Variables

Required:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `AI_PLATFORM`: Either "gemini" or "ollama"

Optional:
- `OLLAMA_HOST`: Ollama host URL (default: http://localhost:11434)
- `OLLAMA_MODEL_TEXT`: Text model name (default: llama3.1:latest)
- `OLLAMA_MODEL_VISION`: Vision model name (default: llava:latest)
- `NEWS_API_KEY`: News API key for trending news (optional)

## Services

- Backend API: http://localhost:5001
- Frontend: Serve the frontend directory with a web server

## Production Notes

- Disable debug mode in production
- Use a production WSGI server (Gunicorn, uWSGI) instead of Flask dev server
- Set up proper logging
- Implement proper security measures
- Use HTTPS in production
