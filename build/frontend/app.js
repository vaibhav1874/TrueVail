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

// 🔒 PROTECT DASHBOARD
// Standalone mode - no Firebase authentication required

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
  if (id === 'history') {
    if (typeof auth !== 'undefined' && auth.currentUser) {
      loadHistory();
    } else {
      // In standalone mode, show a message that history requires login
      console.log('History tab selected - requires authentication in full version');
    }
  }
  
  // Load trending news if trending news tab is selected
  if (id === 'trending-news') {
    // Small delay to ensure the tab is fully rendered and visible
    setTimeout(() => {
      loadTrendingNews();
    }, 50);
  }
}

// Load analysis history
function loadHistory() {
  if (typeof getAnalysisHistory !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
    getAnalysisHistory(auth.currentUser.uid, (history) => {
      displayHistory(history);
    });
  } else {
    // In standalone mode, show a message
    const historyList = document.querySelector('.history-list');
    if (historyList) {
      historyList.innerHTML = '<p class="placeholder-text">Analysis history requires authentication in full version</p>';
    }
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
  } else {
    // In standalone mode, show a message
    alert('Deleting history items requires authentication in full version');
  }
}

// Load trending news when the tab is shown
function loadTrendingNews() {
  const newsList = document.getElementById('trending-news-list');
  if (!newsList) return;
  
  newsList.innerHTML = '<p class="placeholder-text">Loading trending news...</p>';
  
  console.log('Attempting to fetch trending news from: http://localhost:5001/trending-news');
  
  fetch('http://localhost:5001/trending-news')
    .then(response => {
      console.log('Response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Received data:', data);
      if (data.status === 'success') {
        displayTrendingNews(data);
        // Wait for the tab to be visible and then render charts
        setTimeout(() => {
          // Ensure the tab is visible before rendering
          const tab = document.getElementById('trending-news');
          if (tab && tab.classList.contains('active')) {
            renderCharts(data);
          } else {
            // If tab is not active yet, wait a bit more
            setTimeout(() => {
              renderCharts(data);
            }, 200);
          }
        }, 100);
      } else {
        newsList.innerHTML = `<p class="placeholder-text">Error loading trending news: ${data.message || 'Unknown error'}</p>`;
      }
    })
    .catch(error => {
      console.error('Error fetching trending news:', error);
      newsList.innerHTML = `<p class="placeholder-text">Failed to load trending news: ${error.message}. Please ensure the backend server is running on port 5001. You may need to check CORS settings or try accessing the backend directly at http://localhost:5001/trending-news.</p>`;
    });
}

// Display trending news in the UI
function displayTrendingNews(data) {
  const newsList = document.getElementById('trending-news-list');
  if (!newsList) return;
  
  if (!data.trending_news || data.trending_news.length === 0) {
    newsList.innerHTML = '<p class="placeholder-text">No trending news available at the moment.</p>'; 
    return;
  }
  
  let newsHTML = '';
  data.trending_news.forEach(article => {
    try {
      const date = new Date(article.published_at);
      // Check if date is valid
      const formattedDate = !isNaN(date.getTime()) ? date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) + ' ago' : 'Just now';
      
      newsHTML += `
        <div class="news-item">
          <h4>${article.title}</h4>
          <p>${article.description}</p>
          <div class="news-source">
            <span>${article.source}</span>
            <span class="news-date">${formattedDate}</span>
          </div>
        </div>
      `;
    } catch (e) {
      console.error('Error processing article:', article, e);
      // Add a fallback entry
      newsHTML += `
        <div class="news-item">
          <h4>${article.title || 'Untitled'}</h4>
          <p>${article.description || 'No description'}</p>
          <div class="news-source">
            <span>${article.source || 'Unknown source'}</span>
            <span class="news-date">Just now</span>
          </div>
        </div>
      `;
    }
  });
  
  newsList.innerHTML = newsHTML;
}

