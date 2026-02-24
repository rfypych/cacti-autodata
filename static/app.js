/**
 * Cacti AutoData - Web Dashboard v3.0
 * Full client-side application logic with real feature parity to tkinter GUI.
 *
 * Features:
 * - Dashboard: scraping, progress, log, save log
 * - Settings: cookie, URL, time format, mapping editor, data rules
 * - Preview: per-sheet tabs, write to Excel
 * - Upload Form: auto-detect IDs, 24h peak scrape, preview table, upload
 * - Help: accordion sections
 */

// ============================================================
// STATE
// ============================================================
let appConfig = {};
let appSettings = {};
let eventSource = null;
let formEventSource = null;
let currentExcelPath = '';

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    // Default dates: today
    const today = new Date();
    const todayStr = formatDateInput(today);
    document.getElementById('startDate').value = todayStr;
    document.getElementById('endDate').value = todayStr;
    document.getElementById('formStartDate').value = todayStr;
    document.getElementById('formEndDate').value = todayStr;

    // Apply saved theme first (no flash)
    const savedTheme = localStorage.getItem('cacti-theme') || 'dark';
    applyTheme(savedTheme);

    loadConfig();
    loadSettings();
    checkSession();
});

// ============================================================
// THEME TOGGLE
// ============================================================
function applyTheme(theme) {
    if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        ['themeIcon', 'mobileThemeIcon'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '🌙';
        });
        const label = document.getElementById('themeLabel');
        if (label) label.textContent = 'Dark Mode';
    } else {
        document.documentElement.removeAttribute('data-theme');
        ['themeIcon', 'mobileThemeIcon'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '☀️';
        });
        const label = document.getElementById('themeLabel');
        if (label) label.textContent = 'Light Mode';
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    const next = current === 'light' ? 'dark' : 'light';
    localStorage.setItem('cacti-theme', next);
    applyTheme(next);
}

// ============================================================
// MOBILE SIDEBAR TOGGLE
// ============================================================
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const hamburger = document.getElementById('hamburgerBtn');
    const isOpen = sidebar.classList.contains('open');
    if (isOpen) {
        closeSidebar();
    } else {
        sidebar.classList.add('open');
        overlay.classList.add('show');
        hamburger.classList.add('open');
    }
}

