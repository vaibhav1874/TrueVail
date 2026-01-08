// Import Firebase modules (these would normally be in a separate ES module file)
// For browser compatibility, we'll use the compat library approach

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyByDO7osyGjEueWknLcR97ScRwnnPfNjIY",
  authDomain: "truevail-583cc.firebaseapp.com",
  projectId: "truevail-583cc",
  storageBucket: "truevail-583cc.firebasestorage.app",
  messagingSenderId: "35393492710",
  appId: "1:35393492710:web:7830f492974e282ca10d27"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// Alternative modular approach functions (using compat for browser compatibility)
function signup(email, password) {
  firebase.auth().createUserWithEmailAndPassword(email, password)
    .then((userCredential) => {
      // Signed up
      const user = userCredential.user;
      console.log("Registered:", user.email);
      saveUserData(user.uid, user.email);
      alert("Account created successfully!");
      window.location.href = "dashboard.html";
    })
    .catch(err => {
      const errorCode = err.code;
      const errorMessage = err.message;
      
      // Handle specific error codes
      if (errorCode === 'auth/email-already-in-use') {
        alert('An account with this email already exists. Please try logging in instead.');
      } else if (errorCode === 'auth/invalid-email') {
        alert('Invalid email format. Please enter a valid email.');
      } else if (errorCode === 'auth/weak-password') {
        alert('Password is too weak. Please use at least 6 characters.');
      } else {
        alert(errorMessage);
      }
    });
}

// Login with Firebase
function loginWithFirebase() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  
  // Validate inputs
  if (!email || !password) {
    alert("Please enter both email and password.");
    return;
  }
  
  auth.signInWithEmailAndPassword(email, password)
    .then((userCredential) => {
      // Signed in
      const user = userCredential.user;
      console.log("Logged in:", user.email);
      window.location.href = "dashboard.html";
    })
    .catch((error) => {
      const errorCode = error.code;
      const errorMessage = error.message;
      
      // Handle specific error codes
      if (errorCode === 'auth/user-not-found') {
        alert('No account found with this email. Please register first.');
      } else if (errorCode === 'auth/wrong-password') {
        alert('Incorrect password. Please try again.');
      } else if (errorCode === 'auth/invalid-email') {
        alert('Invalid email format. Please enter a valid email.');
      } else if (errorCode === 'auth/invalid-login-credentials') {
        alert('Invalid email or password. Please check your credentials and try again.');
      } else {
        alert(`Login error: ${errorMessage}`);
      }
    });
}

// Register with Firebase (wrapper for signup function)
function registerWithFirebase() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  
  // Validate inputs
  if (!email || !password) {
    alert("Please enter both email and password.");
    return;
  }
  
  if (password.length < 6) {
    alert("Password must be at least 6 characters long.");
    return;
  }
  
  // Call signup with success callback to redirect after registration
  firebase.auth().createUserWithEmailAndPassword(email, password)
    .then((userCredential) => {
      // Signed up
      const user = userCredential.user;
      console.log("Registered:", user.email);
      saveUserData(user.uid, user.email);
      window.location.href = "dashboard.html";
    })
    .catch((error) => {
      const errorCode = error.code;
      const errorMessage = error.message;
      
      // Handle specific error codes
      if (errorCode === 'auth/email-already-in-use') {
        alert('An account with this email already exists. Please try logging in instead.');
      } else if (errorCode === 'auth/invalid-email') {
        alert('Invalid email format. Please enter a valid email.');
      } else if (errorCode === 'auth/weak-password') {
        alert('Password is too weak. Please use at least 6 characters.');
      } else {
        alert(`Registration error: ${errorMessage}`);
      }
    });
}

// Save user data to Firestore
function saveUserData(userId, email) {
  db.collection("users").doc(userId).set({
    email: email,
    joinedAt: firebase.firestore.FieldValue.serverTimestamp()
  });
}

// Save analysis result to Firestore
function saveAnalysisResult(userId, type, content, result) {
  if (typeof db !== 'undefined') {
    db.collection("analysis_results").add({
      userId: userId,
      type: type, // 'news', 'privacy', 'deepfake'
      content: content,
      result: result,
      createdAt: firebase.firestore.FieldValue.serverTimestamp()
    }).catch((error) => {
      console.error("Error saving analysis result: ", error);
    });
  }
}

// Get user's analysis history
function getAnalysisHistory(userId, callback) {
  db.collection("analysis_results")
    .where("userId", "==", userId)
    .orderBy("createdAt", "desc")
    .limit(10)
    .get()
    .then((querySnapshot) => {
      const history = [];
      querySnapshot.forEach((doc) => {
        history.push({
          id: doc.id,
          ...doc.data()
        });
      });
      callback(history);
    })
    .catch((error) => {
      console.error("Error getting history: ", error);
    });
}

// Logout from Firebase
function logoutFromFirebase() {
  auth.signOut().then(() => {
    console.log("Signed out");
    window.location.href = "login.html";
  }).catch((error) => {
    console.error("Sign out error:", error);
  });
}

// Google sign-in
function signInWithGoogle() {
  const provider = new firebase.auth.GoogleAuthProvider();
  auth.signInWithPopup(provider)
    .then((result) => {
      // Signed in with Google
      const user = result.user;
      console.log("Google sign in:", user.email);
      saveUserData(user.uid, user.email);
      window.location.href = "dashboard.html";
    })
    .catch((error) => {
      const errorCode = error.code;
      const errorMessage = error.message;
      alert(`Error: ${errorMessage}`);
    });
}

// GitHub sign-in
function signInWithGithub() {
  const provider = new firebase.auth.GithubAuthProvider();
  auth.signInWithPopup(provider)
    .then((result) => {
      // Signed in with GitHub
      const user = result.user;
      console.log("GitHub sign in:", user.email || user.displayName);
      // GitHub users might not have email accessible
      saveUserData(user.uid, user.email || user.displayName);
      window.location.href = "dashboard.html";
    })
    .catch((error) => {
      const errorCode = error.code;
      const errorMessage = error.message;
      alert(`Error: ${errorMessage}`);
    });
}

// Check auth state
auth.onAuthStateChanged((user) => {
  if (user) {
    // User is signed in
    if (window.location.pathname.includes("login.html")) {
      window.location.href = "dashboard.html";
    }
  } else {
    // User is signed out
    if (window.location.pathname.includes("dashboard.html")) {
      window.location.href = "login.html";
    }
  }
});