// Render charts using Chart.js
function renderCharts(data) {
  try {
    // Store the data globally so individual chart functions can access it
    window.currentTrendsData = data;
    
    // Render Topics Chart
    if (data.trends && data.trends.categories && data.trends.popularity) {
      renderTopicsChart(data.trends.categories, data.trends.popularity);
    }
    
    // Render Categories Chart
    if (data.preferences && data.preferences.most_read_categories) {
      renderCategoriesChart(data.preferences.most_read_categories);
    }
    
    // Render Preferences Chart
    if (data.preferences && data.preferences.reading_time_distribution) {
      renderPreferencesChart(data.preferences.reading_time_distribution);
    }
  } catch (e) {
    console.error('Error rendering charts:', e);
  }
}

// Render Topics Chart
function renderTopicsChart(categories, popularity) {
  try {
    const canvas = document.getElementById('topicsChart');
    if (!canvas) {
      console.error('Topics chart canvas element not found');
      return;
    }
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.topicsChart) {
      window.topicsChart.destroy();
    }
    
    window.topicsChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: categories,
        datasets: [{
          label: 'Popularity (%)',
          data: popularity,
          backgroundColor: [
            '#6366f1',
            '#8b5cf6',
            '#ec4899',
            '#f43f5e',
            '#f59e0b',
            '#10b981'
          ],
          borderColor: [
            'rgba(99, 102, 241, 1)',
            'rgba(139, 92, 246, 1)',
            'rgba(236, 72, 153, 1)',
            'rgba(244, 63, 94, 1)',
            'rgba(245, 158, 11, 1)',
            'rgba(16, 185, 129, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          title: {
            display: true,
            text: 'News Topic Popularity',
            color: '#e5e7eb',
            font: {
              size: 14
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              color: '#94a3b8'
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.1)'
            }
          },
          x: {
            ticks: {
              color: '#94a3b8',
              maxRotation: 45,
              minRotation: 45
            },
            grid: {
              display: false
            }
          }
        }
      }
    });
    
    // Force resize to ensure proper rendering when tab becomes visible
    setTimeout(() => {
      if (window.topicsChart) {
        window.topicsChart.resize();
      }
    }, 100);
  } catch (e) {
    console.error('Error rendering topics chart:', e);
  }
}

// Render Categories Chart
function renderCategoriesChart(categories) {
  try {
    const canvas = document.getElementById('categoriesChart');
    if (!canvas) {
      console.error('Categories chart canvas element not found');
      return;
    }
    const ctx = canvas.getContext('2d');
    
    // Get the actual popularity data from the trends section
    const allCategories = window.currentTrendsData?.trends?.categories || [];
    const allPopularity = window.currentTrendsData?.trends?.popularity || [];
    
    // Find the popularity values for the top 3 categories
    const popularityValues = categories.map(cat => {
      const index = allCategories.findIndex(c => c.toLowerCase() === cat.toLowerCase());
      return index !== -1 ? allPopularity[index] : 10; // Default to 10 if not found
    });
    
    // Destroy existing chart if it exists
    if (window.categoriesChart) {
      window.categoriesChart.destroy();
    }
    
    window.categoriesChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: categories,
        datasets: [{
          data: popularityValues,
          backgroundColor: [
            '#6366f1',
            '#8b5cf6',
            '#ec4899'
          ],
          borderColor: [
            '#6366f1',
            '#8b5cf6',
            '#ec4899'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#e5e7eb',
              padding: 20
            }
          },
          title: {
            display: true,
            text: 'Most Read Categories',
            color: '#e5e7eb',
            font: {
              size: 14
            }
          }
        }
      }
    });
    
    // Force resize to ensure proper rendering when tab becomes visible
    setTimeout(() => {
      if (window.categoriesChart) {
        window.categoriesChart.resize();
      }
    }, 100);
  } catch (e) {
    console.error('Error rendering categories chart:', e);
  }
}