function closeSidebar() {
    document.querySelector('.sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('show');
    const hamburger = document.getElementById('hamburgerBtn');
    if (hamburger) hamburger.classList.remove('open');
}

// ============================================================
// DATE HELPERS
// ============================================================
function formatDateInput(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function htmlDateToDisplay(dateStr) {
    // Convert YYYY-MM-DD → DD/MM/YYYY
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

// ============================================================
// API HELPERS
// ============================================================
async function apiFetch(url, options = {}) {
    try {
        const res = await fetch(url, options);
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || `HTTP ${res.status}`);
        }
        return data;
    } catch (e) {
        showToast(e.message, 'error');
        throw e;
    }
}

// ============================================================
// CONFIG & SETTINGS LOADING
// ============================================================
async function loadConfig() {
    try {
        appConfig = await apiFetch('/api/config');
        populateSheetSelector();
        updateStats();
        populateFormEntries();
    } catch (e) {
        console.error('Failed to load config:', e);
    }
}

async function loadSettings() {
    try {
        appSettings = await apiFetch('/api/settings');
        applySettingsToUI();
    } catch (e) {
        console.error('Failed to load settings:', e);
    }
}

function populateSheetSelector() {
    const container = document.getElementById('sheetSelector');
    container.innerHTML = '';

    const interfaces = appConfig.interfaces || {};
    const selected = appSettings.selected_sheets || {};

    for (const [key, sheetName] of Object.entries(interfaces)) {
        const isSelected = selected[sheetName] !== false;
        const chip = document.createElement('label');
        chip.className = `sheet-chip ${isSelected ? 'selected' : ''}`;
        chip.innerHTML = `
            <input type="checkbox" value="${sheetName}" ${isSelected ? 'checked' : ''}>
            ${sheetName}
        `;
        chip.addEventListener('click', () => {
            setTimeout(() => {
                const cb = chip.querySelector('input');
                chip.classList.toggle('selected', cb.checked);
            }, 0);
        });
        container.appendChild(chip);
    }
}

function updateStats() {
    const interfaces = appConfig.interfaces || {};
    const slots = appConfig.time_slots || [];
    document.getElementById('statInterfaces').textContent = Object.keys(interfaces).length;
    document.getElementById('statSlots').textContent = slots.length;
}

function applySettingsToUI() {
    // Server URL
    document.getElementById('settingUrl').value = appSettings.cacti_url || appConfig.cacti_url || '';

    // Time format radio
    const fmt = appSettings.time_format || 'dot';
    if (fmt === 'colon') {
        document.getElementById('timeColon').checked = true;
    } else {
        document.getElementById('timeDot').checked = true;
    }

    // Dashboard options
    setChecked('optSkipWeekends', appSettings.skip_weekends, true);
    setChecked('optSkipHolidays', appSettings.skip_holidays, false);
    setChecked('optSkipFilled', appSettings.skip_filled_rows, true);
    setChecked('optMetadata', appSettings.include_metadata, true);
    setChecked('optDryRun', appSettings.dry_run_mode, false);

    // Settings page options
    setChecked('setSkipWeekends', appSettings.skip_weekends, true);
    setChecked('setSkipHolidays', appSettings.skip_holidays, false);
    setChecked('setMetadata', appSettings.include_metadata, true);

    // Mapping editor
    populateMapping();
}

function setChecked(id, value, defaultValue) {
    const el = document.getElementById(id);
    if (el) el.checked = value !== undefined ? value : defaultValue;
}

function populateMapping() {
    const container = document.getElementById('mappingContainer');
    const mapping = appConfig.interfaces || {};
    const graphIds = appConfig.graph_ids || {};

    let html = '';
    for (const [iface, sheet] of Object.entries(mapping)) {
        const gid = graphIds[sheet] || graphIds[iface] || '-';
        html += `
            <div class="mapping-row">
                <span class="mapping-key">${iface}</span>
                <span class="mapping-arrow">→</span>
                <input type="text" class="mapping-input" data-interface="${iface}" value="${sheet}">
                <span class="mapping-gid">Graph ID: ${gid}</span>
            </div>
        `;
    }

    if (!html) {
        html = '<div class="empty-state"><p>Mapping belum dikonfigurasi. Periksa file config.py</p></div>';
    }

    container.innerHTML = html;
}

function populateFormEntries() {
    const entries = appConfig.google_form_entries || {};
    if (entries.tanggal) document.getElementById('entryTanggal').value = entries.tanggal;
    if (entries.total) document.getElementById('entryTotal').value = entries.total;
    if (entries.moratel) document.getElementById('entryMoratel').value = entries.moratel;
    if (entries.iforte) document.getElementById('entryIforte').value = entries.iforte;
    if (entries.telkom) document.getElementById('entryTelkom').value = entries.telkom;

    if (appConfig.google_form_url) {
        document.getElementById('formUrl').value = appConfig.google_form_url;
    }
}

// ============================================================
// SESSION STATUS
// ============================================================
async function checkSession() {
    const dot = document.getElementById('sessionDot');
    const text = document.getElementById('sessionText');
    const ageEl = document.getElementById('cookieAge');

    try {
        const data = await fetch('/api/session/status').then(r => r.json());
        if (data.exists) {
            dot.classList.add('active');
            if (data.age_seconds !== null) {
                const mins = Math.round(data.age_seconds / 60);
                if (mins < 60) {
                    text.textContent = `Session aktif`;
                    if (ageEl) ageEl.textContent = `Cookie diupdate ${mins} menit lalu`;
                } else {
                    const hours = Math.round(mins / 60);
                    text.textContent = `Session aktif`;
                    if (ageEl) ageEl.textContent = `Cookie diupdate ${hours} jam lalu`;
                }
            } else {
                text.textContent = 'Session aktif';
            }
        } else {
            dot.classList.remove('active');
            text.textContent = 'Belum ada cookie';
            if (ageEl) ageEl.textContent = 'Belum ada cookie tersimpan';
        }
    } catch (e) {
        dot.classList.remove('active');
        text.textContent = 'Server offline';
    }
}

// ============================================================
// SCRAPING (EXCEL MODE)
// ============================================================
async function startScraping() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    if (!startDate || !endDate) {
        showToast('Pilih tanggal mulai dan akhir terlebih dahulu!', 'warning');
        return;
    }

    // Selected sheets
    const selectedSheets = [];
    document.querySelectorAll('#sheetSelector input:checked').forEach(cb => {
        selectedSheets.push(cb.value);
    });
    if (selectedSheets.length === 0) {
        showToast('Pilih minimal satu sheet!', 'warning');
        return;
    }

    const payload = {
        start_date: htmlDateToDisplay(startDate),
        end_date: htmlDateToDisplay(endDate),
        excel_path: document.getElementById('excelPath').value.trim(),
        dry_run: document.getElementById('optDryRun').checked,
        demo_mode: document.getElementById('optDemoMode').checked,
        selected_sheets: selectedSheets,
        skip_weekends: document.getElementById('optSkipWeekends').checked,
        skip_holidays: document.getElementById('optSkipHolidays').checked,
        skip_filled_rows: document.getElementById('optSkipFilled').checked,
        include_metadata: document.getElementById('optMetadata').checked,
    };

    try {
        const data = await apiFetch('/api/scrape/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        currentExcelPath = data.excel_path || '';
        // Show auto-generated path hint
        if (currentExcelPath && !payload.excel_path) {
            document.getElementById('autoPathHint').style.display = 'block';
            document.getElementById('autoPathHint').innerHTML = `📁 File: <code>${currentExcelPath.split('/').pop()}</code>`;
        }

        showToast('Scraping dimulai! 🚀', 'success');

        // UI state
        document.getElementById('btnStart').disabled = true;
        document.getElementById('btnStop').disabled = false;
        document.getElementById('statStatus').textContent = '🔄 Running';
        document.getElementById('statStatusDetail').textContent = 'Scraping sedang berjalan...';

        // Clear log
        document.getElementById('logViewer').innerHTML = '';

        // Start SSE
        startLogStream();
    } catch (e) {
        // Error already shown by apiFetch
    }
}

async function stopScraping() {
    try {
        await fetch('/api/scrape/stop', { method: 'POST' });
        showToast('Menghentikan proses...', 'warning');
    } catch (e) {
        showToast('Gagal menghentikan: ' + e.message, 'error');
    }
}

function startLogStream() {
    if (eventSource) eventSource.close();

    eventSource = new EventSource('/api/scrape/logs');

    eventSource.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.progress !== undefined) {
            updateProgressUI(data.progress, data.status);
        }
        if (data.log) {
            addLogEntry(data.log, 'logViewer');
        }
        if (data.done) {
            onScrapingComplete();
            eventSource.close();
            eventSource = null;
        }
    };

    eventSource.onerror = function () {
        setTimeout(checkScrapingStatus, 2000);
    };
}

