# Deploying TrueVail on Vercel

## Architecture Overview

TrueVail is a two-part application:
- **Frontend**: Static HTML/CSS/JS files (can be deployed on Vercel)
- **Backend**: Python Flask API (requires a server with Python support)

## Deployment Strategy

Since Vercel doesn't natively support Python Flask applications, we'll deploy:

1. **Frontend** on Vercel (static files)
2. **Backend** on a Python-compatible platform (Heroku, PythonAnywhere, AWS, etc.)

## Frontend Deployment on Vercel

### Step 1: Prepare Frontend for Vercel
The frontend is located in the `frontend/` directory and consists of static files:
- `index.html` - Landing page
- `login.html` - Authentication page
- `dashboard.html` - Main application interface
- `app.js` - Client-side JavaScript
- `style.css` - Styling
- `firebase-config.js` - Firebase configuration

### Step 2: Update API Endpoint
Before deploying, you need to update the frontend to point to your hosted backend API.

In `frontend/app.js`, update the API endpoints to point to your backend URL:
```javascript
// Change from:
const BACKEND_URL = 'http://localhost:5001';

// To your deployed backend URL:
const BACKEND_URL = 'https://your-backend-domain.com';
```

### Step 3: Deploy to Vercel
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project" and connect to your GitHub repository
3. Select the TrueVail repository
4. In the configuration:
   - Framework Preset: `Other`
   - Build Command: `cd frontend && echo "Frontend ready"`
   - Output Directory: `frontend`
   - Root Directory: `.` (or specify the frontend directory)

Or use the Vercel CLI:
```bash
npm install -g vercel
cd frontend
vercel --public
```

## Backend Deployment Alternative Options

Since Vercel doesn't support Python Flask, deploy the backend elsewhere:

### Option 1: Heroku
1. Create a `Procfile` in the backend directory:
   ```
   web: gunicorn app:app
   ```
2. Create `runtime.txt` to specify Python version:
   ```
   python-3.11.0
   ```
3. Update `requirements.txt` with gunicorn:
   ```
   flask==3.0.3
   gunicorn==21.2.0
   requests==2.31.0
   beautifulsoup4==4.12.2
   python-dotenv==1.0.0
   google-generativeai==0.8.4
   ```
4. Deploy to Heroku using Git

### Option 2: PythonAnywhere
1. Create account on PythonAnywhere
2. Upload backend files
3. Set up a web app with Flask
4. Configure environment variables

### Option 3: AWS Elastic Beanstalk
1. Package backend files
2. Create requirements.txt
3. Deploy as Python application

## Configuration for Separated Deployment

### Update Frontend API Calls
When backend is deployed separately, update the API endpoints in the frontend to use the full URL:

In `frontend/app.js`, change:
```javascript
fetch("/analyze", {  // This won't work when frontend is on different domain
```

To:
```javascript
fetch("https://your-backend-domain.com/analyze", {  // Full URL
```

### CORS Configuration
The backend needs to allow requests from your Vercel domain:
In the backend `app.py`, update CORS to include your Vercel URL:
```python
CORS(app, resources={r"/*": {"origins": ["https://your-vercel-url.vercel.app", "http://localhost:3000"]}})
```

## Deployment Checklist

### Before Deploying Frontend to Vercel:
- [ ] Update API endpoints in frontend to point to deployed backend
- [ ] Test CORS configuration on backend
- [ ] Verify environment variables are set on backend
- [ ] Confirm backend is accessible from public internet
- [ ] Test API calls with full URLs

### After Deploying:
- [ ] Verify frontend loads correctly on Vercel URL
- [ ] Test all functionality with deployed backend
- [ ] Confirm fake news detection works
- [ ] Verify text-to-speech functionality
- [ ] Test trending news feature

## Important Notes

1. **Separate Domains**: Frontend and backend will be on different domains, so CORS must be properly configured.

2. **API Keys**: Keep API keys secure on the backend server, not in frontend code.

3. **SSL/HTTPS**: Both frontend and backend should be served over HTTPS for security.

4. **Rate Limiting**: Consider implementing rate limiting on the backend API.

5. **Monitoring**: Set up monitoring for both frontend and backend separately.

## Example Configuration

Once deployed:
- Frontend: `https://your-project-name.vercel.app`
- Backend: `https://your-backend-app.herokuapp.com` (or similar)

The frontend will make API calls to the backend domain while being served from Vercel.