/* ═══════════════════════════════════════════════════════════════════
   CLEANVERSE AI — Dashboard Controller
   Handles all UI logic, API calls, rendering, and agent log animation.
   ═══════════════════════════════════════════════════════════════════ */

'use strict';

// ─── Constants ───────────────────────────────────────────────────────────────
const API = '';   // Same-origin FastAPI — no prefix needed

const QUICK_FILL_DATA = [
  { text: 'Large pile of garbage near temple entrance. Plastic bags and food waste mixed. Very unhygienic. Pilgrims are being affected.',        location: 'Meenakshi Temple Area' },
  { text: 'Stagnant water overflowing from drainage near the market junction. Road flooded. Mosquito breeding visible. Urgent!',                location: 'Mattuthavani Market' },
  { text: 'Deep pothole on main road causing bike accidents. Multiple incidents today. Needs immediate repair.',                                  location: 'Tallakulam Junction' },
  { text: 'Thick black smoke from burning plastic waste near the overbridge. Air quality terrible. Children\'s school is 200m away.',            location: 'Goripalayam Overbridge' },
  { text: 'Street lights non-functional on the entire stretch. Very dangerous at night. Multiple robbery complaints reported.',                   location: 'Anna Nagar Main Road' },
];

const STATUS_COLORS = {
  pending:    '#ffd60a',
  analyzing:  '#00e5ff',
  dispatched: '#ffab40',
  resolved:   '#00e676',
};

const URGENCY_PILL_STYLE = {
  critical: 'background:rgba(255,23,68,0.18);color:#ff4d6d;border:1px solid rgba(255,23,68,0.4);',
  high:     'background:rgba(255,171,64,0.18);color:#ffab40;border:1px solid rgba(255,171,64,0.4);',
  medium:   'background:rgba(255,214,10,0.15);color:#ffd60a;border:1px solid rgba(255,214,10,0.3);',
  low:      'background:rgba(0,230,118,0.15);color:#00e676;border:1px solid rgba(0,230,118,0.3);',
};

const SCORE_CLASS = (score) => {
  if (score >= 75) return 'score-critical';
  if (score >= 55) return 'score-high';
  if (score >= 35) return 'score-medium';
  return 'score-low';
};

// ─── State ───────────────────────────────────────────────────────────────────
let _activeTab = 'dashboard';
let _lastPrediction = null;

// ─── Clock ───────────────────────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById('system-clock');
  const tick = () => {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('en-IN', { hour12: false });
  };
  tick();
  setInterval(tick, 1000);
}

// ─── Tab Navigation ──────────────────────────────────────────────────────────
function switchTab(tabName) {
  document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

  document.getElementById(`tab-${tabName}`).classList.add('active');
  document.getElementById(`nav-${tabName}`).classList.add('active');
  _activeTab = tabName;

  agentLog(`Tab switched → ${tabName.toUpperCase()}`, 'info');

  if (tabName === 'dashboard')   loadDashboard();
  if (tabName === 'complaints')  loadComplaints();
  if (tabName === 'prediction')  loadPredictions();
}

// ─── Agent Log ───────────────────────────────────────────────────────────────
function agentLog(msg, type = 'default') {
  const body = document.getElementById('agent-log-body');
  const now  = new Date().toLocaleTimeString('en-IN', { hour12: false });
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  entry.innerHTML = `<span class="log-time">[${now}]</span> ${msg}`;
  body.appendChild(entry);
  body.scrollTop = body.scrollHeight;
}

function toggleLog() {
  document.getElementById('agent-log').classList.toggle('open');
}

function clearLog() {
  document.getElementById('agent-log-body').innerHTML = '';
}

// ─── Format helpers ───────────────────────────────────────────────────────────
function timeAgo(isoStr) {
  if (!isoStr) return '';
  try {
    const diff = Date.now() - new Date(isoStr).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1)   return 'just now';
    if (m < 60)  return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24)  return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  } catch { return ''; }
}