// Render Preferences Chart
function renderPreferencesChart(timeDistribution) {
  try {
    const canvas = document.getElementById('preferencesChart');
    if (!canvas) {
      console.error('Preferences chart canvas element not found');
      return;
    }
    const ctx = canvas.getContext('2d');
    
    // Define time labels
    const timeLabels = ['Morning', 'Afternoon', 'Evening', 'Night', 'Late Night'];
    
    // Destroy existing chart if it exists
    if (window.preferencesChart) {
      window.preferencesChart.destroy();
    }
    
    window.preferencesChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: timeLabels,
        datasets: [{
          label: 'Reading Time Distribution (%)',
          data: timeDistribution,
          fill: false,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.2)',
          tension: 0.3,
          pointBackgroundColor: '#8b5cf6',
          pointBorderColor: '#fff',
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#e5e7eb'
            }
          },
          title: {
            display: true,
            text: 'News Reading Time Preferences',
            color: '#e5e7eb',
            font: {
              size: 14
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 35,
            ticks: {
              color: '#94a3b8'
            },
            grid: {
              color: 'rgba(255, 255, 255, 0.1)'
            }
          },
          x: {
            ticks: {
              color: '#94a3b8'
            },
            grid: {
              display: false
            }
          }
        }
      }
    });
    
    // Force resize to ensure proper rendering when tab becomes visible
    setTimeout(() => {
      if (window.preferencesChart) {
        window.preferencesChart.resize();
      }
    }, 100);
  } catch (e) {
    console.error('Error rendering preferences chart:', e);
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

  const file = fileInput.files[0];
  const fileName = file.name;
  const mimeType = file.type;
  resultDiv.innerHTML = `<p>Processing ${fileName}... <i class='fas fa-spinner fa-spin'></i></p>`;
  resultDiv.style.display = "block";

  const analyzeBtn = document.querySelector('#deepfake .analyze-btn');
  if (analyzeBtn) analyzeBtn.disabled = true;

  // Use FileReader to read the file as base64
  const reader = new FileReader();
  reader.onload = function (e) {
    const base64Data = e.target.result.split(',')[1]; // Get base64 part only

    // Send the file to the backend for analysis
    fetch("http://localhost:5001/analyze", {
      method: "POST",
      body: JSON.stringify({
        text: fileName,
        type: "deepfake",
        image_data: base64Data,
        mime_type: mimeType
      }),
      headers: { "Content-Type": "application/json" }
    })
      .then(res => res.json())
      .then(data => {
        if (analyzeBtn) analyzeBtn.disabled = false;
        // If backend returned an error or a fetch-failure note, show friendly message
        if (data.status === 'Error' || (data.reason && data.reason.toLowerCase().includes('could not fetch'))) {
          resultDiv.innerHTML = `<p class='placeholder-text'>Could not fetch the file content for deepfake analysis. Showing filename-based heuristic instead.</p>`;
          if (data.reason) resultDiv.innerHTML += `<p>${data.reason}</p>`;
          return;
        }
        // Format the deepfake analysis result
        resultDiv.innerHTML = `
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
              <h4>Analysis Details</h4>
              <p>${data.reason}</p>
            </div>
            
            <div class="detail-item">
              <h4>Technical Assessment</h4>
              <p>${data.analysis_details?.technical_assessment || 'No technical details available'}</p>
            </div>
            
            <div class="detail-item">
              <h4>Privacy Risk</h4>
              <p class="risk-${data.privacy_risk.toLowerCase()}">${data.privacy_risk}</p>
              <p>${data.privacy_explanation}</p>
            </div>
          </div>
          
          <div class="full-analysis">
            <h4>Full Analysis</h4>
            <pre>Indicators Found: ${data.analysis_details?.indicators_found || 0}\nFake Probability: ${(data.analysis_details?.fake_probability * 100).toFixed(1) || 'N/A'}%\nTechnical Notes: ${data.analysis_details?.technical_assessment || 'No technical notes available'}</pre>
          </div>
        </div>
      `;

        // Save result if user is authenticated
        if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
          saveAnalysisResult(auth.currentUser.uid, 'deepfake', fileName, data);
        } else {
          // In standalone mode, just log that result would be saved in full version
          console.log('Analysis result would be saved in full version with authentication');
        }
      })
      .catch(error => {
        console.error('Backend connection error:', error);
        resultDiv.innerHTML = `<p>Error: Could not connect to backend (${error.message || 'Unknown error'}). Please ensure the backend is running at http://localhost:5001.</p>`;
        resultDiv.style.display = "block";
      });
  };

  reader.onerror = function () {
    resultDiv.innerHTML = `<p>Error reading file: ${file.name}</p>`;
  };

  reader.readAsDataURL(file);
}

