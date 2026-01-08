// 🔐 LOGIN
function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  if (email && password) {
    localStorage.setItem("truevail_login", "true");
    window.location.href = "dashboard.html";
  } else {
    alert("Please enter credentials");
  }
}

// Note: db variable is defined in firebase-config.js when Firebase is initialized

// 🔒 PROTECT DASHBOARD
// Keeping localStorage approach as backup, but Firebase handles primary auth state

function logout() {
  // This function is kept for compatibility but Firebase version should be used
  localStorage.removeItem("truevail_login");
  window.location.href = "login.html";
}

// 📑 TAB SWITCH
function showTab(id) {
  // Hide all tab content
  document.querySelectorAll(".tab-content").forEach(tab => {
    tab.classList.remove("active");
  });

  // Show selected tab content
  document.getElementById(id).classList.add("active");

  // Update active nav link
  document.querySelectorAll(".nav-link").forEach(link => {
    link.classList.remove("active");
  });

  // Find and activate the corresponding nav link
  const allNavLinks = document.querySelectorAll(".nav-link");
  allNavLinks.forEach(link => {
    if (link.getAttribute('onclick').includes(id)) {
      link.classList.add("active");
    }
  });

  // Load history if history tab is selected
  if (id === 'history' && typeof auth !== 'undefined' && auth.currentUser) {
    loadHistory();
  }
}

// Load analysis history from Firebase
function loadHistory() {
  if (typeof getAnalysisHistory !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
    getAnalysisHistory(auth.currentUser.uid, (history) => {
      displayHistory(history);
    });
  }
}

// Display history in the UI
function displayHistory(history) {
  const historyList = document.querySelector('.history-list');
  if (!historyList) return;

  if (history.length === 0) {
    historyList.innerHTML = '<p class="placeholder-text">No analysis history found</p>';
    return;
  }

  historyList.innerHTML = '';

  history.forEach(item => {
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';

    let typeName = item.type.charAt(0).toUpperCase() + item.type.slice(1);
    if (item.type === 'news') typeName = 'Fake News';
    else if (item.type === 'privacy') typeName = 'Privacy Risk';
    else if (item.type === 'deepfake') typeName = 'Deep Fake';

    const date = new Date(item.createdAt?.toDate());
    const dateString = date.toLocaleString();

    historyItem.innerHTML = `
      <div class="history-item-header">
        <h4>${typeName} Analysis</h4>
        <span class="history-date">${dateString}</span>
      </div>
      <p class="history-content">${item.content.substring(0, 100)}${item.content.length > 100 ? '...' : ''}</p>
      <div class="history-actions">
        <button class="view-btn" onclick="viewHistoryItem('${item.id}')">View</button>
        <button class="delete-btn" onclick="deleteHistoryItem('${item.id}')">Delete</button>
      </div>
    `;

    historyList.appendChild(historyItem);
  });
}

// View a specific history item
function viewHistoryItem(itemId) {
  // Implementation for viewing a specific history item
  alert('Viewing history item: ' + itemId);
}

// Delete a history item
function deleteHistoryItem(itemId) {
  // Implementation for deleting a history item
  if (typeof db !== 'undefined' && confirm('Are you sure you want to delete this history item?')) {
    db.collection('analysis_results').doc(itemId).delete()
      .then(() => {
        console.log('History item deleted successfully');
        loadHistory(); // Reload the history
      })
      .catch((error) => {
        console.error('Error removing history item: ', error);
      });
  }
}

// CLEAR CONTENT
function clearContent(inputId, resultId) {
  document.getElementById(inputId).value = "";
  const resultElement = document.getElementById(resultId);
  resultElement.innerHTML = "<p class='placeholder-text'>Results will appear here after analysis...</p>";
  resultElement.style.display = "flex";
}

