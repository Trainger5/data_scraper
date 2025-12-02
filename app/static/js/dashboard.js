/**
 * Email Extractor Pro - Frontend Application
 * Custom Modern UI Version with Sidebar Navigation
 */

const API_BASE = '/api';
const POLL_INTERVAL = 2000;

let currentSearchId = null;
let pollInterval = null;
let isSearchRunning = false;
let stopButtonDefaultHTML = null;

const disableDuringRunSelectors = [
    '#webSearchInput', '#webSearchBtn',
    '#mapsBusinessType', '#mapsLocation', '#mapsPageCount', '#mapsCustomPageCount', '#mapsSearchBtn',
    '#socialSearchInput', '#socialPlatform', '#socialSearchBtn',
    '#crawlerUrl', '#crawlerDepth', '#crawlerMaxPages', '#crawlerBtn',
    '#platformType', '#platformQuery', '#platformTarget', '#platformBtn',
    '#globalSearchEngine', '#globalInfiniteScraping',
    '#scrapeEmails', '#scrapePhones'
];

function setControlsDisabled(disabled) {
    disableDuringRunSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        if (!elements || elements.length === 0) return;
        elements.forEach(el => {
            if ('disabled' in el) {
                el.disabled = disabled;
            }
        });
    });
}

function setRunningState(running) {
    isSearchRunning = running;
    setControlsDisabled(running);
    document.body.classList.toggle('app-disabled', running);

    const stopBtn = document.getElementById('stopCrawlBtn');
    if (stopBtn) {
        if (stopButtonDefaultHTML === null) {
            stopButtonDefaultHTML = stopBtn.innerHTML;
        }
        stopBtn.disabled = !running;
        if (!running) {
            stopBtn.innerHTML = stopButtonDefaultHTML;
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log("Dashboard app loaded");
    setupView();
    loadHistory();
    setRunningState(false);

    // Enter key support for inputs
    ['webSearchInput', 'mapsLocation', 'socialSearchInput', 'mapsCustomPageCount'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    if (id === 'webSearchInput') startSearch('web');
                    if (id === 'mapsLocation' || id === 'mapsCustomPageCount') startSearch('maps');
                    if (id === 'socialSearchInput') startSearch('social');
                }
            });
        }
    });

    // Event listener for Maps custom page count
    const mapsPageCountSelect = document.getElementById('mapsPageCount');
    const mapsCustomPageCountInput = document.getElementById('mapsCustomPageCount');

    if (mapsPageCountSelect && mapsCustomPageCountInput) {
        mapsPageCountSelect.addEventListener('change', function () {
            if (this.value === 'custom') {
                mapsCustomPageCountInput.style.display = 'block';
                mapsCustomPageCountInput.focus();
            } else {
                mapsCustomPageCountInput.style.display = 'none';
            }
        });
    }

    // Event listener for Platform type dropdown
    const platformTypeSelect = document.getElementById('platformType');
    const platformCustomGroup = document.getElementById('platformCustomGroup');

    if (platformTypeSelect && platformCustomGroup) {
        platformTypeSelect.addEventListener('change', function () {
            if (this.value === 'custom') {
                platformCustomGroup.style.display = 'block';
                document.getElementById('platformTarget')?.focus();
            } else {
                platformCustomGroup.style.display = 'none';
            }
        });
    }
});

// View Switching Logic
function setupView() {
    const params = new URLSearchParams(window.location.search);
    const view = params.get('view') || 'web';

    // Hide all panes
    const panes = document.querySelectorAll('.tab-content, .view-pane');
    panes.forEach(p => {
        p.style.display = 'none';
        p.classList.remove('active');
    });

    // Show active pane
    const activePane = document.getElementById(`${view}-pane`);
    if (activePane) {
        activePane.style.display = 'block';
        activePane.classList.add('active');
    }

    // Update Header
    const title = document.getElementById('pageTitle');
    const subtitle = document.getElementById('pageSubtitle');

    if (title && subtitle) {
        switch (view) {
            case 'web':
                title.textContent = 'Web Search';
                subtitle.textContent = 'Extract leads by searching keywords';
                break;
            case 'maps':
                title.textContent = 'Google Maps';
                subtitle.textContent = 'Target local businesses and extract contacts';
                break;
            case 'social':
                title.textContent = 'Social Media';
                subtitle.textContent = 'Find profiles from social networks';
                break;
            case 'crawler':
                title.textContent = 'Website Crawler';
                subtitle.textContent = 'Deep crawl a specific website for contacts';
                break;
            case 'platform':
                title.textContent = 'Platform Search';
                subtitle.textContent = 'Search within a specific platform or site';
                break;
        }
    }
}

