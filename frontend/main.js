// Theme Management
class ThemeManager {
  constructor() {
    this.theme = localStorage.getItem('theme') || 'light';
    this.init();
  }

  init() {
    document.documentElement.setAttribute('data-theme', this.theme);
    this.updateThemeIcon();
  }

  toggle() {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', this.theme);
    localStorage.setItem('theme', this.theme);
    this.updateThemeIcon();
  }

  updateThemeIcon() {
    const lightIcon = document.querySelector('.light-icon');
    const darkIcon = document.querySelector('.dark-icon');
    
    if (this.theme === 'light') {
      lightIcon.style.display = 'block';
      darkIcon.style.display = 'none';
    } else {
      lightIcon.style.display = 'none';
      darkIcon.style.display = 'block';
    }
  }
}

// Date Management
class DateManager {
  constructor() {
    // Start with today's date, but it will be updated when we get the actual available date
    this.currentDate = new Date();
    this.app = null; // Reference to the main app
    this.init();
  }

  init() {
    this.updateDateDisplay();
    this.bindEvents();
  }

  setApp(app) {
    this.app = app;
  }

  formatDate(date) {
    const options = { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    };
    return date.toLocaleDateString('en-US', options);
  }

  async updateDateDisplay() {
    const dateDisplay = document.getElementById('dateDisplay');
    if (dateDisplay) {
      dateDisplay.textContent = this.formatDate(this.currentDate);
    }
    
    // Update button states based on available dates
    await this.updateButtonStates();
  }

  async updateButtonStates() {
    try {
      // Check if current date is in the future
      const today = new Date();
      today.setHours(23, 59, 59, 999);
      
      if (this.currentDate > today) {
        this.setButtonState('nextDate', false);
        this.setButtonState('prevDate', true);
        return;
      }
      
      // For previous button, always allow going back (unless it's too far in the past)
      const minDate = new Date('2020-01-01'); // Reasonable minimum date
      this.setButtonState('prevDate', this.currentDate > minDate);
      
      // For next button, only disable if it's today or in the future
      this.setButtonState('nextDate', this.currentDate < today);
      
    } catch (error) {
      console.error('Error updating button states:', error);
    }
  }

  setButtonState(buttonId, enabled) {
    const button = document.getElementById(buttonId);
    if (button) {
      button.disabled = !enabled;
      button.style.opacity = enabled ? '1' : '0.5';
      button.style.cursor = enabled ? 'pointer' : 'not-allowed';
    }
  }

  async navigateDate(direction) {
    try {
      // Calculate target date first
      const newDate = new Date(this.currentDate);
      newDate.setDate(newDate.getDate() + direction);
      
      // Check if the new date is in the future
      const today = new Date();
      today.setHours(23, 59, 59, 999); // End of today
      
      if (newDate > today) {
        this.showDateLimitNotification('Cannot navigate to future dates');
        return;
      }
      
      // Update current date
      this.currentDate = newDate;
      this.updateDateDisplay();
      
      // Show loading animation
      const dateStr = this.formatDate(this.currentDate);
      const direction_str = direction > 0 ? "next" : "prev";
      this.showLoading(`Loading papers for ${dateStr}...`, `Navigating ${direction_str} from Hugging Face`);
      
      // Try to load the target date with direction
      if (this.app && this.app.loadDaily) {
        await this.app.loadDaily(direction_str);
      }
      
    } catch (error) {
      console.error('Error navigating date:', error);
      this.showDateLimitNotification('Error loading date');
    }
  }

  // Removed old notification functions - now using unified notification system

  showLoading(message = 'Loading papers...', submessage = 'Fetching data from Hugging Face') {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
      const loadingText = loadingOverlay.querySelector('.loading-text');
      const loadingSubtext = loadingOverlay.querySelector('.loading-subtext');
      
      if (loadingText) loadingText.textContent = message;
      if (loadingSubtext) loadingSubtext.textContent = submessage;
      
      loadingOverlay.classList.add('show');
    }
  }

  hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
      loadingOverlay.classList.remove('show');
    }
  }

  bindEvents() {
    const prevBtn = document.getElementById('prevDate');
    const nextBtn = document.getElementById('nextDate');
    
    if (prevBtn) {
      prevBtn.addEventListener('click', async () => {
        await this.navigateDate(-1);
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', async () => {
        await this.navigateDate(1);
      });
    }
  }

  getDateString() {
    const pad = (n) => String(n).padStart(2, '0');
    return `${this.currentDate.getFullYear()}-${pad(this.currentDate.getMonth()+1)}-${pad(this.currentDate.getDate())}`;
  }
}

// Search Management
class SearchManager {
  constructor() {
    this.init();
  }

  init() {
    this.bindEvents();
  }