function animateNumber(el, target, duration = 800, suffix = '') {
  const start = performance.now();
  const from  = 0;
  const step  = (ts) => {
    const progress = Math.min((ts - start) / duration, 1);
    const value    = Math.floor(from + (target - from) * easeOut(progress));
    el.textContent = value + suffix;
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

// ─── DASHBOARD ────────────────────────────────────────────────────────────────
async function loadDashboard() {
  agentLog('DecisionAgent → Fetching dashboard metrics…', 'info');

  try {
    const res  = await fetch(`${API}/dashboard`);
    const data = await res.json();

    agentLog(`✔ Dashboard loaded — ${data.totalComplaints} total reports`, 'success');

    // KPIs
    animateNumber(document.getElementById('kpi-total-val'),    data.totalComplaints);
    animateNumber(document.getElementById('kpi-critical-val'), data.urgencyCounts?.critical || 0);
    animateNumber(document.getElementById('kpi-clean-val'),    Math.round(data.cityCleanlinessIndex), 800, '/100');
    animateNumber(document.getElementById('kpi-resolved-val'), data.statusCounts?.resolved || 0);
    animateNumber(document.getElementById('kpi-avg-val'),      Math.round(data.averagePriorityScore), 800, '/100');

    renderPriorityList(data.topPriorityComplaints || []);
    renderStatusChart(data.statusCounts || {}, data.totalComplaints);
    renderCategoryGrid(data.categoryDistribution || {});

  } catch (err) {
    agentLog(`✘ Dashboard fetch error: ${err.message}`, 'error');
  }
}

function renderPriorityList(complaints) {
  const el = document.getElementById('priority-list');
  if (!complaints.length) {
    el.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;text-align:center;padding:1rem;">No incidents found.</p>';
    return;
  }

  el.innerHTML = complaints.map((c, i) => {
    const dec   = c.aiAnalysis?.decision || {};
    const score = dec.priorityScore || 0;
    const uk    = dec.urgencyKey || 'low';
    return `
      <div class="priority-item" onclick="openComplaintModal('${c.id}')">
        <div class="priority-rank">#${i + 1}</div>
        <div class="priority-info">
          <div class="priority-location">📍 ${c.location || 'Unknown'}</div>
          <div class="priority-text">${c.text || ''}</div>
        </div>
        <div class="priority-score-badge ${SCORE_CLASS(score)}">${score}</div>
      </div>`;
  }).join('');
}

function renderStatusChart(counts, total) {
  const el    = document.getElementById('status-chart');
  const order = ['pending', 'analyzing', 'dispatched', 'resolved'];
  const labels= { pending: '⏳ Pending', analyzing: '🤖 Analyzing', dispatched: '🚛 Dispatched', resolved: '✅ Resolved' };
  const max   = total || 1;

  el.innerHTML = order.map(key => {
    const val = counts[key] || 0;
    const pct = Math.round((val / max) * 100);
    return `
      <div class="status-bar-item">
        <div class="status-bar-label">
          <span class="status-bar-name">${labels[key]}</span>
          <span class="status-bar-count">${val} / ${total}</span>
        </div>
        <div class="status-bar-track">
          <div class="status-bar-fill" 
               style="width:${pct}%;background:${STATUS_COLORS[key] || '#fff'};box-shadow:0 0 8px ${STATUS_COLORS[key] || '#fff'}40;"
               data-pct="${pct}">
          </div>
        </div>
      </div>`;
  }).join('');
}

function renderCategoryGrid(cats) {
  const el = document.getElementById('category-grid');
  const EMOJI_MAP = {
    'Solid Waste Management':            '🗑️',
    'Road Infrastructure':               '🚧',
    'Water & Drainage':                  '💧',
    'Air Quality':                       '💨',
    'Noise Pollution':                   '🔊',
    'Encroachment & Illegal Occupation': '🚫',
    'Street Lighting':                   '💡',
    'Animal & Pest Control':             '🐾',
  };

  const entries = Object.entries(cats).sort((a, b) => b[1] - a[1]);
  if (!entries.length) {
    el.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;">No data yet.</p>';
    return;
  }

  el.innerHTML = entries.map(([name, count]) => `
    <div class="category-chip">
      <span class="category-chip-emoji">${EMOJI_MAP[name] || '📌'}</span>
      <div class="category-chip-info">
        <div class="category-chip-name">${name}</div>
        <div class="category-chip-count">${count}</div>
      </div>
    </div>`).join('');
}

// ─── COMPLAINTS ───────────────────────────────────────────────────────────────
async function loadComplaints() {
  agentLog('AnalyzerAgent → Streaming intelligence feed…', 'info');
  const grid    = document.getElementById('complaints-grid');
  const urgFilt = document.getElementById('filter-urgency')?.value || '';

  grid.innerHTML = `<div class="loading-spinner" style="grid-column:1/-1;"><div class="spinner"></div><span>Loading…</span></div>`;

  try {
    const res  = await fetch(`${API}/complaints?limit=100`);
    const data = await res.json();
    let   list = data.complaints || [];

    if (urgFilt) {
      list = list.filter(c => c.aiAnalysis?.decision?.urgencyKey === urgFilt);
    }

    agentLog(`✔ Intelligence feed loaded — ${list.length} entries`, 'success');

    if (!list.length) {
      grid.innerHTML = '<p style="color:var(--text-muted);font-size:0.82rem;padding:1rem;grid-column:1/-1;">No complaints match the current filter.</p>';
      return;
    }

    grid.innerHTML = list.map(c => renderComplaintCard(c)).join('');

  } catch (err) {
    agentLog(`✘ Feed error: ${err.message}`, 'error');
    grid.innerHTML = `<p style="color:var(--accent-red);padding:1rem;grid-column:1/-1;">${err.message}</p>`;
  }
}

function renderComplaintCard(c) {
  const dec  = c.aiAnalysis?.decision || {};
  const ai   = c.aiAnalysis || {};
  const uk   = dec.urgencyKey || 'low';
  const pill = URGENCY_PILL_STYLE[uk] || '';
  const score= dec.priorityScore || 0;
  const borderColor = { critical: '#ff4d6d', high: '#ffab40', medium: '#ffd60a', low: '#00e676' }[uk] || '#00e5ff';

  return `
    <div class="complaint-card" style="--border-color:${borderColor};" onclick="openComplaintModal('${c.id}')">
      <div class="complaint-card-header">
        <span class="complaint-card-category">${ai.categoryEmoji || '📌'} ${ai.category || 'Unknown'}</span>
        <span class="complaint-card-urgency" style="${pill}">${dec.urgencyLabel || uk.toUpperCase()}</span>
      </div>
      <div class="complaint-card-location">📍 ${c.location || 'Unknown Location'}</div>
      <div class="complaint-card-text">${c.text || '—'}</div>
      <div class="complaint-card-footer">
        <div class="complaint-card-score">
          <span class="complaint-status-dot" style="background:${STATUS_COLORS[c.status] || '#fff'};"></span>
          Priority: <strong>${score}/100</strong>
        </div>
        <div class="complaint-card-time">${timeAgo(c.createdAt)}</div>
      </div>
    </div>`;
}

// ─── PREDICTIONS ──────────────────────────────────────────────────────────────
async function loadPredictions() {
  agentLog('PredictionAgent → Running LSTM hotspot model…', 'info');

  const summaryEl  = document.getElementById('prediction-summary-card');
  const hotspotEl  = document.getElementById('hotspot-list');
  const mapEl      = document.getElementById('prediction-map');

  hotspotEl.innerHTML = `<div class="loading-spinner"><div class="spinner"></div><span>Running prediction model…</span></div>`;
  summaryEl.style.display = 'none';

  try {
    const res  = await fetch(`${API}/prediction`);
    const data = await res.json();
    _lastPrediction = data;

    agentLog(`✔ Prediction complete — CCI: ${data.cityCleanlinessIndex}/100, ${data.hotspots.length} hotspots`, 'success');

    // Summary
    summaryEl.innerHTML = `
      <strong>🔮 Forecast Summary</strong><br/>
      ${data.forecastSummary}<br/>
      <small style="color:var(--text-muted);display:block;margin-top:0.4rem;">
        ${data.modelVersion} · ${data.totalAnalyzed} complaints analysed · Generated ${timeAgo(data.generatedAt)}
      </small>`;
    summaryEl.style.display = 'block';

    renderHotspotList(data.hotspots);
    renderSVGMap(data.hotspots);

  } catch (err) {
    agentLog(`✘ Prediction error: ${err.message}`, 'error');
    hotspotEl.innerHTML = `<p style="color:var(--accent-red);padding:1rem;">${err.message}</p>`;
  }
}

function renderHotspotList(hotspots) {
  const el = document.getElementById('hotspot-list');
  const RISK_COL = (s) => s >= 70 ? '#ff4d6d' : s >= 50 ? '#ffab40' : s >= 30 ? '#ffd60a' : '#00e676';

  el.innerHTML = hotspots.map(h => `
    <div class="hotspot-item" onclick="showHotspotDetails(${h.rank})">
      <div class="hotspot-rank" style="color:${RISK_COL(h.riskScore)};">#${h.rank}</div>
      <div>
        <div class="hotspot-name">${h.zone}</div>
        <div class="hotspot-trend">${h.trendLabel} · ${h.complaintCount} reports</div>
      </div>
      <div class="hotspot-score" style="color:${RISK_COL(h.riskScore)};">${h.riskScore}</div>
    </div>`).join('');
}

function renderSVGMap(hotspots) {
  const container = document.getElementById('prediction-map');
  const W = container.clientWidth  || 560;
  const H = container.clientHeight || 420;

  // Map bounding box for Madurai (approx)
  const LAT_MIN = 9.895, LAT_MAX = 9.985;
  const LNG_MIN = 78.065, LNG_MAX = 78.145;

  const toX = (lng) => ((lng - LNG_MIN) / (LNG_MAX - LNG_MIN)) * (W - 80) + 40;
  const toY = (lat) => (1 - (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)) * (H - 80) + 40;

  const RISK_FILL = (s) => s >= 70 ? '#ff1744' : s >= 50 ? '#ff9f0a' : s >= 30 ? '#ffd60a' : '#00e676';

  const dots = hotspots.map(h => {
    const x = toX(h.lng);
    const y = toY(h.lat);
    const r = 6 + (h.riskScore / 100) * 14;
    const col = RISK_FILL(h.riskScore);
    return `
      <circle class="map-zone-dot" cx="${x}" cy="${y}" r="${r}"
        fill="${col}" fill-opacity="0.25" stroke="${col}" stroke-width="1.5"
        onclick="showHotspotDetails(${h.rank})">
        <title>${h.zone} — Risk: ${h.riskScore}/100</title>
      </circle>
      <circle cx="${x}" cy="${y}" r="3" fill="${col}" fill-opacity="0.9"/>
      <text class="map-label" x="${x}" y="${y - r - 4}"
        text-anchor="middle" font-size="8" fill="${col}" opacity="0.85">
        ${h.zone.split(' ')[0]}
      </text>`;
  }).join('');

  // Grid lines
  const grid = Array.from({ length: 5 }, (_, i) => {
    const y = 40 + i * ((H - 80) / 4);
    const x = 40 + i * ((W - 80) / 4);
    return `
      <line x1="40" y1="${y}" x2="${W - 40}" y2="${y}" stroke="rgba(0,229,255,0.06)" stroke-width="1"/>
      <line x1="${x}" y1="40" x2="${x}" y2="${H - 40}" stroke="rgba(0,229,255,0.06)" stroke-width="1"/>`;
  }).join('');

  container.innerHTML = `
    <svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="bg-grad" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stop-color="#0a1628"/>
          <stop offset="100%" stop-color="#050810"/>
        </radialGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <rect width="${W}" height="${H}" fill="url(#bg-grad)" rx="12"/>
      ${grid}
      <!-- City label -->
      <text x="${W/2}" y="24" text-anchor="middle" font-family="Outfit,sans-serif"
        font-size="11" fill="rgba(0,229,255,0.5)" letter-spacing="3" font-weight="700">
        MADURAI CITY GRID
      </text>
      <g filter="url(#glow)">${dots}</g>
      <!-- Legend -->
      <rect x="10" y="${H-60}" width="130" height="50" rx="6" fill="rgba(8,13,26,0.9)" stroke="rgba(0,229,255,0.1)" stroke-width="1"/>
      <circle cx="22" cy="${H-45}" r="5" fill="#ff1744" opacity="0.7"/>
      <text x="32" y="${H-41}" font-size="9" fill="#aaa" font-family="Outfit,sans-serif">Critical ≥70</text>
      <circle cx="22" cy="${H-30}" r="5" fill="#ff9f0a" opacity="0.7"/>
      <text x="32" y="${H-26}" font-size="9" fill="#aaa" font-family="Outfit,sans-serif">High ≥50</text>
      <circle cx="80" cy="${H-45}" r="5" fill="#ffd60a" opacity="0.7"/>
      <text x="90" y="${H-41}" font-size="9" fill="#aaa" font-family="Outfit,sans-serif">Medium ≥30</text>
      <circle cx="80" cy="${H-30}" r="5" fill="#00e676" opacity="0.7"/>
      <text x="90" y="${H-26}" font-size="9" fill="#aaa" font-family="Outfit,sans-serif">Low</text>
    </svg>`;
}

function showHotspotDetails(rank) {
  if (!_lastPrediction) return;
  const h = _lastPrediction.hotspots.find(x => x.rank === rank);
  if (!h) return;

  const RISK_COL = h.riskScore >= 70 ? '#ff4d6d' : h.riskScore >= 50 ? '#ffab40' : h.riskScore >= 30 ? '#ffd60a' : '#00e676';

  document.getElementById('modal-content').innerHTML = `
    <h2 style="font-size:1.2rem;font-weight:800;color:var(--text-primary);margin-bottom:0.3rem;">
      #${h.rank} — ${h.zone}
    </h2>
    <div style="color:var(--text-muted);font-size:0.75rem;margin-bottom:1.5rem;">
      ${h.lat.toFixed(4)}°N, ${h.lng.toFixed(4)}°E
    </div>

    <div class="ai-metrics-row" style="margin-bottom:1.5rem;">
      <div class="ai-metric">
        <div class="ai-metric-val" style="color:${RISK_COL};">${h.riskScore}</div>
        <div class="ai-metric-key">Risk Score</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val">${h.complaintCount}</div>
        <div class="ai-metric-key">Reports</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val">${h.predicted24h}</div>
        <div class="ai-metric-key">Pred. 24h</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val">${h.predicted7d}</div>
        <div class="ai-metric-key">Pred. 7d</div>
      </div>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">📈 Trend Analysis</div>
      <div class="ai-section-content">
        <strong>${h.trendLabel}</strong><br/>${h.trendDescription}
      </div>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">🚀 Recommended Action</div>
      <div class="xai-box">${h.recommendedAction}</div>
    </div>`;

  openModal();
}

// ─── COMPLAINT MODAL ──────────────────────────────────────────────────────────
async function openComplaintModal(id) {
  document.getElementById('modal-content').innerHTML = `
    <div class="loading-spinner"><div class="spinner"></div><span>Loading incident data…</span></div>`;
  openModal();

  try {
    const res = await fetch(`${API}/complaint/${id}`);
    if (!res.ok) throw new Error('Not found');
    const c   = await res.json();
    renderModalContent(c);
  } catch (err) {
    document.getElementById('modal-content').innerHTML =
      `<p style="color:var(--accent-red);">Error loading complaint: ${err.message}</p>`;
  }
}

function renderModalContent(c) {
  const ai   = c.aiAnalysis || {};
  const dec  = ai.decision  || {};
  const vis  = ai.visionResult || {};
  const plan = dec.actionPlan  || {};
  const uk   = dec.urgencyKey  || 'low';
  const pill = URGENCY_PILL_STYLE[uk] || '';

  const imageHtml = c.imageUrl
    ? `<img class="image-preview" src="${c.imageUrl}" alt="Incident photo"/>`
    : '';

  const stepsHtml = (plan.steps || []).map((s, i) =>
    `<li class="action-step"><span class="step-num">${String(i + 1).padStart(2, '0')}</span>${s}</li>`
  ).join('');

  const equipHtml = (plan.equipment || []).map(e =>
    `<span class="equip-tag">⚙️ ${e}</span>`
  ).join('');

  const visionHtml = vis.imageAnalyzed ? `
    <div class="ai-section">
      <div class="ai-section-title">👁️ Vision Agent Output</div>
      <div class="ai-metrics-row">
        <div class="ai-metric">
          <div class="ai-metric-val">${Math.round(vis.garbageProbability * 100)}%</div>
          <div class="ai-metric-key">Garbage Prob.</div>
        </div>
        <div class="ai-metric">
          <div class="ai-metric-val">${vis.estimatedVolume}m³</div>
          <div class="ai-metric-key">Est. Volume</div>
        </div>
        <div class="ai-metric">
          <div class="ai-metric-val" style="color:${vis.cleanlinessScore > 60 ? '#00e676' : '#ff4d6d'};">${vis.cleanlinessScore}</div>
          <div class="ai-metric-key">Clean Score</div>
        </div>
        <div class="ai-metric">
          <div class="ai-metric-val">${vis.hazardous ? '⚠️ YES' : '✅ NO'}</div>
          <div class="ai-metric-key">Hazardous</div>
        </div>
      </div>
      ${vis.riskFactors?.length ? `<div style="margin-top:0.6rem;font-size:0.75rem;color:var(--text-muted);">
        <strong>Risk Factors:</strong> ${vis.riskFactors.join(' · ')}
      </div>` : ''}
    </div>` : `
    <div class="ai-section">
      <div class="ai-section-title">👁️ Vision Agent</div>
      <div class="ai-section-content" style="color:var(--text-muted);font-size:0.8rem;">No image submitted — text analysis only.</div>
    </div>`;

  document.getElementById('modal-content').innerHTML = `
    <div style="margin-bottom:1rem;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">
        <div>
          <span style="font-size:0.72rem;color:var(--text-muted);">${ai.categoryEmoji || ''} ${ai.category || 'Complaint'}</span>
          <h2 style="font-size:1.1rem;font-weight:800;color:var(--text-primary);margin:0.3rem 0;">
            📍 ${c.location || 'Unknown Location'}
          </h2>
        </div>
        <span class="complaint-card-urgency" style="${pill};padding:0.35rem 0.9rem;border-radius:50px;font-size:0.75rem;font-weight:800;white-space:nowrap;">
          ${dec.urgencyLabel || uk.toUpperCase()}
        </span>
      </div>
      <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:0.5rem;line-height:1.6;">${c.text || ''}</p>
      ${imageHtml}
    </div>

    <div class="ai-metrics-row" style="margin-bottom:1.5rem;">
      <div class="ai-metric">
        <div class="ai-metric-val" style="color:${dec.urgencyColor || '#fff'};">${dec.priorityScore || '—'}</div>
        <div class="ai-metric-key">Priority Score</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val">${ai.severityScore || '—'}/10</div>
        <div class="ai-metric-key">Severity</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val">${dec.responseHours || '—'}h</div>
        <div class="ai-metric-key">Response SLA</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val" style="font-size:0.85rem;">₹${(plan.estimatedCostINR || 0).toLocaleString('en-IN')}</div>
        <div class="ai-metric-key">Est. Cost</div>
      </div>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">🧠 AI Analysis Summary</div>
      <div class="ai-section-content">${ai.summary || '—'}</div>
    </div>

    ${visionHtml}

    <div class="ai-section">
      <div class="ai-section-title">🏢 Assigned Department</div>
      <div class="ai-section-content"><strong>${dec.department || '—'}</strong></div>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">⚙️ Cleaning Action Plan — ${plan.method || ''}</div>
      <ul class="action-steps">${stepsHtml}</ul>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">🔧 Equipment Required</div>
      <div class="equipment-tags">${equipHtml}</div>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">🔍 Explainable AI (XAI) Reasoning</div>
      <div class="xai-box">${dec.xaiReasoning || '—'}</div>
    </div>

    <div style="margin-top:1rem;font-size:0.65rem;color:var(--text-muted);font-family:monospace;">
      ID: ${c.id} · ${c.isDemo ? '🧪 Demo Data' : '📡 Live Report'} · ${timeAgo(c.createdAt)}
    </div>`;
}

// ─── FORM SUBMISSION ──────────────────────────────────────────────────────────
document.getElementById('complaint-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const btn      = document.getElementById('submit-btn');
  const btnText  = document.getElementById('btn-text');
  const btnLoad  = document.getElementById('btn-loading');
  btn.disabled   = true;
  btnText.style.display = 'none';
  btnLoad.style.display = 'inline';

  agentLog('Complaint received → starting agent pipeline…', 'info');
  agentLog('AnalyzerAgent → Classifying complaint text…', 'info');

  try {
    const formData = new FormData(e.target);
    setTimeout(() => agentLog('VisionAgent → Processing image evidence…', 'info'),  600);
    setTimeout(() => agentLog('DecisionAgent → Computing priority score…', 'info'), 1200);

    const res  = await fetch(`${API}/complaint`, { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Server error');

    agentLog(`✔ Pipeline complete — Priority: ${data.aiAnalysis?.decision?.priorityScore}/100`, 'success');

    displayAIResponse(data.aiAnalysis, data.complaintId);

    // Reset form
    e.target.reset();
    document.getElementById('file-drop-content').innerHTML = `
      <span class="file-drop-icon">📷</span>
      <span>Click or drag image here</span>
      <span class="file-drop-hint">JPG, PNG, WebP · Max 10MB</span>`;

  } catch (err) {
    agentLog(`✘ Submission error: ${err.message}`, 'error');
    alert(`Error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btnText.style.display = 'inline';
    btnLoad.style.display = 'none';
  }
});

function displayAIResponse(ai, id) {
  const panel  = document.getElementById('ai-response-panel');
  const body   = document.getElementById('ai-response-body');
  const badge  = document.getElementById('ai-urgency-badge');
  const dec    = ai?.decision  || {};
  const vis    = ai?.visionResult || {};
  const plan   = dec.actionPlan || {};
  const uk     = dec.urgencyKey || 'low';
  const pill   = URGENCY_PILL_STYLE[uk] || '';

  badge.style.cssText = pill;
  badge.textContent   = dec.urgencyLabel || uk.toUpperCase();

  const stepsHtml = (plan.steps || []).slice(0, 4).map((s, i) =>
    `<li class="action-step"><span class="step-num">${String(i+1).padStart(2,'0')}</span>${s}</li>`
  ).join('');

  body.innerHTML = `
    <div class="ai-metrics-row" style="margin-bottom:1.2rem;">
      <div class="ai-metric">
        <div class="ai-metric-val" style="color:${dec.urgencyColor || '#fff'};">${dec.priorityScore || 0}</div>
        <div class="ai-metric-key">Priority Score</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val">${ai.severityScore || 0}/10</div>
        <div class="ai-metric-key">Severity</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val">${Math.round((ai.analyzerConfidence || 0) * 100)}%</div>
        <div class="ai-metric-key">AI Confidence</div>
      </div>
      <div class="ai-metric">
        <div class="ai-metric-val">${dec.responseHours || '—'}h</div>
        <div class="ai-metric-key">Response SLA</div>
      </div>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">🧠 Category</div>
      <div class="ai-section-content">${ai.categoryEmoji || ''} <strong>${ai.category || '—'}</strong> · ${ai.sentiment || ''}</div>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">📋 AI Summary</div>
      <div class="ai-section-content">${ai.summary || '—'}</div>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">⚙️ Top Action Steps</div>
      <ul class="action-steps">${stepsHtml}</ul>
    </div>

    <div class="ai-section">
      <div class="ai-section-title">🔍 XAI Reasoning</div>
      <div class="xai-box">${dec.xaiReasoning || '—'}</div>
    </div>

    <div style="margin-top:1rem;display:flex;gap:0.5rem;flex-wrap:wrap;">
      <button onclick="switchTab('complaints')" style="background:rgba(0,229,255,0.1);border:1px solid rgba(0,229,255,0.3);color:var(--accent-cyan);font-family:var(--font-main);font-size:0.78rem;font-weight:700;padding:0.5rem 1rem;border-radius:8px;cursor:pointer;">
        📡 View in Intelligence Feed
      </button>
      <button onclick="switchTab('prediction')" style="background:rgba(124,77,255,0.1);border:1px solid rgba(124,77,255,0.3);color:#b39ddb;font-family:var(--font-main);font-size:0.78rem;font-weight:700;padding:0.5rem 1rem;border-radius:8px;cursor:pointer;">
        🔮 View Prediction Engine
      </button>
    </div>`;

  panel.style.display = 'block';
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ─── Quick Fill ───────────────────────────────────────────────────────────────
function quickFill(idx) {
  const d = QUICK_FILL_DATA[idx];
  if (!d) return;
  document.getElementById('complaint-text').value     = d.text;
  document.getElementById('complaint-location').value = d.location;
  agentLog(`Quick fill applied: "${d.location}"`, 'info');
}

// ─── File Picker ──────────────────────────────────────────────────────────────
function handleFileSelect(input) {
  const file = input.files?.[0];
  if (!file) return;
  const url  = URL.createObjectURL(file);
  document.getElementById('file-drop-content').innerHTML = `
    <img src="${url}" style="max-height:80px;border-radius:6px;object-fit:contain;"/>
    <span style="font-size:0.72rem;color:var(--accent-cyan);">✔ ${file.name}</span>
    <span class="file-drop-hint">${(file.size / 1024).toFixed(1)} KB</span>`;
  agentLog(`Image selected: ${file.name} (${(file.size/1024).toFixed(1)} KB)`, 'success');
}

// Drag-and-drop
const dropZone = document.getElementById('file-drop-zone');
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--accent-cyan)'; });
dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = ''; });
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.style.borderColor = '';
  const file = e.dataTransfer.files?.[0];
  if (file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    document.getElementById('complaint-image').files = dt.files;
    handleFileSelect(document.getElementById('complaint-image'));
  }
});

// ─── Modal helpers ────────────────────────────────────────────────────────────
function openModal() { document.getElementById('complaint-modal').classList.add('open'); }
function closeModalDirect() { document.getElementById('complaint-modal').classList.remove('open'); }
function closeModal(e) { if (e.target.id === 'complaint-modal') closeModalDirect(); }

// ─── Boot ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  startClock();
  agentLog('CLEANVERSE AI — System boot sequence initiated…', 'info');
  agentLog('Agents: AnalyzerAgent · VisionAgent · DecisionAgent · PredictionAgent', 'info');
  agentLog('Firebase: initializing store…', 'info');

  setTimeout(() => {
    agentLog('✔ All systems online. Grid connected.', 'success');
  }, 600);

  loadDashboard();
});