// Start Search
function startSearch(type) {
    if (isSearchRunning) {
        alert('A crawl is already running. Please stop it before starting a new one.');
        return;
    }

    let payload = { search_type: type };
    let btnId = '';

    // Global Infinite Toggle
    const isInfinite = document.getElementById('globalInfiniteScraping')?.checked;

    // Get email/phone filter settings (default to true if checkboxes don't exist yet)
    const scrapeEmails = document.getElementById('scrapeEmails')?.checked !== false;
    const scrapePhones = document.getElementById('scrapePhones')?.checked !== false;

    if (type === 'web') {
        const query = document.getElementById('webSearchInput').value;
        if (!query.trim()) return alert('Please enter a search query');
        const engine = document.getElementById('globalSearchEngine')?.value || 'duckduckgo';
        payload.query = query;
        payload.engine = engine;
        payload.scrape_emails = scrapeEmails;
        payload.scrape_phones = scrapePhones;
        if (isInfinite) payload.max_pages = -1;
        btnId = 'webSearchBtn';
    }
    else if (type === 'maps') {
        const business = document.getElementById('mapsBusinessType').value;
        const location = document.getElementById('mapsLocation').value;
        if (!business.trim() || !location.trim()) return alert('Please enter both business type and location');
        const engine = document.getElementById('globalSearchEngine')?.value || 'google';
        let pageCount = document.getElementById('mapsPageCount')?.value;
        if (pageCount === 'custom') {
            pageCount = parseInt(document.getElementById('mapsCustomPageCount')?.value);
            if (!pageCount || pageCount < 1) return alert('Please enter a valid number of pages (minimum 1)');
        } else {
            pageCount = parseInt(pageCount) || 3;
        }
        payload.query = `${business} in ${location}`;
        payload.engine = engine;
        payload.page_count = pageCount;
        if (isInfinite) payload.max_pages = -1;
        btnId = 'mapsSearchBtn';
    }
    else if (type === 'social') {
        const query = document.getElementById('socialSearchInput').value;
        if (!query.trim()) return alert('Please enter a search query');
        const platform = document.getElementById('socialPlatform').value;
        const engine = document.getElementById('globalSearchEngine')?.value || 'duckduckgo';
        payload.query = query;
        payload.platform = platform;
        payload.engine = engine;
        payload.scrape_emails = scrapeEmails;
        payload.scrape_phones = scrapePhones;
        if (isInfinite) payload.max_pages = -1;
        btnId = 'socialSearchBtn';
    }
    else if (type === 'crawler') {
        const url = document.getElementById('crawlerUrl').value;
        if (!url.trim()) return alert('Please enter a target URL');
        const depth = parseInt(document.getElementById('crawlerDepth').value) || 2;
        const maxPages = parseInt(document.getElementById('crawlerMaxPages').value) || 50;
        payload.query = url;
        payload.depth = depth;
        payload.max_pages = isInfinite ? -1 : maxPages;
        btnId = 'crawlerBtn';
    }
    else if (type === 'platform') {
        const platformType = document.getElementById('platformType').value;
        const query = document.getElementById('platformQuery').value;
        if (!query.trim()) return alert('Please enter a search query');
        let target;
        if (platformType === 'yelp') {
            target = 'yelp.com';
        } else {
            target = document.getElementById('platformTarget').value;
            if (!target.trim()) return alert('Please enter a target website');
        }
        payload.query = `site:${target} ${query}`;
        payload.platform_type = platformType;
        payload.target_website = target;
        payload.engine = document.getElementById('globalSearchEngine')?.value || 'google';
        if (isInfinite) payload.max_pages = -1;
        btnId = 'platformBtn';
    }

    if (!btnId) return;

    setRunningState(true);

    // UI Feedback
    const btn = document.getElementById(btnId);
    const originalContent = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
    }

    // API Call
    fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);

            currentSearchId = data.search_id;
            showStatusSection();
            startPolling();

            if (btn) {
                btn.innerHTML = originalContent;
            }
        })
        .catch(error => {
            alert('Error: ' + error.message);
            setRunningState(false);
            if (btn) {
                btn.innerHTML = originalContent;
            }
        });
}