// Function to show preview of selected file
function previewFile() {
  const fileInput = document.getElementById('deepfakeFile');
  const fileDisplayArea = document.querySelector('.file-upload-area');

  if (fileInput.files && fileInput.files[0]) {
    const file = fileInput.files[0];

    const reader = new FileReader();
    reader.onload = function (e) {
      const isImage = file.type.match('image.*');
      const isVideo = file.type.match('video.*');

      // Create preview HTML
      let previewContent = "";
      if (isImage) {
        previewContent = `<img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px; margin-bottom: 10px; border-radius: 8px; border: 2px solid var(--accent-color);">`;
      } else if (isVideo) {
        previewContent = `<i class="fas fa-file-video" style="font-size: 48px; margin-bottom: 10px; color: var(--accent-color);"></i>`;
      } else {
        previewContent = `<i class="fas fa-file" style="font-size: 48px; margin-bottom: 10px; color: var(--accent-color);"></i>`;
      }

      const previewHtml = `
        <div id="filePreviewContainer" style="display: flex; flex-direction: column; align-items: center; width: 100%;">
          ${previewContent}
          <p style="margin-bottom: 10px; word-break: break-all;">${file.name}</p>
          <button class="browse-btn" onclick="document.getElementById('deepfakeFile').click()">Change File</button>
        </div>
      `;

      // Hide the original input but keep it in the DOM
      fileInput.style.display = 'none';

      // Clear display area and re-add the input + the new preview
      const currentInput = document.getElementById('deepfakeFile');
      fileDisplayArea.innerHTML = '';
      fileDisplayArea.appendChild(currentInput);
      fileDisplayArea.insertAdjacentHTML('beforeend', previewHtml);
    }

    if (file.type.match('image.*')) {
      reader.readAsDataURL(file);
    } else {
      // For non-images, just show the name and icon immediately
      reader.onload({ target: { result: null } });
    }
  }
}