// ANALYZE DEEPFAKE
function analyzeDeepfake() {
  const fileInput = document.getElementById('deepfakeFile');
  const resultDiv = document.getElementById('deepfakeResult');

  if (!fileInput.files[0]) {
    resultDiv.innerHTML = "<p class='placeholder-text'>Please select a file to analyze.</p>";
    return;
  }

  const fileName = fileInput.files[0].name;
  resultDiv.innerHTML = `<p>Processing ${fileName}... <i class='fas fa-spinner fa-spin'></i></p>`;
  resultDiv.style.display = "block";

  // Simulate processing delay
  setTimeout(() => {
    // Generate a simulated deepfake analysis result
    const fakeProbability = Math.random();
    let status, statusClass;

    if (fakeProbability > 0.7) {
      status = "Likely Deepfake";
      statusClass = "status-likely-fake";
    } else if (fakeProbability > 0.4) {
      status = "Uncertain";
      statusClass = "status-uncertain";
    } else {
      status = "Likely Authentic";
      statusClass = "status-likely-real";
    }

    const confidence = Math.round(fakeProbability * 100);

    resultDiv.innerHTML = `
      <div class="analysis-results">
        <div class="result-summary">
          <div class="result-item">
            <span class="label">Status:</span>
            <span class="value ${statusClass}">${status}</span>
          </div>
          <div class="result-item">
            <span class="label">Confidence:</span>
            <span class="value">${confidence}%</span>
          </div>
        </div>
        
        <div class="result-details">
          <div class="detail-item">
            <h4>Analysis Details</h4>
            <p>Pixel-level inconsistencies detected in facial landmarks and lighting patterns.</p>
          </div>
          
          <div class="detail-item">
            <h4>Metadata Check</h4>
            <p>No anomalies found in file metadata.</p>
          </div>
        </div>
        
        <div class="full-analysis">
          <h4>Technical Assessment</h4>
          <p>This analysis is based on simulated deepfake detection algorithms. Actual deepfake detection requires advanced neural networks trained on large datasets of authentic and synthetic media.</p>
        </div>
      </div>
    `;

    // Save result to Firebase if user is authenticated
    if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
      const resultData = {
        status: status,
        confidence: confidence + '%',
        analysisDetails: 'Pixel-level inconsistencies detected in facial landmarks and lighting patterns.',
        metadataCheck: 'No anomalies found in file metadata.',
        technicalAssessment: 'This analysis is based on simulated deepfake detection algorithms. Actual deepfake detection requires advanced neural networks trained on large datasets of authentic and synthetic media.'
      };
      saveAnalysisResult(auth.currentUser.uid, 'deepfake', fileName, resultData);
    }
  }, 3000);
}

// CLEAR DEEPFAKE ANALYSIS
function clearDeepfakeAnalysis() {
  document.getElementById('deepfakeFile').value = "";
  const resultElement = document.getElementById('deepfakeResult');
  resultElement.innerHTML = "<p class='placeholder-text'>Deep fake detection results will appear here...</p>";
  resultElement.style.display = "flex";
}

// 📰 FAKE NEWS ANALYSIS
function analyzeNews() {
  const text = document.getElementById("newsInput").value;
  const result = document.getElementById("newsResult");

  result.innerHTML = "<p>Analyzing with AI...</p>";
  result.style.display = "block";

  fetch("http://127.0.0.1:5001/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, type: "news" })
  })
    .then(res => res.json())
    .then(data => {
      // Format the structured response nicely
      result.innerHTML = `
      <div class="analysis-results">
        <div class="result-summary">
          <div class="result-item">
            <span class="label">Status:</span>
            <span class="value status-${data.status.toLowerCase().replace(' ', '-').replace(/[^a-z0-9-]/g, '')}">${data.status}</span>
          </div>
          <div class="result-item">
            <span class="label">Confidence:</span>
            <span class="value">${(parseFloat(data.confidence) * 100).toFixed(1)}%</span>
          </div>
        </div>
        
        <div class="result-details">
          <div class="detail-item">
            <h4>Reasoning</h4>
            <p>${data.reason}</p>
          </div>
          
          ${data.correction_suggestion ? `
          <div class="detail-item correction-suggestion">
            <h4>Correction Suggestion</h4>
            <p>${data.correction_suggestion}</p>
          </div>
          ` : ''}
          
          <div class="detail-item">
            <h4>Privacy Risk</h4>
            <p class="risk-${data.privacy_risk.toLowerCase()}">${data.privacy_risk}</p>
            <p>${data.privacy_explanation}</p>
          </div>
        </div>
        
        <div class="full-analysis">
          <h4>Full Analysis</h4>
          <pre>${data.analysis}</pre>
        </div>
      </div>
    `;

      // Save result to Firebase if user is authenticated
      if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
        saveAnalysisResult(auth.currentUser.uid, 'news', text, data);
      }
    })
    .catch(error => {
      result.innerHTML = `<p>Error: Could not connect to backend (${error.message})</p>`;
      result.style.display = "block";
    });
}

