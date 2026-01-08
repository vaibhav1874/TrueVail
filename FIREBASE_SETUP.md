# Firebase Setup Guide

This project uses Firebase for authentication and data storage. Follow these steps to configure Firebase:

## 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add Project" or "Create a project"
3. Enter your project name and follow the setup wizard
4. Agree to the terms and click "Create Project"

## 2. Enable Authentication Methods

1. In Firebase Console, go to "Authentication" in the left sidebar
2. Click "Get Started"
3. Go to "Sign-in method" tab
4. Enable "Email/Password" provider
5. Also enable "Google" and "GitHub" providers if you want social login

## 3. Configure Firestore Database

1. In Firebase Console, go to "Firestore Database" in the left sidebar
2. Click "Create Database"
3. Choose your security rules (start with "test mode" for development)
4. Set up the rules as needed for production

## 4. Get Your Firebase Config

1. In Firebase Console, go to Project Settings (gear icon)
2. Scroll down to "Your apps" section
3. Copy the Firebase config object values:
   - apiKey
   - authDomain
   - projectId
   - storageBucket
   - messagingSenderId
   - appId

## 5. Update Firebase Configuration

1. Open `frontend/firebase-config.js`
2. Replace the placeholder values in the `firebaseConfig` object with your actual values:

```javascript
const firebaseConfig = {
  apiKey: "your-actual-api-key",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "your-sender-id",
  appId: "your-app-id"
};
```

## 6. Enable Firestore Security Rules

For development, you can use these basic rules in Firestore Database > Rules:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{document} {
      allow read, write: if request.auth != null;
    }
    match /analysis_results/{document} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.userId;
    }
  }
}
```

For production, you'll want to customize these rules based on your specific security requirements.

## 7. Deploy

After updating the configuration, your Firebase integration will be ready to use.