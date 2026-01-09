# TrueVail Production Deployment

## Overview
TrueVail is a comprehensive content analysis platform that detects fake news, deep fakes, and privacy risks using AI-powered analysis.

## Architecture
- **Backend**: Python Flask API running on port 5001
- **Frontend**: Static HTML/CSS/JS served via HTTP server
- **AI Integration**: Supports both Google Gemini and Ollama

## Production Requirements

### System Requirements
- Python 3.8+
- Node.js (for frontend server)
- Access to Google Gemini API or local Ollama service

### Environment Variables
Create a `.env` file in the backend directory with the following:

```env
GEMINI_API_KEY=your_google_gemini_api_key
AI_PLATFORM=gemini  # or "ollama"
OLLAMA_HOST=http://localhost:11434  # if using Ollama
OLLAMA_MODEL_TEXT=llama3.1:latest
OLLAMA_MODEL_VISION=llava:latest
NEWS_API_KEY=your_news_api_key  # optional
```

## Deployment Steps

### 1. Backend Setup
```bash
cd backend
pip install -r ../requirements_prod.txt
python app.py
```

### 2. Frontend Setup
```bash
cd frontend
npx http-server -p 3000
```

### 3. Using the Production Script
Run the batch file to start both servers:
```cmd
start_production.bat
```

## API Endpoints

### Health Checks
- `GET /health` - Service health status
- `GET /ready` - Service readiness status

### Main Endpoints
- `GET /` - Home endpoint
- `POST /analyze` - Content analysis
- `GET /trending-news` - Trending news data

## Configuration Options

### AI Platform Selection
- Set `AI_PLATFORM=gemini` to use Google Gemini
- Set `AI_PLATFORM=ollama` to use local Ollama service

### Port Configuration
- Backend runs on port 5001 by default
- Change in `backend/app.py` if needed
- Frontend typically runs on port 3000

## Security Considerations
- Use HTTPS in production
- Implement proper authentication
- Validate all inputs
- Sanitize outputs
- Monitor API usage

## Monitoring

### Health Check Endpoints
- `/health` - Basic service health
- `/ready` - Service readiness for traffic

### Logging
- All API calls are logged to `ai_debug_output.txt`
- Monitor for errors and performance issues

## Scaling Recommendations

### Horizontal Scaling
- Deploy backend behind a load balancer
- Use multiple instances for high availability
- Implement caching for repeated requests

### Performance Tuning
- Adjust timeout values in `analyzer.py`
- Optimize AI model selection based on response time
- Implement request queuing for heavy loads

## Troubleshooting

### Common Issues
1. **API Keys**: Verify all API keys are correctly configured
2. **Ports**: Check that ports 5001 and 3000 are available
3. **Dependencies**: Ensure all Python packages are installed
4. **CORS**: Backend allows all origins for development; restrict in production

### Log Files
- Check `ai_debug_output.txt` for AI service interactions
- Monitor Flask application logs

## Maintenance

### Regular Tasks
- Rotate API keys periodically
- Update dependencies
- Monitor performance metrics
- Backup configuration files

### Updates
1. Backup current deployment
2. Test changes in staging environment
3. Deploy with rolling updates if possible
4. Verify all endpoints after deployment

## Support
For production issues, check logs first and verify:
- Network connectivity
- API key validity
- Resource availability
- Service dependencies