// CLEAR DEEPFAKE ANALYSIS
function clearDeepfakeAnalysis() {
  const fileDisplayArea = document.querySelector('.file-upload-area');
  if (fileDisplayArea) {
    fileDisplayArea.innerHTML = `
      <i class="fas fa-cloud-upload-alt"></i>
      <p>Drag & drop your image/video here or click to browse</p>
      <input type="file" id="deepfakeFile" accept="image/*,video/*" onchange="previewFile()">
      <button class="browse-btn" onclick="document.getElementById('deepfakeFile').click()">Browse Files</button>
    `;
  }

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

  fetch("http://localhost:5001/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, type: "news" })
  })
    .then(res => res.json())
    .then(data => {
      // If backend returned an error or a fetch-failure note, show friendly message
      if (data.status === 'Error' || (data.reason && data.reason.toLowerCase().includes('could not fetch'))) {
        result.innerHTML = `<p class='placeholder-text'>Could not fetch the full content from the provided URL. Showing domain-level heuristics instead.</p>`;
        if (data.reason) result.innerHTML += `<p>${data.reason}</p>`;
        return;
      }
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
          
          ${data.correction ? `
          <div class="detail-item correction-suggestion">
            <h4>Correction Suggestion</h4>
            <p>${data.correction}</p>
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
          <pre>${data.analysis || 'Detailed analysis not available'}</pre>
        </div>
      </div>
    `;

      // Save result if user is authenticated
      if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
        saveAnalysisResult(auth.currentUser.uid, 'news', text, data);
      } else {
        // In standalone mode, just log that result would be saved in full version
        console.log('Analysis result would be saved in full version with authentication');
      }
    })
    .catch(error => {
      console.error('Backend connection error:', error);
      result.innerHTML = `<p>Error: Could not connect to backend (${error.message || 'Unknown error'}). Please ensure the backend is running at http://localhost:5001.</p>`;
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

  fetch("http://localhost:5001/analyze", {
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
          
          ${data.correction ? `
          <div class="detail-item correction-suggestion">
            <h4>Correct Information / Fact Check</h4>
            <p>${data.correction}</p>
          </div>
          ` : ''}
          
          <div class="detail-item">
            <h4>Source Information</h4>
            <p>${data.analysis ? data.analysis.split('\n')[0] : data.reason || 'Analysis information not available'}</p>
          </div>
        </div>
      </div>
    `;

      // Save result if user is authenticated
      if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
        saveAnalysisResult(auth.currentUser.uid, 'news-link', url, data);
      } else {
        // In standalone mode, just log that result would be saved in full version
        console.log('Analysis result would be saved in full version with authentication');
      }
    })
    .catch(error => {
      console.error('Backend connection error:', error);
      result.innerHTML = `<p>Error: Could not connect to backend (${error.message || 'Unknown error'}). Note: API key not configured, using heuristic analysis only.</p>`;
      result.style.display = "block";
    });
}


// 🧠 ADVANCED ANALYSIS
function analyzeAdvanced() {
  const text = document.getElementById("newsInput").value;
  const result = document.getElementById("newsResult");
  const structuredResult = document.getElementById("newsStructuredResult");

  if (!text) {
    alert("Please enter news content to analyze.");
    return;
  }

  result.innerHTML = "<p>Performing advanced analysis with Ollama...</p>";
  result.style.display = "block";
  structuredResult.style.display = "none"; // Hide structured results during analysis

  fetch("http://localhost:5001/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, type: "news_advanced" })
  })
    .then(res => res.json())
    .then(data => {
      // Format the regular response
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
          
          ${data.correction ? `
          <div class="detail-item correction-suggestion">
            <h4>Correction Suggestion</h4>
            <p>${data.correction}</p>
          </div>
          ` : ''}
          
          <div class="detail-item">
            <h4>Privacy Risk</h4>
            <p class="risk-${data.privacy_risk.toLowerCase()}">${data.privacy_risk}</p>
            <p>${data.privacy_explanation}</p>
          </div>
        </div>
      </div>
    `;

      // Format the structured response with advanced details
      structuredResult.innerHTML = `
      <h4>Advanced Analysis Breakdown</h4>
      <div class="structured-content">
        <div class="structured-section">
          <h5>Claims Verification</h5>
          <ul>
            <li><strong>Status:</strong> ${data.status}</li>
            <li><strong>Confidence:</strong> ${(parseFloat(data.confidence) * 100).toFixed(1)}%</li>
            <li><strong>Reasoning:</strong> ${data.reason}</li>
          </ul>
        </div>
        
        <div class="structured-section">
          <h5>Indicators Analysis</h5>
          <p>${data.indicators || 'No specific indicators provided'}</p>
        </div>
        
        <div class="structured-section">
          <h5>Verification Suggestions</h5>
          <p>${data.verification_suggestions || 'Verify with multiple reliable sources'}</p>
        </div>
        
        <div class="structured-section">
          <h5>Raw Model Output</h5>
          <div class="raw-output">
            <pre>${data.raw_output || 'No raw output available'}</pre>
          </div>
        </div>
        
        <div class="structured-section">
          <h5>Privacy Assessment</h5>
          <ul>
            <li><strong>Risk Level:</strong> ${data.privacy_risk}</li>
            <li><strong>Explanation:</strong> ${data.privacy_explanation}</li>
          </ul>
        </div>
        
        ${data.correction ? `
        <div class="structured-section">
          <h5>Correction & Fact Check</h5>
          <p>${data.correction}</p>
        </div>
        ` : ''}
      </div>
      `;

      structuredResult.style.display = "block"; // Show structured results

      // Save result if user is authenticated
      if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
        saveAnalysisResult(auth.currentUser.uid, 'news', text, data);
      } else {
        // In standalone mode, just log that result would be saved in full version
        console.log('Analysis result would be saved in full version with authentication');
      }
    })
    .catch(error => {
      console.error('Backend connection error:', error);
      result.innerHTML = `<p>Error: Could not connect to backend (${error.message || 'Unknown error'}). Note: API key not configured, using heuristic analysis only.</p>`;
      result.style.display = "block";
      structuredResult.style.display = "none";
    });
}

