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

// Utility functions
function getParam(name) {
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

function parseMaybeJSON(str) {
  if (typeof str !== 'string') return str;
  try {
    return JSON.parse(str);
  } catch (e) {
    const start = str.indexOf('{');
    const end = str.lastIndexOf('}');
    if (start !== -1 && end !== -1 && end > start) {
      const sliced = str.slice(start, end + 1);
      try { return JSON.parse(sliced); } catch {}
    }
  }
  return str;
}

// Paper Evaluation Renderer
class PaperEvaluationRenderer {
  constructor() {
    this.themeManager = new ThemeManager();
    this.init();
  }

  init() {
    this.bindEvents();
  }

  bindEvents() {
    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        this.themeManager.toggle();
      });
    }
  }

  renderMetaGrid(meta, paperAuthors = '') {
    const metaGrid = document.getElementById('metaGrid');
    if (!metaGrid) return;
    
    const metaItems = [
      { label: 'Assessed At', value: meta.assessed_at || '-', icon: 'fas fa-calendar' },
      { label: 'Model', value: meta.model || '-', icon: 'fas fa-robot' },
      { label: 'Version', value: meta.version || '-', icon: 'fas fa-tag' },
      { label: 'Authors', value: paperAuthors || '-', icon: 'fas fa-users' },
      { label: 'Paper Path', value: meta.paper_path || '-', icon: 'fas fa-file-pdf', isLink: true }
    ];

    metaGrid.innerHTML = metaItems.map(item => `
      <div class="meta-item">
        <span class="meta-label">
          <i class="${item.icon}"></i>
          ${item.label}
        </span>
        <span class="meta-value">
          ${item.isLink && item.value !== '-' ? 
            `<a href="${esc(item.value)}" target="_blank">${esc(item.value)}</a>` : 
            esc(item.value)
          }
        </span>
      </div>
    `).join('');
  }

  renderDimensionCard(label, key, data, icon = 'fas fa-chart-bar') {
    const item = data[key] || {};
    const score = item.score !== undefined ? item.score : null;
    const probability = item.probability_pct !== undefined ? item.probability_pct : null;
    const analysis = item.analysis || '';
    
    const extras = [];
    if (Array.isArray(item.tools_models)) {
      extras.push(`<span class="meta-item"><i class="fas fa-tools"></i> Tools/Models: ${item.tools_models.map(esc).join(', ')}</span>`);
    }
    if (item.coverage_pct_estimate !== undefined) {
      extras.push(`<span class="meta-item"><i class="fas fa-percentage"></i> Coverage: ${esc(item.coverage_pct_estimate)}%</span>`);
    }

    return `
      <div class="dimension-card">
        <div class="dimension-header">
          <div class="dimension-title">
            <i class="${icon}"></i>
            ${esc(label)}
          </div>
          <div class="dimension-score">
            ${score !== null ? `<span class="score-badge">${score}</span>` : ''}
            ${probability !== null ? `<span class="score-badge probability">${probability}%</span>` : ''}
          </div>
        </div>
        ${extras.length > 0 ? `<div class="dimension-meta">${extras.join('')}</div>` : ''}
        ${analysis ? `<div class="dimension-analysis">${esc(analysis).replace(/\n/g, '<br/>')}</div>` : ''}
      </div>
    `;
  }

  async renderContent(json) {
    const contentEl = document.getElementById('content');
    const titleEl = document.getElementById('title');
    if (!contentEl || !titleEl) return;
    
    const meta = json.metadata || {};
    const paperId = getParam('id');
    
    // Fetch paper details from database
    let paperTitle = `Paper Evaluation - ${paperId}`;
    let paperAuthors = '';
    let paperAbstract = '';
    
    try {
      const response = await fetch(`/api/paper/${encodeURIComponent(paperId)}`);
      if (response.ok) {
        const paperData = await response.json();
        if (paperData.title) {
          paperTitle = paperData.title;
          paperAuthors = paperData.authors || '';
          paperAbstract = paperData.abstract || '';
        }
      }
    } catch (error) {
      console.error('Error fetching paper details:', error);
    }
    
    // Update title with actual paper title
    titleEl.textContent = paperTitle;
    
    // Render meta grid with paper info
    this.renderMetaGrid(meta, paperAuthors);

    // Executive Summary - styled like Hugging Face abstract
    const execSummary = json.executive_summary ? `
      <section class="evaluation-section">
        <div class="section-header">
          <h2><i class="fas fa-chart-pie"></i> Executive Summary</h2>
        </div>
        <div class="section-content">
          <div class="summary-card">
            <p class="summary-text">${esc(json.executive_summary)}</p>
          </div>
        </div>
      </section>
    ` : '';

    // Dimensions - create beautiful cards
    const d = parseMaybeJSON(json.dimensions) || {};
    const dims = [
      ['Task Formalization', 'task_formalization', 'fas fa-tasks'],
      ['Data & Resource Availability', 'data_resource_availability', 'fas fa-database'],
      ['Input-Output Complexity', 'input_output_complexity', 'fas fa-exchange-alt'],
      ['Real-World Interaction', 'real_world_interaction', 'fas fa-globe'],
      ['Existing AI Coverage', 'existing_ai_coverage', 'fas fa-robot'],
      ['Automation Barriers', 'automation_barriers', 'fas fa-shield-alt'],
      ['Human Originality', 'human_originality', 'fas fa-lightbulb'],
      ['Safety & Ethics', 'safety_ethics', 'fas fa-balance-scale'],
      ['Societal/Economic Impact', 'societal_economic_impact', 'fas fa-chart-line'],
      ['Technical Maturity Needed', 'technical_maturity_needed', 'fas fa-cogs'],
      ['3-Year Feasibility', 'three_year_feasibility', 'fas fa-calendar-alt'],
      ['Overall Automatability', 'overall_automatability', 'fas fa-magic'],
    ];

    const dimensionsHtml = dims.map(([label, key, icon]) => 
      this.renderDimensionCard(label, key, d, icon)
    ).join('');

    // Recommendations - styled sections
    const rec = json.recommendations || {};
    const renderList = (arr) => {
      return Array.isArray(arr) && arr.length ? 
        `<ul class="recommendation-list">${arr.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : 
        '<p class="no-data">No recommendations available.</p>';
    };

    const recommendationsHtml = `
      <section class="evaluation-section">
        <div class="section-header">
          <h2><i class="fas fa-lightbulb"></i> Recommendations</h2>
        </div>
        <div class="section-content">
          <div class="recommendations-grid">
            <div class="recommendation-card">
              <h3><i class="fas fa-user-graduate"></i> For Researchers</h3>
              ${renderList(rec.for_researchers)}
            </div>
            <div class="recommendation-card">
              <h3><i class="fas fa-university"></i> For Institutions</h3>
              ${renderList(rec.for_institutions)}
            </div>
            <div class="recommendation-card">
              <h3><i class="fas fa-cogs"></i> For AI Development</h3>
              ${renderList(rec.for_ai_development)}
            </div>
          </div>
        </div>
      </section>
    `;

    // Limitations
    const lim = Array.isArray(json.limitations_uncertainties) ? json.limitations_uncertainties : [];
    const limitationsHtml = `
      <section class="evaluation-section">
        <div class="section-header">
          <h2><i class="fas fa-exclamation-triangle"></i> Limitations & Uncertainties</h2>
        </div>
        <div class="section-content">
          <div class="limitations-card">
            ${lim.length ? `<ul class="limitations-list">${lim.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : '<p class="no-data">No limitations documented.</p>'}
          </div>
        </div>
      </section>
    `;

    // Add action buttons at the top
    const actionButtons = `
      <section class="evaluation-section">
        <div class="section-header">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2><i class="fas fa-chart-line"></i> Evaluation Actions</h2>
            <div class="action-buttons">
              <a href="/" class="action-btn primary">
                <i class="fas fa-arrow-left"></i>
                Back to Daily Papers
              </a>
            </div>
          </div>
        </div>
      </section>
    `;

    contentEl.innerHTML = actionButtons + execSummary + 
      `<section class="evaluation-section">
        <div class="section-header">
          <h2><i class="fas fa-chart-bar"></i> Detailed Dimensional Analysis</h2>
        </div>
        <div class="section-content">
          <div class="dimensions-grid">
            ${dimensionsHtml}
          </div>
        </div>
      </section>` + 
      recommendationsHtml + 
      limitationsHtml;
  }

  updateRadarChart(json) {
    const radarEl = document.getElementById('radar');
    const legendEl = document.getElementById('radar-legend');
    const overallScoreEl = document.getElementById('overallScore');
    
    if (!radarEl) return;
    
    try {
      const score = json.scorecard || {};
      const d = parseMaybeJSON(json.dimensions) || {};
      
      const labels = [
        'Task Formalization',
        'Data & Resources',
        'Input-Output Complexity',
        'Real-World Interaction',
        'Existing AI Coverage',
        'Human Originality',
        'Safety & Ethics',
        'Technical Maturity',
        '3-Year Feasibility',
        'Overall Automatability',
      ];
      
      const values = [
        Number(score.task_formalization ?? d.task_formalization?.score ?? 0),
        Number(score.data_resource_availability ?? d.data_resource_availability?.score ?? 0),
        Number(score.input_output_complexity ?? d.input_output_complexity?.score ?? 0),
        Number(score.real_world_interaction ?? d.real_world_interaction?.score ?? 0),
        Number(score.existing_ai_coverage ?? d.existing_ai_coverage?.score ?? 0),
        Number(score.human_originality ?? d.human_originality?.score ?? 0),
        Number(score.safety_ethics ?? d.safety_ethics?.score ?? 0),
        Number(score.technical_maturity_needed ?? d.technical_maturity_needed?.score ?? 0),
        Number((score.three_year_feasibility_pct ?? d.three_year_feasibility?.probability_pct ?? 0) / 25),
        Number(score.overall_automatability ?? d.overall_automatability?.score ?? 0),
      ];

      // Calculate overall score
      const validScores = values.filter(v => v > 0);
      const overallScore = validScores.length > 0 ? 
        (validScores.reduce((a, b) => a + b, 0) / validScores.length).toFixed(1) : '-';
      
      if (overallScoreEl) {
        overallScoreEl.innerHTML = `
          <span class="score-number">${overallScore}</span>
          <span class="score-label">Overall</span>
        `;
      }

      this.drawRadar(radarEl, labels, values, 4);
      this.setupRadarInteractions(radarEl);
      
      if (legendEl) {
        const labelConfig = [
          { abbr: 'TASK', color: '#3b82f6', full: 'Task Formalization' },
          { abbr: 'DATA', color: '#10b981', full: 'Data & Resources' },
          { abbr: 'I/O', color: '#f59e0b', full: 'Input-Output Complexity' },
          { abbr: 'REAL', color: '#8b5cf6', full: 'Real-World Interaction' },
          { abbr: 'AI', color: '#ef4444', full: 'Existing AI Coverage' },
          { abbr: 'HUMAN', color: '#06b6d4', full: 'Human Originality' },
          { abbr: 'SAFETY', color: '#84cc16', full: 'Safety & Ethics' },
          { abbr: 'TECH', color: '#f97316', full: 'Technical Maturity' },
          { abbr: '3YR', color: '#ec4899', full: '3-Year Feasibility' },
          { abbr: 'AUTO', color: '#6366f1', full: 'Overall Automatability' }
        ];
        
        legendEl.innerHTML = `
          <ul class="legend-list">
            ${labelConfig.map(config => `
              <li>
                <span class="legend-color" style="background-color: ${config.color}"></span>
                <span class="legend-abbr" style="color: ${config.color}; font-weight: bold;">${config.abbr}</span>
                <span class="legend-full">${esc(config.full)}</span>
              </li>
            `).join('')}
          </ul>
        `;
      }
    } catch (error) {
      console.error('Error updating radar chart:', error);
    }
  }

  setupRadarInteractions(canvas) {
    if (!canvas || !this.dotPositions) return;
    
    // Create tooltip element
    let tooltip = document.getElementById('radar-tooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.id = 'radar-tooltip';
      tooltip.className = 'radar-tooltip';
      document.body.appendChild(tooltip);
    }
    
    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      // Check if mouse is near any dot
      let hoveredDot = null;
      const hoverRadius = 15;
      
      for (const dot of this.dotPositions) {
        const distance = Math.sqrt((x - dot.x) ** 2 + (y - dot.y) ** 2);
        if (distance <= hoverRadius) {
          hoveredDot = dot;
          break;
        }
      }
      
      if (hoveredDot) {
        tooltip.style.display = 'block';
        tooltip.style.left = e.clientX + 10 + 'px';
        tooltip.style.top = e.clientY - 30 + 'px';
        tooltip.innerHTML = `
          <div class="tooltip-content">
            <span class="tooltip-abbr" style="color: ${hoveredDot.config.color}">${hoveredDot.config.abbr}</span>
            <span class="tooltip-full">${hoveredDot.config.full || ''}</span>
          </div>
        `;
        canvas.style.cursor = 'pointer';
      } else {
        tooltip.style.display = 'none';
        canvas.style.cursor = 'default';
      }
    };
    
    const handleMouseLeave = () => {
      tooltip.style.display = 'none';
      canvas.style.cursor = 'default';
    };
    
    // Remove existing listeners
    canvas.removeEventListener('mousemove', handleMouseMove);
    canvas.removeEventListener('mouseleave', handleMouseLeave);
    
    // Add new listeners
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);
  }

  drawRadar(canvas, labels, values, maxValue) {
    if (!canvas || !canvas.getContext) return;
    
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    
    const cx = w / 2, cy = h / 2, radius = Math.min(w, h) * 0.42;
    const n = values.length;
    const angleStep = (Math.PI * 2) / n;

    // Get theme colors
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? '#475569' : '#e2e8f0';
    const axisColor = isDark ? '#64748b' : '#cbd5e1';
    const fillColor = isDark ? 'rgba(34, 211, 238, 0.2)' : 'rgba(59, 130, 246, 0.2)';
    const strokeColor = isDark ? '#22d3ee' : '#3b82f6';
    const textColor = isDark ? '#e2e8f0' : '#475569';
    
    // Define colors and abbreviations for each dimension
    const labelConfig = [
      { color: '#3b82f6', abbr: 'TASK' },      // Task Formalization
      { color: '#10b981', abbr: 'DATA' },      // Data & Resources
      { color: '#f59e0b', abbr: 'I/O' },       // Input-Output Complexity
      { color: '#8b5cf6', abbr: 'REAL' },      // Real-World Interaction
      { color: '#ef4444', abbr: 'AI' },        // Existing AI Coverage
      { color: '#06b6d4', abbr: 'HUMAN' },     // Human Originality
      { color: '#84cc16', abbr: 'SAFETY' },    // Safety & Ethics
      { color: '#f97316', abbr: 'TECH' },      // Technical Maturity
      { color: '#ec4899', abbr: '3YR' },       // 3-Year Feasibility
      { color: '#6366f1', abbr: 'AUTO' }       // Overall Automatability
    ];

    // Store dot positions for mouse interaction
    this.dotPositions = [];

    // Draw grid (5 rings)
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    for (let r = 1; r <= 5; r++) {
      const rr = (radius * r) / 5;
      ctx.beginPath();
      for (let i = 0; i < n; i++) {
        const ang = i * angleStep - Math.PI / 2;
        const x = cx + rr * Math.cos(ang);
        const y = cy + rr * Math.sin(ang);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = axisColor;
    for (let i = 0; i < n; i++) {
      const ang = i * angleStep - Math.PI / 2;
      const x = cx + radius * Math.cos(ang);
      const y = cy + radius * Math.sin(ang);
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.stroke();
    }

    // Draw polygon
    ctx.fillStyle = fillColor;
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const v = Math.max(0, Math.min(maxValue, Number(values[i] || 0)));
      const r = (v / maxValue) * radius;
      const ang = i * angleStep - Math.PI / 2;
      const x = cx + r * Math.cos(ang);
      const y = cy + r * Math.sin(ang);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Draw axis endpoints with colored dots and store positions
    for (let i = 0; i < n; i++) {
      const ang = i * angleStep - Math.PI / 2;
      const x = cx + radius * Math.cos(ang);
      const y = cy + radius * Math.sin(ang);
      
      // Store position for mouse interaction
      this.dotPositions[i] = { x, y, index: i, config: labelConfig[i] };
      
      // Draw colored dot at the end of each axis
      const dotRadius = 6; // Slightly larger for better hover detection
      ctx.fillStyle = labelConfig[i]?.color || textColor;
      ctx.beginPath();
      ctx.arc(x, y, dotRadius, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw white border around dot
      ctx.strokeStyle = isDark ? '#1e293b' : '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }

  async render(json) {
    await this.renderContent(json);
    this.updateRadarChart(json);
  }
}

// Main Application
class PaperEvaluationApp {
  constructor() {
    this.renderer = new PaperEvaluationRenderer();
    this.paperId = getParam('id');
    this.init();
  }



  async init() {
    const id = getParam('id');
    console.log('PaperEvaluationApp init with ID:', id);
    
    if (!id) {
      const contentEl = document.getElementById('content');
      if (contentEl) {
        contentEl.innerHTML = `
          <div style="text-align: center; padding: 48px; color: var(--text-muted);">
            <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
            <h3>Missing Paper ID</h3>
            <p>Please provide a valid paper ID in the URL.</p>
          </div>
        `;
      }
      return;
    }

    try {
      console.log('Fetching evaluation for ID:', id);
      const response = await fetch(`/api/eval/${encodeURIComponent(id)}`);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`Evaluation not found: ${response.status}`);
      }
      
      const json = await response.json();
      console.log('Received JSON data:', Object.keys(json));
      
      // Fix stringified dimensions
      if (json && typeof json.dimensions === 'string') {
        try { 
          json.dimensions = JSON.parse(json.dimensions); 
          console.log('Successfully parsed dimensions JSON');
        } catch (e) {
          console.warn('Failed to parse dimensions JSON:', e);
        }
      }
      
      console.log('Rendering evaluation...');
      await this.renderer.render(json);
      console.log('Evaluation rendered successfully');
      
    } catch (error) {
      console.error('Error loading evaluation:', error);
      const contentEl = document.getElementById('content');
      if (contentEl) {
        contentEl.innerHTML = `
          <div style="text-align: center; padding: 48px; color: var(--text-muted);">
            <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
            <h3>Evaluation Not Found</h3>
            <p>The requested evaluation could not be loaded: ${error.message}</p>
            <a href="/" class="action-btn primary" style="margin-top: 16px; display: inline-flex; align-items: center; gap: 8px;">
              <i class="fas fa-arrow-left"></i>Back to Daily Papers
            </a>
          </div>
        `;
      }
    }
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.paperApp = new PaperEvaluationApp();
});


