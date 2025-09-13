// --- FILE: frontend/assets/js/script.js ---

// 1. Get references to all the HTML elements we'll need to interact with
const urlInput = document.getElementById('url-input');
const analyzeBtn = document.getElementById('analyze-btn');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const buttonText = analyzeBtn.querySelector('.button-text');
const buttonLoader = analyzeBtn.querySelector('.loader');

// The URL of our deployed backend.
// For local testing, this points to our local server.
// IMPORTANT: Change this to your real Google Cloud Function URL after deployment.
const API_ENDPOINT = 'http://localhost:8080';

// 2. Add an event listener for the "Analyze" button
analyzeBtn.addEventListener('click', handleAnalysis);

async function handleAnalysis() {
    const urlToAnalyze = urlInput.value;

    // Simple validation to ensure the URL is not empty
    if (!urlToAnalyze) {
        displayError({ error: "Please enter a URL to analyze." });
        return;
    }

    // 3. Update the UI to show the loading state
    setLoadingState(true);

    try {
        // 4. Make the API call to our backend
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: urlToAnalyze }),
        });

        const data = await response.json();

        if (!response.ok) {
            // If the server returns an error (like 400 or 500), handle it
            displayError(data);
        } else {
            // If the server returns a successful response, display the results
            displayResults(data);
        }
    } catch (error) {
        // Handle network errors (e.g., backend server is not running)
        console.error('Network or fetch error:', error);
        displayError({ error: "Cannot connect to the analysis service. Please ensure it is running." });
    } finally {
        // 5. Always revert the UI back to the normal state
        setLoadingState(false);
    }
}

function setLoadingState(isLoading) {
    if (isLoading) {
        analyzeBtn.disabled = true;
        buttonText.classList.add('hidden');
        buttonLoader.classList.remove('hidden');
        loadingSection.classList.remove('hidden');
        resultsSection.innerHTML = ''; // Clear previous results
        resultsSection.classList.add('hidden');
    } else {
        analyzeBtn.disabled = false;
        buttonText.classList.remove('hidden');
        buttonLoader.classList.add('hidden');
        loadingSection.classList.add('hidden');
    }
}

function displayResults(data) {
    resultsSection.classList.remove('hidden');

    const verdictClass = data.verdict.toLowerCase(); // e.g., "verified", "danger"
    const scoreColor = `var(--color-${verdictClass})`;
    const verdictIcon = {
        'Verified': 'verified',
        'Caution': 'warning',
        'Unreliable': 'error',
        'Danger': 'gpp_bad'
    }[data.verdict] || 'help';

    const flagsHTML = data.flags.length > 0
        ? `
        <div class="results-card flags-card">
            <h3>Flags Detected</h3>
            <ul class="flags-list">
                ${data.flags.map(flag => `<li><span class="material-symbols-outlined">flag</span>${flag.replace(/_/g, ' ')}</li>`).join('')}
            </ul>
        </div>`
        : '';

    resultsSection.innerHTML = `
        <div class="results-card verdict-card">
            <div class="score-gauge" style="border-color: ${scoreColor};">
                <span class="${verdictClass}">${data.veracity_score}</span>
            </div>
            <div class="verdict-text ${verdictClass}">
                <span class="material-symbols-outlined">${verdictIcon}</span>
                <h2>${data.verdict}</h2>
            </div>
        </div>
        <div class="results-card summary-card">
            <h3>Summary</h3>
            <p>${data.summary}</p>
        </div>
        ${flagsHTML}
    `;
}

function displayError(data) {
    resultsSection.classList.remove('hidden');
    resultsSection.innerHTML = `
        <div class="results-card error-card">
            <h3>Analysis Error</h3>
            <p>${data.error || 'An unknown error occurred.'}</p>
        </div>
    `;
}