async function checkScrapingStatus() {
    try {
        const data = await apiFetch('/api/scrape/status');
        updateProgressUI(data.progress, data.status);
        if (!data.is_running) onScrapingComplete();
    } catch (e) { }
}

function updateProgressUI(percent, status) {
    document.getElementById('progressBar').style.width = percent + '%';
    document.getElementById('progressPercent').textContent = Math.round(percent) + '%';
    if (status) {
        document.getElementById('progressStatus').textContent = status;
    }
}

function addLogEntry(message, viewerId) {
    const viewer = document.getElementById(viewerId);
    const entry = document.createElement('div');
    entry.className = 'log-entry';

    // Color code
    if (message.includes('❌') || message.includes('Error') || message.includes('error')) {
        entry.classList.add('error');
    } else if (message.includes('✅') || message.includes('Sukses') || message.includes('Selesai') || message.includes('Berhasil')) {
        entry.classList.add('success');
    } else if (message.includes('⚠️') || message.includes('Warning')) {
        entry.classList.add('warning');
    }

    entry.textContent = message;
    viewer.appendChild(entry);
    viewer.scrollTop = viewer.scrollHeight;
}

function onScrapingComplete() {
    document.getElementById('btnStart').disabled = false;
    document.getElementById('btnStop').disabled = true;
    document.getElementById('statStatus').textContent = '✅ Done';
    document.getElementById('statStatusDetail').textContent = 'Selesai. Cek tab Preview untuk melihat data.';

    refreshPreview();
    showToast('Proses selesai! Cek tab Preview. ✅', 'success');
}