  bindEvents() {
    const searchInput = document.querySelector('.search-input');
    const aiSearchInput = document.querySelector('.ai-search-input');
    
    searchInput.addEventListener('input', (e) => {
      this.handleSearch(e.target.value);
    });

    aiSearchInput.addEventListener('input', (e) => {
      this.handleAISearch(e.target.value);
    });
  }

  handleSearch(query) {
    // Implement search functionality
    console.log('Search query:', query);
  }

  handleAISearch(query) {
    // Implement AI search functionality
    console.log('AI search query:', query);
  }
}

// Paper Card Renderer
class PaperCardRenderer {
  constructor() {
    this.cardsContainer = document.getElementById('cards');
  }

  generateThumbnail(title) {
    // Generate a simple thumbnail based on title
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 120;
    const ctx = canvas.getContext('2d');
    
    // Create gradient background
    const gradient = ctx.createLinearGradient(0, 0, 400, 120);
    gradient.addColorStop(0, '#3b82f6');
    gradient.addColorStop(1, '#06b6d4');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 400, 120);
    
    // Add text
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.font = 'bold 16px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    const words = title.split(' ');
    const lines = [];
    let currentLine = '';
    
    for (const word of words) {
      const testLine = currentLine + word + ' ';
      const metrics = ctx.measureText(testLine);
      if (metrics.width > 350 && currentLine !== '') {
        lines.push(currentLine);
        currentLine = word + ' ';
      } else {
        currentLine = testLine;
      }
    }
    lines.push(currentLine);
    
    const yStart = 60 - (lines.length * 20) / 2;
    lines.forEach((line, index) => {
      ctx.fillText(line.trim(), 200, yStart + index * 20);
    });
    