// 🔊 TEXT-TO-SPEECH FUNCTION
function speakText(text) {
  if ('speechSynthesis' in window) {
    // Cancel any ongoing speech
    speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Configure speech settings
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1;
    
    // Try to use a natural-sounding voice
    const voices = speechSynthesis.getVoices();
    const englishVoice = voices.find(voice => 
      voice.lang.includes('en') || 
      voice.name.includes('Google') || 
      voice.name.includes('Natural')
    );
    
    if (englishVoice) {
      utterance.voice = englishVoice;
    }
    
    speechSynthesis.speak(utterance);
  } else {
    alert('Text-to-speech is not supported in your browser.');
  }
}

// 🔊 SPEAK ANALYSIS RESULTS
function speakAnalysisResults() {
  const resultDiv = document.getElementById("newsResult");
  const structuredResultDiv = document.getElementById("newsStructuredResult");
  
  // Extract text from both regular and structured results
  let textToSpeak = "";
  
  // Get text from regular results
  if (resultDiv && resultDiv.innerText) {
    textToSpeak += resultDiv.innerText + " ";
  }
  
  // Get text from structured results
  if (structuredResultDiv && structuredResultDiv.innerText) {
    textToSpeak += structuredResultDiv.innerText;
  }
  
  if (textToSpeak.trim()) {
    // Clean up the text to make it more speakable
    textToSpeak = textToSpeak.replace(/\n/g, '. ').replace(/\s+/g, ' ');
    speakText(textToSpeak);
  } else {
    alert('No analysis results to speak.');
  }
}

// Initialize speech synthesis voices when available
window.addEventListener('load', function() {
  // Some browsers need a little time to load voices
  setTimeout(() => {
    if ('speechSynthesis' in window) {
      speechSynthesis.getVoices(); // This helps preload voices
    }
  }, 500);
});

// 🔐 PRIVACY ANALYSIS (SAME AI, DIFFERENT TAB)
function analyzePrivacy() {
  const text = document.getElementById("privacyInput").value;
  const result = document.getElementById("privacyResult");

  result.innerHTML = "<p>Checking privacy risk...</p>";
  result.style.display = "block";

  fetch("http://localhost:5001/analyze", {
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
          
          ${data.correction ? `
          <div class="detail-item correction-suggestion">
            <h4>Correction Suggestion</h4>
            <p>${data.correction}</p>
          </div>
          ` : ''}
        </div>
        
        <div class="full-analysis">
          <h4>Full Analysis</h4>
          <pre>${data.analysis || 'Detailed analysis not available'}</pre>
        </div>
      </div>
    `;

      // Save result if user is authenticated
      if (typeof saveAnalysisResult !== 'undefined' && typeof auth !== 'undefined' && auth.currentUser) {
        saveAnalysisResult(auth.currentUser.uid, 'privacy', text, data);
      } else {
        // In standalone mode, just log that result would be saved in full version
        console.log('Analysis result would be saved in full version with authentication');
      }
    })
    .catch(error => {
      console.error('Backend connection error:', error);
      result.innerHTML = `<p>Error: Could not connect to backend (${error.message || 'Unknown error'}). Note: API key not configured, using heuristic analysis only.</p>`;
      result.style.display = "block";
    });
}