// ============================================================
// PREVIEW
// ============================================================
async function refreshPreview() {
    try {
        const data = await apiFetch('/api/preview');
        const sheets = data.sheets || {};
        const total = data.total || 0;

        document.getElementById('statCount').textContent = total;
        document.getElementById('previewCount').textContent = total > 0
            ? `${total} records dari ${Object.keys(sheets).length} sheet`
            : 'Belum ada data';

        document.getElementById('btnWriteExcel').disabled = total === 0;
        renderPreviewTabs(sheets);
    } catch (e) {
        // Error shown by apiFetch
    }
}

function renderPreviewTabs(sheets) {
    const tabNav = document.getElementById('previewTabNav');
    const tabContent = document.getElementById('previewTabContent');
    const sheetNames = Object.keys(sheets);

    if (sheetNames.length === 0) {
        tabNav.innerHTML = '';
        tabContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <p>Belum ada data. Jalankan scraping di Dashboard terlebih dahulu.</p>
            </div>
        `;
        return;
    }

    // Tabs
    tabNav.innerHTML = sheetNames.map((name, i) =>
        `<button class="tab-btn ${i === 0 ? 'active' : ''}"
                 onclick="switchPreviewTab('${name}')"
                 data-sheet="${name}">
            ${name} (${sheets[name].length})
        </button>`
    ).join('');

    // Content
    tabContent.innerHTML = sheetNames.map((name, i) => `
        <div class="tab-content ${i === 0 ? 'active' : ''}" data-sheet="${name}">
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Tanggal</th>
                            <th>Waktu</th>
                            <th>Cur In</th>
                            <th>Cur Out</th>
                            <th>Max In</th>
                            <th>Max Out</th>
                            <th>Avg In</th>
                            <th>Avg Out</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>${renderTableRows(sheets[name])}</tbody>
                </table>
            </div>
        </div>
    `).join('');
}

function renderTableRows(rows) {
    if (!rows || rows.length === 0) {
        return '<tr><td colspan="9" class="text-muted" style="text-align:center;padding:24px;">Tidak ada data</td></tr>';
    }

    let lastDate = '';
    return rows.map(row => {
        const displayDate = row.date === lastDate ? '' : row.date;
        lastDate = row.date;
        const statusClass = getStatusBadgeClass(row.status);

        return `<tr>
            <td>${displayDate}</td>
            <td>${row.time}</td>
            <td>${row.curr_in || '-'}</td>
            <td>${row.curr_out || '-'}</td>
            <td>${row.max_in || '-'}</td>
            <td>${row.max_out || '-'}</td>
            <td>${row.avg_in || '-'}</td>
            <td>${row.avg_out || '-'}</td>
            <td><span class="badge ${statusClass}">${row.status || 'Pending'}</span></td>
        </tr>`;
    }).join('');
}

function getStatusBadgeClass(status) {
    if (!status) return 'badge-pending';
    const s = status.toLowerCase();
    if (s.includes('new') || s.includes('baru')) return 'badge-new';
    if (s.includes('update')) return 'badge-updated';
    if (s.includes('skip')) return 'badge-skipped';
    return 'badge-pending';
}

function switchPreviewTab(sheetName) {
    document.querySelectorAll('#previewTabNav .tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.sheet === sheetName);
    });
    document.querySelectorAll('#previewTabContent .tab-content').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.sheet === sheetName);
    });
}

function clearPreview() {
    document.getElementById('previewTabNav').innerHTML = '';
    document.getElementById('previewTabContent').innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">📋</div>
            <p>Preview dikosongkan.</p>
        </div>
    `;
    document.getElementById('previewCount').textContent = 'Belum ada data';
    document.getElementById('btnWriteExcel').disabled = true;
    showToast('Preview dikosongkan', 'info');
}

// ============================================================
// EXCEL WRITE
// ============================================================
async function writeToExcel() {
    const excelPath = document.getElementById('excelPath').value.trim() || currentExcelPath;

    if (!excelPath) {
        showToast('Path file Excel belum ditentukan!', 'warning');
        return;
    }

    try {
        const data = await apiFetch('/api/excel/write', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ excel_path: excelPath })
        });

        showToast(data.message, 'success');
        refreshPreview();
    } catch (e) {
        // Error shown by apiFetch
    }
}