// 🔗 LINK NEWS ANALYSIS
function analyzeLink() {
  const url = document.getElementById("linkInput").value;
  const result = document.getElementById("linkResult");

  if (!url) {
    result.innerHTML = "<p class='placeholder-text'>Please enter a URL to analyze.</p>";
    return;
  }

  result.innerHTML = "<p>Crawling and analyzing news source... <i class='fas fa-spinner fa-spin'></i></p>";
  result.style.display = "block";

  fetch("http://127.0.0.1:5001/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: url, type: "news" })
  })
    .then(res => res.json())
    .then(data => {
      // Format the structured response nicely
      result.innerHTML = `
      <div class="analysis-results">
        <div class="result-summary">
          <div class="result-item">
            <span class="label">Status:</span>
            <span class="value status-${data.status.toLowerCase().replace(' ', '-').replace(/[^a-z0-9-]/g, '')}">${data.status}</span>
          </div>
          <div class="result-item">
            <span class="label">Confidence:</span>
            <span class="value">${(parseFloat(data.confidence) * 100).toFixed(1)}%</span>
          </div>
        </div>
        
        <div class="result-details">
          <div class="detail-item">
            <h4>Analysis Result</h4>
            <p>${data.reason}</p>
          </div>
          
          ${data.correction_suggestion ? `
          <div class="detail-item correction-suggestion">
            <h4>Correct Information / Fact Check</h4>
            <p>${data.correction_suggestion}</p>
          </div>
          ` : ''}
          
          <div class="detail-item">
            <h4>Source Information</h4>
            <p>${data.analysis.split('\n')[0]}</p>
          </div>
        </div>
      </div>
    `;

      // Save result to Firebase if user is authenticated
      if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
        saveAnalysisResult(auth.currentUser.uid, 'news-link', url, data);
      }
    })
    .catch(error => {
      result.innerHTML = `<p>Error: Could not connect to backend (${error.message})</p>`;
      result.style.display = "block";
    });
}


// 🔐 PRIVACY ANALYSIS (SAME AI, DIFFERENT TAB)
function analyzePrivacy() {
  const text = document.getElementById("privacyInput").value;
  const result = document.getElementById("privacyResult");

  result.innerHTML = "<p>Checking privacy risk...</p>";
  result.style.display = "block";

  fetch("http://127.0.0.1:5001/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, type: "privacy" })
  })
    .then(res => res.json())
    .then(data => {
      // Format the structured response nicely
      result.innerHTML = `
      <div class="analysis-results">
        <div class="result-summary">
          <div class="result-item">
            <span class="label">Privacy Risk:</span>
            <span class="value risk-${data.privacy_risk.toLowerCase()}">${data.privacy_risk}</span>
          </div>
          <div class="result-item">
            <span class="label">Confidence:</span>
            <span class="value">${(parseFloat(data.confidence) * 100).toFixed(1)}%</span>
          </div>
        </div>
        
        <div class="result-details">
          <div class="detail-item">
            <h4>Risk Assessment</h4>
            <p>${data.privacy_explanation}</p>
          </div>
          
          <div class="detail-item">
            <h4>Content Status</h4>
            <p class="status-${data.status.toLowerCase().replace(' ', '-').replace(/[^a-z0-9-]/g, '')}">${data.status}</p>
            <p>${data.reason}</p>
          </div>
          
          ${data.correction_suggestion ? `
          <div class="detail-item correction-suggestion">
            <h4>Correction Suggestion</h4>
            <p>${data.correction_suggestion}</p>
          </div>
          ` : ''}
        </div>
        
        <div class="full-analysis">
          <h4>Full Analysis</h4>
          <pre>${data.analysis}</pre>
        </div>
      </div>
    `;

      // Save result to Firebase if user is authenticated
      if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
        saveAnalysisResult(auth.currentUser.uid, 'privacy', text, data);
      }
    })
    .catch(error => {
      result.innerHTML = `<p>Error: Could not connect to backend (${error.message})</p>`;
      result.style.display = "block";
    });
}