// Polling & Status
function showStatusSection() {
    document.getElementById('statusSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('statusSection').scrollIntoView({ behavior: 'smooth' });
}

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(() => {
        fetch(`${API_BASE}/status/${currentSearchId}`)
            .then(res => res.json())
            .then(data => {
                updateStatus(data);

                if (data.status === 'completed' || data.status === 'error' || data.status === 'stopped') {
                    setRunningState(false);
                    stopPolling();
                    loadResults();
                }
            })
            .catch(error => console.error('Polling error:', error));
    }, POLL_INTERVAL);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function stopCrawl() {
    if (!currentSearchId) {
        alert('No active search to stop');
        return;
    }

    // Disable stop button to prevent multiple clicks
    const stopBtn = document.getElementById('stopCrawlBtn');
    if (stopBtn) {
        stopBtn.disabled = true;
        stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
    }

    // Call the stop endpoint
    fetch(`${API_BASE}/stop/${currentSearchId}`, {
        method: 'POST'
    })
        .then(res => res.json())
        .then(data => {
            console.log('Stop response:', data);
            // Stop polling and load results
            stopPolling();
            setTimeout(() => {
                loadResults();
                setRunningState(false);
            }, 1000); // Give backend a second to finish cleanly
        })
        .catch(error => {
            console.error('Error stopping search:', error);
            alert('Failed to stop search: ' + error.message);
            if (stopBtn) {
                stopBtn.disabled = false;
                stopBtn.innerHTML = stopButtonDefaultHTML || '<i class="fas fa-stop"></i> Stop';
            }
        });
}

function updateStatus(data) {
    const progress = Math.min((data.pages_crawled / 20) * 100, 95);
    const bar = document.getElementById('progressFill');
    bar.style.width = progress + '%';

    document.getElementById('pagesCrawled').textContent = data.pages_crawled;
    document.getElementById('emailsFound').textContent = data.total_emails;
    const phonesEl = document.getElementById('phonesFound');
    if (phonesEl) {
        phonesEl.textContent = data.total_phones ?? 0;
    }

    let statusText = `Crawling...`;

    if (data.status === 'error' && data.error_message) {
        statusText = `Error: ${data.error_message}`;
        const statusEl = document.getElementById('statusText');
        statusEl.style.color = '#dc3545'; // Danger color
    } else if (data.current_url) {
        try {
            const url = new URL(data.current_url);
            statusText = `Scanning: ${url.hostname}`;
            document.getElementById('statusText').style.color = '';
        } catch (e) { }
    }
    document.getElementById('statusText').textContent = statusText;
}

// Results
function loadResults() {
    fetch(`${API_BASE}/results/${currentSearchId}`)
        .then(res => res.json())
        .then(data => {
            displayResults(data.results);

            // Show error if present
            const errorAlert = document.getElementById('errorAlert');
            if (data.search && data.search.error_message) {
                errorAlert.style.display = 'block';
                errorAlert.innerHTML = `<i class="fas fa-exclamation-circle"></i> <strong>Error:</strong> ${data.search.error_message}`;
            } else {
                errorAlert.style.display = 'none';
            }

            document.getElementById('statusSection').style.display = 'none';
            document.getElementById('resultsSection').style.display = 'block';
            document.getElementById('progressFill').style.width = '100%';
        })
        .catch(error => alert('Error loading results: ' + error.message));
}

function displayResults(results) {
    const tbody = document.getElementById('resultsBody');
    tbody.innerHTML = '';

    const emails = results.emails || [];
    const phones = results.phones || [];
    const businesses = results.businesses || [];

    document.getElementById('emailCount').textContent = `${emails.length} Emails`;
    document.getElementById('phoneCount').textContent = `${phones.length} Phones`;

    // Add business count badge if businesses exist
    let businessBadge = document.getElementById('businessCount');
    if (businesses.length > 0) {
        if (!businessBadge) {
            const header = document.querySelector('#resultsSection .card-header div:last-child');
            businessBadge = document.createElement('span');
            businessBadge.id = 'businessCount';
            businessBadge.className = 'badge badge-info';
            header.appendChild(businessBadge);
        }
        businessBadge.textContent = `${businesses.length} Businesses`;
        businessBadge.style.display = 'inline-block';
    } else if (businessBadge) {
        businessBadge.style.display = 'none';
    }

    const formatSource = (source) => {
        try {
            return new URL(source).hostname;
        } catch (e) {
            return source;
        }
    };

    // Display Businesses first (if any)
    businesses.forEach(item => {
        const row = tbody.insertRow();
        let details = `<strong>${item.name}</strong><br>`;
        if (item.address) details += `<small class="text-muted"><i class="fas fa-map-marker-alt"></i> ${item.address}</small><br>`;
        if (item.website) details += `<small><a href="${item.website}" target="_blank"><i class="fas fa-globe"></i> Website</a></small>`;

        let value = '';
        if (item.phone) value += `<div><i class="fas fa-phone"></i> ${item.phone}</div>`;

        row.innerHTML = `
            <td><span class="badge badge-info">Business</span></td>
            <td>
                ${details}
                ${value ? `<div style="margin-top: 0.5rem;">${value}</div>` : ''}
            </td>
            <td><span class="text-muted">${item.source || 'Yelp'}</span></td>
        `;
    });

    emails.forEach(item => {
        const row = tbody.insertRow();
        let details = `<div>${item.email}</div>`;

        // Add business info if available
        if (item.business_name) {
            details += `<div class="small mt-1"><strong>${item.business_name}</strong></div>`;
        }
        if (item.address) {
            details += `<div class="small text-muted"><i class="fas fa-map-marker-alt"></i> ${item.address}</div>`;
        }
        if (item.website) {
            details += `<div class="small"><a href="${item.website}" target="_blank"><i class="fas fa-globe"></i> Website</a></div>`;
        }

        row.innerHTML = `
            <td><span class="badge badge-primary">Email</span></td>
            <td>${details}</td>
            <td><span class="text-muted">${formatSource(item.source_url)}</span></td>
        `;
    });

    phones.forEach(item => {
        const row = tbody.insertRow();
        let details = `<div>${item.phone}</div>`;

        // Add business info if available
        if (item.business_name) {
            details += `<div class="small mt-1"><strong>${item.business_name}</strong></div>`;
        }
        if (item.address) {
            details += `<div class="small text-muted"><i class="fas fa-map-marker-alt"></i> ${item.address}</div>`;
        }
        if (item.website) {
            details += `<div class="small"><a href="${item.website}" target="_blank"><i class="fas fa-globe"></i> Website</a></div>`;
        }

        row.innerHTML = `
            <td><span class="badge badge-success">Phone</span></td>
            <td>${details}</td>
            <td><span class="text-muted">${formatSource(item.source_url)}</span></td>
        `;
    });

    if (emails.length === 0 && phones.length === 0 && businesses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center" style="padding: 2rem;">No results found</td></tr>';
    }
}

function exportResults(format) {
    if (!currentSearchId) {
        alert('Please perform a search first.');
        return;
    }
    window.location.href = `${API_BASE}/export/${currentSearchId}?format=${format}`;
}

// History
function loadHistory() {
    const grid = document.getElementById('historyGrid');
    if (!grid) return;

    fetch(`${API_BASE}/history?limit=6`)
        .then(res => res.json())
        .then(data => {
            if (!data.searches || data.searches.length === 0) {
                grid.innerHTML = `
                    <div class="col-12 text-center" style="padding: 3rem;">
                        <i class="fas fa-history" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
                        <p class="text-muted">No extraction history yet.</p>
                    </div>`;
                return;
            }

            grid.innerHTML = data.searches.map(search => `
                <div class="col-4">
                    <div class="glass-card" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <small class="text-muted">${new Date(search.created_at).toLocaleDateString()}</small>
                                <span class="badge badge-${getStatusColor(search.status)}">${search.status}</span>
                            </div>
                            <h4 style="font-size: 1.1rem; margin-bottom: 1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${search.query}">${search.query}</h4>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                            <small class="text-muted">
                                <i class="fas fa-envelope"></i> ${search.total_emails}
                                <span style="margin: 0 0.5rem;">|</span>
                                <i class="fas fa-file"></i> ${search.pages_crawled}
                            </small>
                            <button onclick="loadHistoryItem(${search.id})" class="btn btn-outline" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;">View</button>
                        </div>
                    </div>
                </div>
            `).join('');
        });
}

function getStatusColor(status) {
    if (status === 'completed') return 'success';
    if (status === 'error') return 'danger';
    return 'warning';
}

function stopCrawl() {
    if (!currentSearchId) {
        alert('No active crawl to stop');
        return;
    }

    if (!confirm('Stop crawling and show current results?')) return;

    // Call stop API
    const stopBtn = document.getElementById('stopCrawlBtn');
    if (stopBtn) {
        stopBtn.disabled = true;
        stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
    }

    fetch(`${API_BASE}/stop/${currentSearchId}`, {
        method: 'POST'
    })
        .then(res => res.json())
        .then(data => {
            console.log('Stop requested:', data);
            stopPolling();
            loadResults();
            setRunningState(false);
        })
        .catch(error => {
            console.error('Error stopping crawl:', error);
            alert('Error stopping crawl: ' + error.message);
            if (stopBtn && stopButtonDefaultHTML !== null) {
                stopBtn.disabled = false;
                stopBtn.innerHTML = stopButtonDefaultHTML;
            } else if (stopBtn) {
                stopBtn.disabled = false;
                stopBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
            }
        });
}

function loadHistoryItem(id) {
    currentSearchId = id;
    loadResults();
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}