// ============================================================
// SAVE LOG (Download)
// ============================================================
function downloadLog() {
    window.location.href = '/api/logs/download';
    showToast('Log sedang diunduh...', 'info');
}

// ============================================================
// SETTINGS
// ============================================================
async function saveCookie() {
    const name = document.getElementById('cookieName').value;
    const value = document.getElementById('cookieValue').value.trim();

    if (!value) {
        showToast('Cookie value tidak boleh kosong!', 'warning');
        return;
    }

    try {
        const data = await apiFetch('/api/session/cookie', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cookie_name: name, cookie_value: value })
        });

        showToast('Cookie berhasil disimpan! 🔑', 'success');
        document.getElementById('cookieValue').value = '';
        checkSession();
    } catch (e) {
        // Error shown by apiFetch
    }
}

async function saveSettings() {
    const payload = {
        cacti_url: document.getElementById('settingUrl').value.trim(),
        time_format: document.querySelector('input[name="timeFormat"]:checked').value,
        skip_weekends: document.getElementById('setSkipWeekends').checked,
        skip_holidays: document.getElementById('setSkipHolidays').checked,
        include_metadata: document.getElementById('setMetadata').checked,
    };

    try {
        await apiFetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        showToast('Settings tersimpan! ⚙️', 'success');
        // Sync dashboard options too
        setChecked('optSkipWeekends', payload.skip_weekends);
        setChecked('optSkipHolidays', payload.skip_holidays);
        setChecked('optMetadata', payload.include_metadata);
    } catch (e) { }
}

async function saveMapping() {
    const inputs = document.querySelectorAll('.mapping-input');
    const mapping = {};
    inputs.forEach(input => {
        const iface = input.dataset.interface;
        mapping[iface] = input.value.trim();
    });

    try {
        await apiFetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ interface_mapping: mapping })
        });
        showToast('Mapping berhasil disimpan! 🗺️', 'success');

        // Refresh config to reflect changes
        appConfig.interfaces = mapping;
        populateSheetSelector();
    } catch (e) { }
}

async function resetSettings() {
    if (!confirm('Reset semua settings ke default? Tindakan ini tidak bisa dibatalkan.')) return;

    try {
        await apiFetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reset: true })
        });
        showToast('Settings telah direset ke default! 🔄', 'info');
        loadSettings();
        loadConfig();
    } catch (e) { }
}

// ============================================================
// UPLOAD FORM FEATURES
// ============================================================