    return canvas.toDataURL();
  }

  generateAuthorAvatars(authorCount) {
    const avatars = [];
    const count = Math.min(authorCount, 5);
    
    for (let i = 0; i < count; i++) {
      avatars.push(`<li title="Author ${i + 1}"></li>`);
    }
    
    return avatars.join('');
  }

  renderCard(paper) {
    const title = paper.title || 'Untitled Paper';
    const abstract = paper.abstract || 'No abstract available';
    const authors = paper.authors || [];
    const authorCount = paper.author_count || authors.length || 0;
    const upvotes = paper.upvotes || 0;
    const githubStars = paper.github_stars || 0;
    const comments = paper.comments || 0;
    const submitter = paper.submitter || 'Anonymous';
    
    // Generate thumbnail URL - try to use HF thumbnail if available
    const arxivId = paper.arxiv_id;
    const thumbnailUrl = arxivId ? 
      `https://cdn-thumbnails.huggingface.co/social-thumbnails/papers/${arxivId}.png` : 
      this.generateThumbnail(title);
    
    const authorAvatars = this.generateAuthorAvatars(authorCount);
    
    const card = document.createElement('article');
    card.className = 'hf-paper-card';
    card.innerHTML = `
      <a href="${paper.huggingface_url || '#'}" class="paper-thumbnail-link" target="_blank" rel="noreferrer">
        <img src="${thumbnailUrl}" loading="lazy" decoding="async" alt="" class="paper-thumbnail-img">
      </a>
      
      <div class="submitted-by-badge">
        <span>Submitted by</span>
        <div class="submitter-avatar-placeholder">
          <i class="fas fa-user"></i>
        </div>
        ${submitter}
      </div>
      
      <div class="card-content">
        <div class="upvote-section">
          <label class="upvote-button">
            <input type="checkbox" class="upvote-checkbox">
            <svg class="upvote-icon" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="img" width="1em" height="1em" preserveAspectRatio="xMidYMid meet" viewBox="0 0 12 12">
              <path fill="currentColor" d="M5.19 2.67a.94.94 0 0 1 1.62 0l3.31 5.72a.94.94 0 0 1-.82 1.4H2.7a.94.94 0 0 1-.82-1.4l3.31-5.7v-.02Z"></path>
            </svg>
            <div class="upvote-count">${upvotes}</div>
          </label>
        </div>
        
        <div class="paper-info">
          <h3 class="paper-title">
            <a href="${paper.huggingface_url || '#'}" class="title-link">
              ${title}
            </a>
          </h3>
          
          <div class="paper-meta">
            <div class="authors-section">
              <a href="${paper.huggingface_url || '#'}" class="authors-link">
                <ul class="author-avatars-list">
                  ${authorAvatars}
                </ul>
                <div class="author-count">· ${authorCount} authors</div>
              </a>
            </div>
            
            <div class="engagement-metrics">
              <a href="${paper.huggingface_url || '#'}" class="metric-link">
                <svg class="github-icon" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false" role="img" width="1.03em" height="1em" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 250">
                  <path d="M128.001 0C57.317 0 0 57.307 0 128.001c0 56.554 36.676 104.535 87.535 121.46c6.397 1.185 8.746-2.777 8.746-6.158c0-3.052-.12-13.135-.174-23.83c-35.61 7.742-43.124-15.103-43.124-15.103c-5.823-14.795-14.213-18.73-14.213-18.73c-11.613-7.944.876-7.78.876-7.78c12.853.902 19.621 13.19 19.621 13.19c11.417 19.568 29.945 13.911 37.249 10.64c1.149-8.272 4.466-13.92 8.127-17.116c-28.431-3.236-58.318-14.212-58.318-63.258c0-13.975 5-25.394 13.188-34.358c-1.329-3.224-5.71-16.242 1.24-33.874c0 0 10.749-3.44 35.21 13.121c10.21-2.836 21.16-4.258 32.038-4.307c10.878.049 21.837 1.47 32.066 4.307c24.431-16.56 35.165-13.12 35.165-13.12c6.967 17.63 2.584 30.65 1.255 33.873c8.207 8.964 13.173 20.383 13.173 34.358c0 49.163-29.944 59.988-58.447 63.157c4.591 3.972 8.682 11.762 8.682 23.704c0 17.126-.148 30.91-.148 35.126c0 3.407 2.304 7.398 8.792 6.14C219.37 232.5 256 184.537 256 128.002C256 57.307 198.691 0 128.001 0zm-80.06 182.34c-.282.636-1.283.827-2.194.39c-.929-.417-1.45-1.284-1.15-1.922c.276-.655 1.279-.838 2.205-.399c.93.418 1.46 1.293 1.139 1.931zm6.296 5.618c-.61.566-1.804.303-2.614-.591c-.837-.892-.994-2.086-.375-2.66c.63-.566 1.787-.301 2.626.591c.838.903 1 2.088.363 2.66zm4.32 7.188c-.785.545-2.067.034-2.86-1.104c-.784-1.138-.784-2.503.017-3.05c.795-.547 2.058-.055 2.861 1.075c.782 1.157.782 2.522-.019 3.08zm7.304 8.325c-.701.774-2.196.566-3.29-.49c-1.119-1.032-1.43-2.496-.726-3.27c.71-.776 2.213-.558 3.315.49c1.11 1.03 1.45 2.505.701 3.27zm9.442 2.81c-.31 1.003-1.75 1.459-3.199 1.033c-1.448-.439-2.395-1.613-2.103-2.626c.301-1.01 1.747-1.484 3.207-1.028c1.446.436 2.396 1.602 2.095 2.622zm10.744 1.193c.036 1.055-1.193 1.93-2.715 1.95c-1.53.034-2.769-.82-2.786-1.86c0-1.065 1.202-1.932 2.733-1.958c1.522-.03 2.768.818 2.768 1.868zm10.555-.405c.182 1.03-.875 2.088-2.387 2.37c-1.485.271-2.861-.365-3.05-1.386c-.184-1.056.893-2.114 2.376-2.387c1.514-.263 2.868.356 3.061 1.403z" fill="currentColor"></path>
                </svg>
                <span>${githubStars}</span>
              </a>
              <a href="${paper.huggingface_url || '#'}" class="metric-link">
                <svg class="comment-icon" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="img" width="1em" height="1em" preserveAspectRatio="xMidYMid meet" viewBox="0 0 24 24">
                  <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span>${comments}</span>
              </a>
            </div>
          </div>
        </div>
      </div>
      
      ${paper.arxiv_id ? `
        <div class="card-actions">
          <button class="eval-button" data-arxiv-id="${paper.arxiv_id}" data-paper-title="${encodeURIComponent(title)}">
            <i class="fas fa-spinner fa-spin" style="display: none;"></i>
            <i class="fas fa-chart-line eval-icon"></i>
            <span class="eval-text">Checking...</span>
          </button>
        </div>
      ` : ''}
    `;

    // Check evaluation status for this paper
    if (paper.arxiv_id) {
      this.checkEvaluationStatus(card, paper.arxiv_id);
      
      // Store paper data in card for score checking
      card.setAttribute('data-paper-data', JSON.stringify(paper));
      this.checkPaperScore(card, paper.arxiv_id);
    }

    return card;
  }

  renderCards(papers) {
    this.cardsContainer.innerHTML = '';
    
    if (!papers || papers.length === 0) {
      this.cardsContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 48px; color: var(--text-muted);">
          <i class="fas fa-search" style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
          <h3>No papers found</h3>
          <p>Try selecting a different date or check back later.</p>
        </div>
      `;
      return;
    }

    papers.forEach(paper => {
      const card = this.renderCard(paper);
      this.cardsContainer.appendChild(card);
    });
  }

  async checkEvaluationStatus(card, arxivId) {
    const button = card.querySelector('.eval-button');
    const spinner = button.querySelector('.fa-spinner');
    const evalIcon = button.querySelector('.eval-icon');
    const evalText = button.querySelector('.eval-text');
    
    try {
      const response = await fetch(`/api/has-eval/${encodeURIComponent(arxivId)}`);
      const data = await response.json();
      
      if (data.exists) {
        // Paper has evaluation - show evaluation button
        evalIcon.className = 'fas fa-chart-line eval-icon';
        evalText.textContent = 'Evaluation';
        button.className = 'eval-button evaluation-state';
        button.onclick = () => {
          window.location.href = `/paper.html?id=${encodeURIComponent(arxivId)}`;
        };
        
        // Add re-evaluate button for already evaluated papers
        this.addReevaluateButton(card, arxivId);
      } else {
        // Paper doesn't have evaluation - show evaluate button
        evalIcon.className = 'fas fa-play eval-icon';
        evalText.textContent = 'Evaluate';
        button.className = 'eval-button evaluate-state';
        button.onclick = () => {
          this.evaluatePaper(button, arxivId);
        };
      }
    } catch (error) {
      console.error('Error checking evaluation status:', error);
      evalIcon.className = 'fas fa-exclamation-triangle eval-icon';
      evalText.textContent = 'Error';
      button.className = 'eval-button error-state';
    }
  }

  addReevaluateButton(card, arxivId) {
    // Check if re-evaluate button already exists
    if (card.querySelector('.reevaluate-button')) {
      return;
    }
    
    const cardActions = card.querySelector('.card-actions');
    if (cardActions) {
      const reevaluateButton = document.createElement('button');
      reevaluateButton.className = 'reevaluate-button';
      reevaluateButton.innerHTML = `
        <i class="fas fa-redo"></i>
        <span>Re-evaluate</span>
      `;
      reevaluateButton.onclick = () => {
        this.reevaluatePaper(reevaluateButton, arxivId);
      };
      
      cardActions.appendChild(reevaluateButton);
    }
  }

  async reevaluatePaper(button, arxivId) {
    const icon = button.querySelector('i');
    const text = button.querySelector('span');
    const originalText = text.textContent;
    const originalIcon = icon.className;
    
    // Show loading state
    icon.className = 'fas fa-spinner fa-spin';
    text.textContent = 'Re-evaluating...';
    button.disabled = true;
    
    // Show log message
    this.showLogMessage(`Started re-evaluation for paper ${arxivId}`, 'info');
    
    try {
      const response = await fetch(`/api/papers/reevaluate/${encodeURIComponent(arxivId)}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.status === 'already_running') {
          text.textContent = 'Already running';
          this.showLogMessage(`Re-evaluation already running for paper ${arxivId}`, 'warning');
          setTimeout(() => {
            icon.className = originalIcon;
            text.textContent = originalText;
            button.disabled = false;
          }, 2000);
        } else {
          // Start polling for status
          this.pollReevaluationStatus(button, arxivId, originalText, originalIcon);
        }
      } else {
        throw new Error('Failed to start re-evaluation');
      }
    } catch (error) {
      console.error('Error re-evaluating paper:', error);
      icon.className = 'fas fa-exclamation-triangle';
      text.textContent = 'Error';
      this.showLogMessage(`Re-evaluation failed for paper ${arxivId}: ${error.message}`, 'error');
      setTimeout(() => {
        icon.className = originalIcon;
        text.textContent = originalText;
        button.disabled = false;
      }, 2000);
    }
  }

  async pollReevaluationStatus(button, arxivId, originalText, originalIcon) {
    const icon = button.querySelector('i');
    const text = button.querySelector('span');
    let pollCount = 0;
    const maxPolls = 60; // Poll for up to 5 minutes (5s intervals)
    
    const poll = async () => {
      try {
        const response = await fetch(`/api/papers/evaluate/${encodeURIComponent(arxivId)}/status`);
        if (response.ok) {
          const status = await response.json();
          
          switch (status.status) {
            case 'evaluating':
              text.textContent = `Re-evaluating... (${pollCount * 5}s)`;
              icon.className = 'fas fa-spinner fa-spin';
              this.showLogMessage(`Re-evaluating paper ${arxivId}... (${pollCount * 5}s)`, 'info');
              break;
              
            case 'completed':
              icon.className = 'fas fa-check';
              text.textContent = 'Re-evaluated';
              button.disabled = false;
              this.showLogMessage(`Re-evaluation completed for paper ${arxivId}`, 'success');
              
              // Refresh the page to show updated results
              setTimeout(() => {
                window.location.reload();
              }, 1000);
              return;
              
            case 'failed':
              icon.className = 'fas fa-exclamation-triangle';
              text.textContent = 'Failed';
              button.disabled = false;
              this.showLogMessage(`Re-evaluation failed for paper ${arxivId}`, 'error');
              return;
              
            default:
              text.textContent = `Status: ${status.status}`;
          }
          
          pollCount++;
          if (pollCount < maxPolls) {
            setTimeout(poll, 5000);
          } else {
            icon.className = 'fas fa-clock';
            text.textContent = 'Timeout';
            button.disabled = false;
            this.showLogMessage(`Re-evaluation timeout for paper ${arxivId}`, 'warning');
          }
        } else {
          throw new Error('Failed to get status');
        }
      } catch (error) {
        console.error('Error polling re-evaluation status:', error);
        icon.className = 'fas fa-exclamation-triangle';
        text.textContent = 'Error';
        button.disabled = false;
      }
    };
    
    poll();
  }



  async checkPaperScore(card, arxivId) {
    try {
      // First check if the card already has score data from the API response
      const cardData = card.getAttribute('data-paper-data');
      if (cardData) {
        const paperData = JSON.parse(cardData);
        if (paperData.overall_score !== null && paperData.overall_score !== undefined) {
          this.displayScoreBadge(card, paperData.overall_score, arxivId);
          return;
        }
      }
      
      // Fallback to API call if no score data in card
      const response = await fetch(`/api/paper-score/${encodeURIComponent(arxivId)}`);
      const data = await response.json();
      
      console.log(`Paper score data for ${arxivId}:`, data);
      
      if (data.has_score && data.score !== null) {
        this.displayScoreBadge(card, data.score, arxivId);
      }
    } catch (error) {
      console.error('Error checking paper score:', error);
    }
  }

  displayScoreBadge(card, score, arxivId) {
    // Create score badge
    const scoreBadge = document.createElement('div');
    scoreBadge.className = 'score-badge';
    const formattedScore = parseFloat(score).toFixed(1);
    
    // Determine score color based on value (0-4 scale)
    const scoreValue = parseFloat(score);
    let scoreColor = 'var(--accent-primary)';
    if (scoreValue >= 3.0) {
      scoreColor = 'var(--accent-success)';
    } else if (scoreValue >= 2.0) {
      scoreColor = 'var(--accent-warning)';
    } else if (scoreValue < 1.0) {
      scoreColor = 'var(--accent-danger)';
    }
    
    scoreBadge.style.background = `linear-gradient(135deg, ${scoreColor}, ${scoreColor}dd)`;
    scoreBadge.innerHTML = `
      <span class="score-number">${formattedScore}</span>
      <span class="score-label">Overall</span>
    `;
    
    // Add click handler to navigate to evaluation page
    scoreBadge.onclick = () => {
      window.location.href = `/paper.html?id=${encodeURIComponent(arxivId)}`;
    };
    
    // Add to card with animation
    card.appendChild(scoreBadge);
    scoreBadge.style.opacity = '0';
    scoreBadge.style.transform = 'scale(0.8) translateY(10px)';
    
    // Animate in
    setTimeout(() => {
      scoreBadge.style.transition = 'all 0.3s ease';
      scoreBadge.style.opacity = '1';
      scoreBadge.style.transform = 'scale(1) translateY(0)';
    }, 100);
  }

  async evaluatePaper(button, arxivId, isReevaluate = false) {
    const spinner = button.querySelector('.fa-spinner');
    const evalIcon = button.querySelector('.eval-icon');
    const evalText = button.querySelector('.eval-text');
    const paperTitle = button.getAttribute('data-paper-title');
    
    // Clear any existing state classes and show loading state
    button.className = 'eval-button started-state';
    spinner.style.display = 'inline-block';
    evalIcon.style.display = 'none';
    evalText.textContent = isReevaluate ? 'Re-starting...' : 'Starting...';
    button.disabled = true;
    
    try {
      // First, check if paper exists in database, if not, insert it
      const paperData = {
        arxiv_id: arxivId,
        title: decodeURIComponent(paperTitle),
        authors: "Unknown Authors", // We don't have authors in the card data
        abstract: "No abstract available",
        categories: "Unknown",
        published_date: new Date().toISOString().split('T')[0]
      };
      
      // Try to insert the paper (this will work even if it already exists)
      await fetch('/api/papers/insert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(paperData)
      });
      
      // Start evaluation
      const url = isReevaluate ? 
        `/api/papers/reevaluate/${encodeURIComponent(arxivId)}` : 
        `/api/papers/evaluate/${encodeURIComponent(arxivId)}`;
      
      const response = await fetch(url, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.status === 'already_evaluated' && !isReevaluate) {
          // Paper was already evaluated, redirect to evaluation page
          window.location.href = `/paper.html?id=${encodeURIComponent(arxivId)}`;
        } else {
          // Evaluation started, show progress and poll for status
          evalText.textContent = isReevaluate ? 'Re-started...' : 'Started...';
          button.className = 'eval-button started-state';
          
          // Start polling for status
          this.pollEvaluationStatus(button, arxivId, isReevaluate);
        }
      } else {
        throw new Error('Failed to start evaluation');
      }
    } catch (error) {
      console.error('Error evaluating paper:', error);
      evalIcon.className = 'fas fa-exclamation-triangle eval-icon';
      evalText.textContent = 'Error';
      button.className = 'eval-button error-state';
      button.disabled = false;
    } finally {
      spinner.style.display = 'none';
      evalIcon.style.display = 'inline-block';
    }
  }

  async pollEvaluationStatus(button, arxivId, isReevaluate = false) {
    const evalIcon = button.querySelector('.eval-icon');
    const evalText = button.querySelector('.eval-text');
    let pollCount = 0;
    const maxPolls = 60; // Poll for up to 5 minutes (5s intervals)
    
    // Show log message
    const action = isReevaluate ? 're-evaluation' : 'evaluation';
    this.showLogMessage(`Started ${action} for paper ${arxivId}`, 'info');
    
    const poll = async () => {
      try {
        const response = await fetch(`/api/papers/evaluate/${encodeURIComponent(arxivId)}/status`);
        if (response.ok) {
          const status = await response.json();
          
          switch (status.status) {
            case 'evaluating':
              evalText.textContent = isReevaluate ? `Re-evaluating... (${pollCount * 5}s)` : `Evaluating... (${pollCount * 5}s)`;
              evalIcon.className = 'fas fa-spinner fa-spin eval-icon';
              button.className = 'eval-button evaluating-state';
              const evaluatingAction = isReevaluate ? 'Re-evaluating' : 'Evaluating';
              this.showLogMessage(`${evaluatingAction} paper ${arxivId}... (${pollCount * 5}s)`, 'info');
              break;
              
            case 'completed':
              evalIcon.className = 'fas fa-check eval-icon';
              evalText.textContent = isReevaluate ? 'Re-evaluated' : 'Completed';
              button.className = 'eval-button evaluation-state';
              button.onclick = () => {
                window.location.href = `/paper.html?id=${encodeURIComponent(arxivId)}`;
              };
              const completedAction = isReevaluate ? 'Re-evaluation' : 'Evaluation';
              this.showLogMessage(`${completedAction} completed for paper ${arxivId}`, 'success');
              
              // Add score badge after completion
              this.checkPaperScore(button.closest('.hf-paper-card'), arxivId);
              
              // Add re-evaluate button if not already re-evaluating
              if (!isReevaluate) {
                this.addReevaluateButton(button.closest('.hf-paper-card'), arxivId);
              }
              
              return; // Stop polling
              
            case 'failed':
              evalIcon.className = 'fas fa-exclamation-triangle eval-icon';
              evalText.textContent = 'Failed';
              button.className = 'eval-button error-state';
              button.disabled = false;
              this.showLogMessage(`Evaluation failed for paper ${arxivId}`, 'error');
              return; // Stop polling
              
            default:
              evalText.textContent = `Processing... (${pollCount * 5}s)`;
              button.className = 'eval-button processing-state';
          }
        }
      } catch (error) {
        console.error('Error polling status:', error);
        this.showLogMessage(`Error checking status for paper ${arxivId}`, 'error');
      }
      
      pollCount++;
      if (pollCount < maxPolls) {
        setTimeout(poll, 5000); // Poll every 5 seconds
      } else {
        // Timeout
        evalIcon.className = 'fas fa-clock eval-icon';
        evalText.textContent = 'Timeout';
        button.className = 'eval-button error-state';
        button.disabled = false;
        this.showLogMessage(`Evaluation timeout for paper ${arxivId}`, 'warning');
      }
    };
    
    // Start polling
    setTimeout(poll, 5000); // First poll after 5 seconds
  }

  showLogMessage(message, type = 'info') {
    // Create or get log container
    let logContainer = document.getElementById('evaluation-log');
    if (!logContainer) {
      logContainer = document.createElement('div');
      logContainer.id = 'evaluation-log';
      logContainer.className = 'evaluation-log';
      logContainer.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        max-width: 400px;
        max-height: 300px;
        overflow-y: auto;
        background: var(--bg-primary);
        border: 1px solid var(--border-medium);
        border-radius: 8px;
        padding: 12px;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        font-size: 12px;
      `;
      document.body.appendChild(logContainer);
    }
    
    // Create log entry
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.style.cssText = `
      margin-bottom: 8px;
      padding: 8px;
      border-radius: 4px;
      border-left: 3px solid;
    `;
    
    // Set color based on type
    switch (type) {
      case 'success':
        logEntry.style.borderLeftColor = 'var(--accent-success)';
        logEntry.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
        break;
      case 'error':
        logEntry.style.borderLeftColor = 'var(--accent-danger)';
        logEntry.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
        break;
      case 'warning':
        logEntry.style.borderLeftColor = 'var(--accent-warning)';
        logEntry.style.backgroundColor = 'rgba(245, 158, 11, 0.1)';
        break;
      default:
        logEntry.style.borderLeftColor = 'var(--accent-primary)';
        logEntry.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
    }
    
    const timestamp = new Date().toLocaleTimeString();
    logEntry.innerHTML = `
      <div style="font-weight: 500; margin-bottom: 2px;">${timestamp}</div>
      <div>${message}</div>
    `;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // Auto-remove old entries (keep last 10)
    const entries = logContainer.querySelectorAll('.log-entry');
    if (entries.length > 10) {
      entries[0].remove();
    }
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
      setTimeout(() => {
        if (logEntry.parentNode) {
          logEntry.style.opacity = '0.5';
        }
      }, 5000);
    }
  }
}

// Main Application
class PaperIndexApp {
  constructor() {
    this.themeManager = new ThemeManager();
    this.dateManager = new DateManager();
    this.dateManager.setApp(this); // Pass app reference to date manager
    this.searchManager = new SearchManager();
    this.cardRenderer = new PaperCardRenderer();
    this.init();
  }

  init() {
    this.bindEvents();
    this.dateManager.showLoading('Loading papers...', 'Initializing application');
    this.loadDaily();
  }

  bindEvents() {
    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', () => {
      this.themeManager.toggle();
    });

    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
      });
    });

    // Batch evaluate button
    const batchEvaluateBtn = document.getElementById('batchEvaluateBtn');
    console.log('Looking for batchEvaluateBtn:', batchEvaluateBtn);
    if (batchEvaluateBtn) {
      console.log('Adding click listener to batchEvaluateBtn');
      batchEvaluateBtn.addEventListener('click', () => {
        console.log('Batch evaluate button clicked');
        this.startBatchEvaluation();
      });
    } else {
      console.error('batchEvaluateBtn not found during initialization');
    }
  }

  async loadDaily(direction = null) {
    const dateStr = this.dateManager.getDateString();
    
    try {
      // Build URL with direction parameter if provided
      let url = `/api/daily?date_str=${encodeURIComponent(dateStr)}`;
      if (direction) {
        url += `&direction=${direction}`;
      }
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('Failed to load daily papers');
      }
      
      const data = await response.json();
      
      console.log('API Response:', {
        requested_date: data.requested_date,
        actual_date: data.date,
        fallback_used: data.fallback_used,
        cards_count: data.cards?.length,
        direction: direction
      });
      
      // Handle fallback cases - if we got redirected to a different date
      if (data.date && data.requested_date && data.date !== data.requested_date) {
        console.log('Redirected from', data.requested_date, 'to', data.date);
        
        // Update to the actual date that was found
        const actualDate = new Date(data.date);
        this.dateManager.currentDate = actualDate;
        this.dateManager.updateDateDisplay();
        
        // Show a notification about the redirect
        this.showRedirectNotification(data.requested_date, data.date);
      } else if (data.cards && data.cards.length === 0) {
        // No papers found for the requested date
        this.showNoPapersNotification(data.requested_date);
      }
      
      // Show cache status if available
      if (data.cached) {
        this.showCacheNotification(data.cached_at);
      }
      
      this.cardRenderer.renderCards(data.cards || []);
      
    } catch (error) {
      console.error('Error loading papers:', error);
      this.cardRenderer.renderCards([]);
      
      // Show fallback message
      this.cardRenderer.cardsContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 48px; color: var(--text-muted);">
          <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
          <h3>Unable to load papers</h3>
          <p>Backend unavailable on static hosting. Try opening the daily page on Hugging Face:</p>
          <a class="action-btn primary" href="https://huggingface.co/papers/date/${encodeURIComponent(dateStr)}" target="_blank" rel="noreferrer">
            <i class="fas fa-external-link-alt"></i>Open on Hugging Face
          </a>
        </div>
      `;
    } finally {
      // Hide loading animation and update button states
      this.dateManager.hideLoading();
      await this.dateManager.updateDateDisplay();
    }
  }

  async startBatchEvaluation() {
    console.log('startBatchEvaluation called');
    
    const button = document.getElementById('batchEvaluateBtn');
    if (!button) {
      console.error('batchEvaluateBtn not found');
      return;
    }

    console.log('Found batchEvaluateBtn:', button);

    // Disable button and show loading state
    button.disabled = true;
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Starting...</span>';

    try {
      // Find all unevaluated evaluate buttons
      const unevaluatedButtons = document.querySelectorAll('.eval-button');
      console.log('Found eval buttons:', unevaluatedButtons.length);
      
      const buttonsToClick = [];
      
      unevaluatedButtons.forEach((evalButton, index) => {
        const evalText = evalButton.querySelector('.eval-text');
        console.log(`Button ${index}:`, evalText ? evalText.textContent : 'no text');
        if (evalText && (evalText.textContent === 'Evaluate' || evalText.textContent === 'Check')) {
          buttonsToClick.push(evalButton);
        }
      });
      
      console.log('Buttons to click:', buttonsToClick.length);
      
      if (buttonsToClick.length === 0) {
        console.log('No buttons to click');
        this.cardRenderer.showLogMessage('All papers have already been evaluated.', 'info');
        return;
      }

      this.cardRenderer.showLogMessage(`Starting batch evaluation of ${buttonsToClick.length} papers...`, 'info');

      // Click each evaluate button with delay
      for (let i = 0; i < buttonsToClick.length; i++) {
        const evalButton = buttonsToClick[i];
        
        // Update button text to show progress
        button.innerHTML = `<i class="fas fa-spinner fa-spin"></i><span>Starting ${i + 1} of ${buttonsToClick.length}</span>`;
        
        console.log(`Clicking button ${i + 1}:`, evalButton);
        // Simulate click on the evaluate button
        evalButton.click();
        
        // Add delay between clicks to avoid API overload
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      this.cardRenderer.showLogMessage(`Started evaluation for ${buttonsToClick.length} papers. They will complete in the background.`, 'success');

    } catch (error) {
      console.error('Batch evaluation error:', error);
      this.cardRenderer.showLogMessage(`Batch evaluation failed: ${error.message}`, 'error');
    } finally {
      // Restore button state
      button.disabled = false;
      button.innerHTML = originalContent;
    }
  }



  // Unified notification system
  showNotification(options) {
    const {
      type = 'info', // 'info', 'success', 'warning', 'error'
      title = '',
      message = '',
      duration = 4000,
      icon = null
    } = options;
    
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    });
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    
    // Set icon based on type if not provided
    let iconClass = icon;
    if (!iconClass) {
      switch (type) {
        case 'success':
          iconClass = 'fas fa-check-circle';
          break;
        case 'warning':
          iconClass = 'fas fa-exclamation-triangle';
          break;
        case 'error':
          iconClass = 'fas fa-times-circle';
          break;
        case 'info':
        default:
          iconClass = 'fas fa-info-circle';
          break;
      }
    }
    
    // Set colors based on type
    let borderColor = 'var(--accent-info)';
    let iconColor = 'var(--accent-info)';
    
    switch (type) {
      case 'success':
        borderColor = 'var(--accent-success)';
        iconColor = 'var(--accent-success)';
        break;
      case 'warning':
        borderColor = 'var(--accent-warning)';
        iconColor = 'var(--accent-warning)';
        break;
      case 'error':
        borderColor = 'var(--accent-danger)';
        iconColor = 'var(--accent-danger)';
        break;
    }
    
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--bg-primary);
      border: 1px solid ${borderColor};
      border-radius: 8px;
      padding: 16px;
      box-shadow: var(--shadow-lg);
      z-index: 1000;
      max-width: 350px;
      color: var(--text-primary);
      animation: slideInRight 0.3s ease;
    `;
    
    notification.innerHTML = `
      <div style="display: flex; align-items: flex-start; gap: 12px;">
        <i class="${iconClass}" style="color: ${iconColor}; font-size: 18px; margin-top: 2px; flex-shrink: 0;"></i>
        <div style="flex: 1; min-width: 0;">
          ${title ? `<div style="font-weight: 600; margin-bottom: 4px; color: var(--text-primary);">${title}</div>` : ''}
          ${message ? `<div style="font-size: 14px; color: var(--text-secondary); line-height: 1.4;">${message}</div>` : ''}
        </div>
      </div>
    `;
    
    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideInRight {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Remove notification after duration
    if (duration > 0) {
      setTimeout(() => {
        if (notification.parentNode) {
          notification.style.animation = 'slideInRight 0.3s ease reverse';
          setTimeout(() => {
            if (notification.parentNode) {
              notification.parentNode.removeChild(notification);
            }
          }, 300);
        }
      }, duration);
    }
    
    return notification;
  }

  // Convenience methods for different notification types
  showDateLimitNotification(message) {
    this.showNotification({
      type: 'warning',
      title: 'Date Limit',
      message: message,
      icon: 'fas fa-calendar-times'
    });
  }

  showNoPapersNotification(date) {
    this.showNotification({
      type: 'info',
      title: 'No Papers Found',
      message: `No papers available for ${date}. Try a different date.`,
      icon: 'fas fa-search'
    });
  }

  showRedirectNotification(requestedDate, actualDate) {
    this.showNotification({
      type: 'info',
      title: 'Date Redirected',
      message: `Papers for ${requestedDate} not available. Showing papers for ${actualDate}.`,
      icon: 'fas fa-arrow-right'
    });
  }

  showCacheNotification(cachedAt) {
    const cacheTime = new Date(cachedAt).toLocaleTimeString();
    this.showNotification({
      type: 'info',
      title: 'Cached Data',
      message: `Showing cached data from ${cacheTime}`,
      icon: 'fas fa-database',
      duration: 3000
    });
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new PaperIndexApp();
});