// Auto Detect Google Form Entry IDs
async function autoDetectFormIds() {
    const url = document.getElementById('formUrl').value.trim();
    if (!url) {
        showToast('Masukkan URL Google Form terlebih dahulu!', 'warning');
        return;
    }

    const btn = document.getElementById('btnAutoDetect');
    btn.disabled = true;
    btn.textContent = '⏳ Detecting...';

    try {
        const data = await apiFetch('/api/form/detect-ids', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (data.method === 'auto' && data.mapping) {
            const m = data.mapping;
            if (m.tanggal) document.getElementById('entryTanggal').value = m.tanggal;
            if (m.total) document.getElementById('entryTotal').value = m.total;
            if (m.moratel) document.getElementById('entryMoratel').value = m.moratel;
            if (m.iforte) document.getElementById('entryIforte').value = m.iforte;
            if (m.telkom) document.getElementById('entryTelkom').value = m.telkom;
            showToast(`Berhasil mendeteksi ${Object.keys(m).length} field otomatis! ✅`, 'success');
        } else if (data.method === 'semi-auto') {
            showToast('Ditemukan entry IDs tetapi gagal mapping otomatis. Isi manual.', 'warning');
            addFormLog('Semi-auto: ' + (data.raw_entries || []).join(', '));
        }
    } catch (e) {
        // Error shown
    } finally {
        btn.disabled = false;
        btn.textContent = '🔍 Auto Detect IDs';
    }
}

// Scrape 24-hour peak data
async function scrapeFormPeak() {
    const startDate = document.getElementById('formStartDate').value;
    const endDate = document.getElementById('formEndDate').value;

    if (!startDate || !endDate) {
        showToast('Pilih tanggal mulai dan akhir!', 'warning');
        return;
    }

    const btn = document.getElementById('btnFormScrape');
    btn.disabled = true;
    btn.textContent = '⏳ Mengambil data...';

    // Clear preview table
    document.getElementById('formPreviewBody').innerHTML = `
        <tr><td colspan="6" class="text-muted" style="text-align:center; padding:24px;">
            ⏳ Mengambil data 24-jam... Mohon tunggu...
        </td></tr>
    `;
    document.getElementById('formLogViewer').innerHTML = '';

    try {
        await apiFetch('/api/form/scrape-peak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_date: htmlDateToDisplay(startDate),
                end_date: htmlDateToDisplay(endDate),
            })
        });

        // Start SSE for form logs
        startFormLogStream();

    } catch (e) {
        btn.disabled = false;
        btn.textContent = '🔍 Tarik Data & Preview';
    }
}

function startFormLogStream() {
    if (formEventSource) formEventSource.close();

    formEventSource = new EventSource('/api/form/scrape-logs');

    formEventSource.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.log) {
            addLogEntry(data.log, 'formLogViewer');
        }

        if (data.done) {
            formEventSource.close();
            formEventSource = null;
            onFormScrapeComplete();
        }
    };

    formEventSource.onerror = function () {
        setTimeout(async () => {
            try {
                const st = await apiFetch('/api/form/scrape-status');
                if (!st.running) onFormScrapeComplete();
            } catch (e) { }
        }, 2000);
    };
}

async function onFormScrapeComplete() {
    const btn = document.getElementById('btnFormScrape');
    btn.disabled = false;
    btn.textContent = '🔍 Tarik Data & Preview';

    // Fetch preview data
    try {
        const data = await apiFetch('/api/form/preview');
        renderFormPreview(data.rows || []);
    } catch (e) { }
}

function renderFormPreview(rows) {
    const tbody = document.getElementById('formPreviewBody');

    if (rows.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="6" class="text-muted" style="text-align:center; padding:24px;">
                Tidak ada data. Pastikan cookie valid dan coba lagi.
            </td></tr>
        `;
        document.getElementById('btnFormUpload').disabled = true;
        return;
    }

    tbody.innerHTML = rows.map((row, i) => `
        <tr>
            <td style="text-align:center;">
                <input type="checkbox" class="form-checkbox" data-date="${row.date}" ${row.checked ? 'checked' : ''}>
            </td>
            <td>${row.date}</td>
            <td style="font-weight:600; color:var(--text-accent);">${row.total}</td>
            <td>${row.moratel}</td>
            <td>${row.iforte}</td>
            <td>${row.telkom}</td>
        </tr>
    `).join('');

    document.getElementById('btnFormUpload').disabled = false;
    showToast(`Preview siap: ${rows.length} hari data teragregasi ✅`, 'success');
}

// Upload to Google Form
async function uploadToForm() {
    const formUrl = document.getElementById('formUrl').value.trim();
    if (!formUrl) {
        showToast('URL Google Form belum diisi!', 'warning');
        return;
    }

    // Gather entry mapping
    const entryMapping = {
        tanggal: document.getElementById('entryTanggal').value.trim(),
        total: document.getElementById('entryTotal').value.trim(),
        moratel: document.getElementById('entryMoratel').value.trim(),
        iforte: document.getElementById('entryIforte').value.trim(),
        telkom: document.getElementById('entryTelkom').value.trim(),
    };

    // Get checked dates
    const checkedDates = [];
    document.querySelectorAll('#formPreviewBody .form-checkbox:checked').forEach(cb => {
        checkedDates.push(cb.dataset.date);
    });

    if (checkedDates.length === 0) {
        showToast('Tidak ada tanggal yang dicentang!', 'warning');
        return;
    }

    const isDryRun = document.getElementById('formDryRun').checked;
    const modeText = isDryRun ? ' (TEST MODE)' : '';

    if (!isDryRun && !confirm(`Upload ${checkedDates.length} hari ke Google Form? Pastikan data sudah benar.`)) {
        return;
    }

    addFormLog(`========= MULAI UPLOAD${modeText} =========`);

    const btn = document.getElementById('btnFormUpload');
    btn.disabled = true;
    btn.textContent = '⏳ Mengupload...';

    try {
        const data = await apiFetch('/api/form/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                form_url: formUrl,
                entry_mapping: entryMapping,
                checked_dates: checkedDates,
                dry_run: isDryRun,
            })
        });

        // Log results
        if (data.results) {
            data.results.forEach(r => {
                const icon = r.success ? '✅' : '❌';
                addFormLog(`${icon} ${r.date}: ${r.message}`);
            });
        }

        addFormLog(`========= ${data.summary} =========`);
        showToast(data.summary, 'success');

    } catch (e) {
        // Error shown by apiFetch
    } finally {
        btn.disabled = false;
        btn.textContent = '▶️ Upload ke Google Form';
    }
}

function addFormLog(message) {
    const viewer = document.getElementById('formLogViewer');
    const entry = document.createElement('div');
    entry.className = 'log-entry';

    if (message.includes('❌') || message.includes('Error')) {
        entry.classList.add('error');
    } else if (message.includes('✅') || message.includes('Berhasil')) {
        entry.classList.add('success');
    } else if (message.includes('⚠️')) {
        entry.classList.add('warning');
    }

    const timestamp = new Date().toLocaleTimeString('id-ID');
    entry.textContent = `[${timestamp}] ${message}`;
    viewer.appendChild(entry);
    viewer.scrollTop = viewer.scrollHeight;
}

// ============================================================
// PAGE NAVIGATION
// ============================================================
function switchPage(pageName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });

    // Update sections
    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.toggle('active', section.id === `page-${pageName}`);
    });

    // Auto-close sidebar on mobile after nav
    if (window.innerWidth <= 768) closeSidebar();

    // Auto-refresh
    if (pageName === 'preview') refreshPreview();
}

// ============================================================
// ACCORDION (Help page)
// ============================================================
function toggleAccordion(headerEl) {
    const body = headerEl.nextElementSibling;
    const arrow = headerEl.querySelector('.accordion-arrow');

    body.classList.toggle('open');
    arrow.textContent = body.classList.contains('open') ? '▼' : '▶';
}

// ============================================================
// MODAL
// ============================================================
function openModal(id) {
    document.getElementById(id).classList.add('show');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-backdrop') && e.target.classList.contains('show')) {
        e.target.classList.remove('show');
    }
});

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================
function showToast(message, type = 'info', duration = 4500) {
    const container = document.getElementById('toastContainer');
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}
