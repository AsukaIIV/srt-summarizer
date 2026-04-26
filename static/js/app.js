// ============================================================
// SRT-SUMMARIZER Web App — Main Script
// ============================================================

// ---- Tab Switching ----

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            const panel = document.getElementById(targetId);
            if (panel) {
                panel.classList.remove('hidden');
                panel.classList.add('active');
            }
        });
    });

    loadProviders();
    loadConfig();
    refreshNavStatus();
    setTimeout(autoValidateConfig, 500);
});

function switchToTab(tabId) {
    const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    if (btn) btn.click();
}

// ---- Toast ----

function showToast(msg, type) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + (type || 'info');
    toast.textContent = msg;
    toast.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);padding:12px 24px;'
        + 'border-radius:12px;font-size:13px;font-weight:500;z-index:9999;'
        + 'box-shadow:0 4px 8px rgba(0,0,0,0.10),0 1px 4px rgba(66,104,232,0.10);'
        + 'animation:toastSlideUp 0.35s ease;'
        + (type === 'error' ? 'background:#FFDAD6;color:#410002;border:1px solid #FFB4AB;' :
           type === 'success' ? 'background:#C3F5D2;color:#00210D;border:1px solid #7BD89E;' :
           'background:#E9E4E3;color:#1C1B1F;border:1px solid #C5C5CC;');
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ---- API Helpers ----

async function apiGet(url) {
    const resp = await fetch(url);
    if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || resp.statusText);
    }
    return resp.json();
}

async function apiPost(url, body) {
    const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || resp.statusText);
    }
    return resp.json();
}

async function apiDelete(url, body) {
    const resp = await fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(txt || resp.statusText);
    }
    return resp.json();
}

// ---- Config / API Settings Tab ----

let _providers = [];
let _providerMemory = {};  // {provider_key: {model, base_url, api_key}}

async function loadProviders() {
    try {
        _providers = await apiGet('/api/providers');
        const sel = document.getElementById('provider-select');
        sel.innerHTML = _providers.map(p =>
            `<option value="${p.key}">${p.label}</option>`
        ).join('');
        sel.addEventListener('change', onProviderChange);
    } catch (e) {
        console.error('loadProviders:', e);
    }
}

async function loadConfig() {
    try {
        const cfg = await apiGet('/api/config');
        document.getElementById('provider-select').value = cfg.provider || 'deepseek';
        document.getElementById('model-input').value = cfg.model || '';
        document.getElementById('url-input').value = cfg.base_url || '';
        document.getElementById('key-input').value = '';
        document.getElementById('out-dir').value = cfg.output_dir || '';
        document.getElementById('course-name').value = cfg.course_name || '';

        // Build provider memory: defaults overridden by saved per-provider settings
        for (const p of _providers) {
            _providerMemory[p.key] = {
                model: (cfg.provider_models && cfg.provider_models[p.key]) || p.default_model,
                base_url: (cfg.provider_urls && cfg.provider_urls[p.key]) || p.base_url,
                api_key: '',
                has_key: (cfg.provider_api_keys_present && cfg.provider_api_keys_present[p.key]) || false,
                masked_key: (cfg.provider_masked_keys && cfg.provider_masked_keys[p.key]) || '',
            };
        }
        // Restore key indicator for current provider
        const cur = document.getElementById('provider-select').value;
        updateApiKeyIndicator(cur);

        // Sync current provider fields, preserving has_key and masked_key
        const curMem = _providerMemory[cur] || {};
        _providerMemory[cur] = {
            model: document.getElementById('model-input').value,
            base_url: document.getElementById('url-input').value,
            api_key: document.getElementById('key-input').value,
            has_key: curMem.has_key || false,
            masked_key: curMem.masked_key || '',
        };
        document.getElementById('provider-select').dataset.prev = cur;

        // Save-to-source state
        if (cfg.save_to_source) {
            document.getElementById('btn-save-to-src').classList.add('on');
            document.getElementById('btn-save-to-src').classList.remove('off');
            document.getElementById('btn-save-to-src').textContent = '输出到源目录：开';
            document.getElementById('output-hint').textContent = '输出将保存到各源文件所在目录';
            document.getElementById('out-dir').disabled = true;
            document.getElementById('btn-browse-out').disabled = true;
        }
    } catch (e) {
        console.error('loadConfig:', e);
    }
}

function onProviderChange() {
    const cur = document.getElementById('provider-select').value;
    const prev = document.getElementById('provider-select').dataset.prev || cur;
    // Save current fields to memory, preserving has_key and masked_key
    const prevMem = _providerMemory[prev] || {};
    _providerMemory[prev] = {
        model: document.getElementById('model-input').value,
        base_url: document.getElementById('url-input').value,
        api_key: document.getElementById('key-input').value,
        has_key: prevMem.has_key || false,
        masked_key: prevMem.masked_key || '',
    };
    // Restore new provider's memory
    const mem = _providerMemory[cur] || {};
    document.getElementById('model-input').value = mem.model || '';
    document.getElementById('url-input').value = mem.base_url || '';
    document.getElementById('key-input').value = mem.api_key || '';
    document.getElementById('provider-select').dataset.prev = cur;
    updateApiKeyIndicator(cur);
}

function maskApiKey(key) {
    if (!key || key.length <= 8) return key ? '*'.repeat(key.length) : '';
    return key.substring(0, 4) + '*'.repeat(key.length - 8) + key.substring(key.length - 4);
}

function updateApiKeyIndicator(providerKey) {
    const keyInput = document.getElementById('key-input');
    const mem = _providerMemory[providerKey];
    if (mem && mem.has_key && mem.masked_key) {
        keyInput.value = '';
        keyInput.placeholder = mem.masked_key;
    } else {
        keyInput.placeholder = 'API Key';
    }
}

async function saveConfig() {
    try {
        const provider = document.getElementById('provider-select').value;
        const keyValue = document.getElementById('key-input').value;
        await apiPost('/api/config', {
            provider: provider,
            model: document.getElementById('model-input').value,
            base_url: document.getElementById('url-input').value,
            api_key: keyValue,
            output_dir: document.getElementById('out-dir').value,
            save_to_source: document.getElementById('btn-save-to-src').classList.contains('on'),
            course_name: document.getElementById('course-name').value,
        });
        if (keyValue && _providerMemory[provider]) {
            _providerMemory[provider].has_key = true;
            _providerMemory[provider].masked_key = maskApiKey(keyValue);
        }
        updateApiKeyIndicator(provider);
        refreshNavStatus();
        showToast('配置已保存', 'success');
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

async function testConfig() {
    const msgEl = document.getElementById('config-validation-msg');
    msgEl.classList.remove('hidden', 'success', 'error');
    msgEl.classList.add('info');
    msgEl.textContent = '正在测试...';
    const provider = document.getElementById('provider-select').value;
    const keyValue = document.getElementById('key-input').value;
    try {
        // Test first without saving
        const result = await apiPost('/api/config/test', {
            provider: provider,
            model: document.getElementById('model-input').value,
            base_url: document.getElementById('url-input').value,
            api_key: keyValue,
            output_dir: '',
            save_to_source: false,
            course_name: '',
        });
        msgEl.classList.remove('info');
        if (result.ok) {
            // Test passed — now save
            await apiPost('/api/config', {
                provider: provider,
                model: document.getElementById('model-input').value,
                base_url: document.getElementById('url-input').value,
                api_key: keyValue,
                output_dir: document.getElementById('out-dir').value,
                save_to_source: document.getElementById('btn-save-to-src').classList.contains('on'),
                course_name: document.getElementById('course-name').value,
            });
            if (keyValue && _providerMemory[provider]) {
                _providerMemory[provider].has_key = true;
                _providerMemory[provider].masked_key = maskApiKey(keyValue);
            }
            updateApiKeyIndicator(provider);
            msgEl.classList.add('success');
            msgEl.textContent = '✓ 连接成功 — 配置已保存';
        } else {
            msgEl.classList.add('error');
            msgEl.textContent = '✗ ' + result.message;
        }
        refreshNavStatus();
    } catch (e) {
        msgEl.classList.remove('info');
        msgEl.classList.add('error');
        msgEl.textContent = '✗ 测试失败: ' + e.message;
    }
}

// ---- Nav Status ----

async function refreshNavStatus() {
    try {
        const result = await apiGet('/api/config/status');
        const chip = document.getElementById('nav-config-chip');
        chip.textContent = result.label;
        chip.className = 'chip';
        if (result.status === 'ok') {
            chip.classList.add('chip-ok');
        } else {
            chip.classList.add('chip-warn');
        }

        const cfg = await apiGet('/api/config');
        const providerBadge = document.getElementById('nav-provider-badge');
        const label = cfg.provider_labels[cfg.provider] || cfg.provider;
        providerBadge.textContent = label + ' · ' + cfg.model;
        providerBadge.className = 'chip chip-info';
    } catch (e) {
        console.error('refreshNavStatus:', e);
    }
}

async function autoValidateConfig() {
    try {
        const result = await apiGet('/api/config/status');
        if (result.status === 'error') {
            switchToTab('tab-config');
            const msgEl = document.getElementById('config-validation-msg');
            msgEl.classList.remove('hidden');
            msgEl.classList.add('error');
            msgEl.textContent = 'API 配置缺失或无效，请先完成 API 设置。';
        }
    } catch (e) {
        console.error('autoValidateConfig:', e);
    }
}

// ---- Save-to-Source Toggle ----

function toggleSaveToSource() {
    const btn = document.getElementById('btn-save-to-src');
    const isOn = btn.classList.contains('on');
    if (isOn) {
        btn.classList.remove('on');
        btn.classList.add('off');
        btn.textContent = '输出到源目录：关';
        document.getElementById('output-hint').textContent = '';
    } else {
        btn.classList.remove('off');
        btn.classList.add('on');
        btn.textContent = '输出到源目录：开';
        document.getElementById('output-hint').textContent = '输出将保存到各源文件所在目录';
    }
    document.getElementById('out-dir').disabled = !isOn;
    document.getElementById('btn-browse-out').disabled = !isOn;
}

// ---- Shared tree refresh ----

let _treeLessons = [];

async function refreshTree() {
    try {
        const tree = await apiGet('/api/files/tree');
        _treeLessons = tree.lessons || [];
        document.getElementById('task-count').textContent = String(tree.stat || 0);
        document.getElementById('task-breakdown').textContent = tree.extra_stat || '字幕 0 / 视频 0 / 往期笔记 0';
        document.getElementById('list-count').textContent = tree.stat ? `(${tree.stat} 个)` : '';

        const tbody = document.getElementById('file-tree-body');
        if (!tree.lessons || tree.lessons.length === 0) {
            tbody.innerHTML = '<tr class="tree-empty"><td colspan="5">暂无任务，请扫描或选择文件</td></tr>';
            return;
        }

        tbody.innerHTML = tree.lessons.map((l, i) => {
            const name = l.transcript_path.split(/[/\\]/).pop();
            const dirName = l.transcript_path.split(/[/\\]/).slice(-2, -1)[0] || '-';
            const videoName = l.video_path ? l.video_path.split(/[/\\]/).pop() : '---';
            const mode = l.video_path ? '图文混排' : '纯字幕';
            const status = l.status || '待处理';
            let tagClass = '';
            if (status === '✓ 完成') tagClass = 'done';
            else if (status === '✗ 失败') tagClass = 'fail';
            else if (status === '解析中…' || status === '生成中…') tagClass = 'doing';
            return `<tr class="${tagClass}" data-path="${l.transcript_path}" data-idx="${i}" onclick="toggleTreeSelect(this)">
                <td class="col-lesson">${escapeHtml(name)}</td>
                <td class="col-folder">${escapeHtml(dirName)}</td>
                <td class="col-video">${escapeHtml(videoName)}</td>
                <td class="col-mode">${mode}</td>
                <td class="col-status">${status}</td>
            </tr>`;
        }).join('');
    } catch (e) {
        console.error('refreshTree:', e);
    }
}

function toggleTreeSelect(row) {
    row.classList.toggle('selected');
}

function getSelectedTranscripts() {
    const rows = document.querySelectorAll('#file-tree-body tr.selected');
    return Array.from(rows).map(r => r.getAttribute('data-path')).filter(Boolean);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ---- Scan / Pick Files (native dialogs) ----

async function browseDirectory(inputId) {
    const input = document.getElementById(inputId);
    const currentVal = input.value.trim();
    try {
        const result = await apiPost('/api/pick/folder?initial_dir=' + encodeURIComponent(currentVal || ''), {});
        if (result.path) {
            input.value = result.path;
            input.dispatchEvent(new Event('change'));
        }
    } catch (e) {
        showToast('打开目录选择器失败: ' + e.message, 'error');
    }
}

async function scanDirectory() {
    const dir = document.getElementById('dir-path').value.trim();
    if (!dir) {
        showToast('请先选择工作目录', 'error');
        return;
    }
    try {
        const result = await apiPost('/api/files/scan', { directory: dir });
        refreshTree();
        appendLog('» 扫描完成  ' + dir + '\n', 'dim');
        appendLog('» 发现 ' + (result.transcript_count || 0) + ' 个字幕/文本文件\n', 'dim');
        appendLog('» 发现 ' + (result.video_count || 0) + ' 个视频文件\n', 'dim');
    } catch (e) {
        showToast('扫描失败: ' + e.message, 'error');
    }
}

async function pickFiles(type) {
    try {
        const result = await apiPost('/api/pick/files?file_type=' + encodeURIComponent(type), {});
        if (!result.paths || result.paths.length === 0) return;
        if (type === 'transcripts') {
            await apiPost('/api/files/transcripts', { paths: result.paths });
        } else if (type === 'videos') {
            await apiPost('/api/files/videos', { paths: result.paths });
        } else if (type === 'notes') {
            await apiPost('/api/files/notes', { paths: result.paths });
        }
        refreshTree();
    } catch (e) {
        showToast('添加失败: ' + e.message, 'error');
    }
}

async function removeSelected() {
    const paths = getSelectedTranscripts();
    if (paths.length === 0) {
        showToast('请先在任务列表中选择要移除的字幕', 'error');
        return;
    }
    try {
        await apiDelete('/api/files/transcripts', { paths });
        refreshTree();
    } catch (e) {
        showToast('移除失败: ' + e.message, 'error');
    }
}

// ---- Console Output ----

function appendLog(text, tag) {
    const consoleEl = document.getElementById('console-output');
    const placeholder = document.getElementById('console-placeholder');
    if (placeholder) placeholder.style.display = 'none';

    const span = document.createElement('span');
    span.className = 'console-tag-' + (tag || 'normal');
    span.textContent = text;
    consoleEl.appendChild(span);
    autoScrollConsole();
}

function appendToken(delta) {
    const consoleEl = document.getElementById('console-output');
    const placeholder = document.getElementById('console-placeholder');
    if (placeholder) placeholder.style.display = 'none';

    // Find or create the current token span
    let last = consoleEl.lastElementChild;
    if (!last || !last.classList.contains('token-stream')) {
        last = document.createElement('span');
        last.className = 'token-stream console-tag-normal';
        consoleEl.appendChild(last);
    }
    last.textContent += delta;
    autoScrollConsole();
}

let _outAutoScroll = true;

function autoScrollConsole() {
    if (!_outAutoScroll) return;
    const consoleEl = document.getElementById('console-output');
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

document.addEventListener('DOMContentLoaded', () => {
    const consoleEl = document.getElementById('console-output');
    if (consoleEl) {
        consoleEl.addEventListener('scroll', () => {
            const frac = consoleEl.scrollTop + consoleEl.clientHeight;
            _outAutoScroll = frac >= consoleEl.scrollHeight - 10;
        });
    }
});

function clearOutput() {
    const consoleEl = document.getElementById('console-output');
    consoleEl.innerHTML = '<span class="console-placeholder" id="console-placeholder">等待任务开始...这里会显示模型实时输出...</span>';
}

// ---- Run Controls ----

let _sseClient = null;

async function startRun() {
    if (_sseClient) return;

    const btnStart = document.getElementById('btn-start');
    const btnCancel = document.getElementById('btn-cancel');
    btnStart.disabled = true;
    btnStart.classList.add('hidden');
    btnCancel.classList.remove('hidden');

    // Build request
    const body = {
        course_name: document.getElementById('course-name').value,
        requirements_text: document.getElementById('requirements').value,
        output_dir: document.getElementById('out-dir').value,
        save_to_source: document.getElementById('btn-save-to-src').classList.contains('on'),
    };

    try {
        // Initiate run
        const result = await apiPost('/api/run/start', body);
        const runId = result.run_id;

        // Open SSE stream
        _sseClient = new EventSource('/api/stream/output?run_id=' + runId);

        _sseClient.addEventListener('progress', (e) => {
            const d = JSON.parse(e.data);
            document.getElementById('progress-bar').style.width = d.percentage + '%';
            document.getElementById('progress-pct').textContent = d.percentage + '%';
            document.getElementById('progress-label').textContent = '[' + d.current + '/' + d.total + ']  ' + (d.filename || '');
            document.getElementById('chip-current-file').textContent = d.filename || '';
            document.getElementById('status-text').textContent = '处理 ' + d.current + '/' + d.total + ' · ' + (d.mode || '');
        });

        _sseClient.addEventListener('token', (e) => {
            const d = JSON.parse(e.data);
            appendToken(d.delta);
            if (d.total_chars) {
                document.getElementById('chip-chars').textContent = d.total_chars.toLocaleString() + ' chars';
            }
        });

        _sseClient.addEventListener('status', (e) => {
            const d = JSON.parse(e.data);
            document.getElementById('status-text').textContent = d.message || '';
        });

        _sseClient.addEventListener('log', (e) => {
            const d = JSON.parse(e.data);
            appendLog(d.text, d.tag);
        });

        _sseClient.addEventListener('tree_update', (e) => {
            const d = JSON.parse(e.data);
            updateTreeRow(d.path, d.status, d.tag, d.mode);
        });

        _sseClient.addEventListener('complete', (e) => {
            const d = JSON.parse(e.data);
            appendLog('\n' + '═'.repeat(60) + '\n  全部完成  成功 ' + d.success_count + ' 个  失败 ' + d.fail_count + ' 个\n  输出位置：' + d.output_summary + '\n', 'dim');
            document.getElementById('status-text').textContent = '完成 — 成功 ' + d.success_count + ' 个 / 失败 ' + d.fail_count + ' 个';
            document.getElementById('progress-label').textContent = '全部完成：成功 ' + d.success_count + ' 个，失败 ' + d.fail_count + ' 个';
            document.getElementById('chip-current-file').textContent = '';
            document.getElementById('chip-pulse').classList.remove('pulse-running');
            document.getElementById('chip-pulse').classList.add('pulse-idle');
            document.getElementById('chip-pulse').textContent = 'idle';
            cleanupRun();
            refreshTree();
            refreshNavStatus();
        });

        _sseClient.addEventListener('error', (e) => {
            let data = {};
            try { data = JSON.parse(e.data); } catch (_) {}
            appendLog('\n» 错误：' + (data.message || '未知错误') + '\n', 'error');
            if (data.fatal) {
                cleanupRun();
            }
        });

        _sseClient.onerror = () => {
            // SSE connection lost — the complete event may have already fired
            if (_sseClient && _sseClient.readyState === EventSource.CLOSED) {
                cleanupRun();
            }
        };

        document.getElementById('chip-pulse').classList.remove('pulse-idle');
        document.getElementById('chip-pulse').classList.add('pulse-running');
        document.getElementById('chip-pulse').textContent = '● running';
        switchToTab('tab-run');

    } catch (e) {
        showToast('启动失败: ' + e.message, 'error');
        cleanupRun();
    }
}

function updateTreeRow(path, status, tag, mode) {
    const row = document.querySelector('#file-tree-body tr[data-path="' + CSS.escape(path) + '"]');
    if (!row) return;
    const cells = row.querySelectorAll('td');
    if (cells.length >= 5) {
        if (status) cells[4].textContent = status;
        if (mode) cells[3].textContent = mode;
    }
    row.className = '';
    if (tag === 'done') row.classList.add('done');
    else if (tag === 'fail') row.classList.add('fail');
    else if (tag === 'doing') row.classList.add('doing');
}

function cleanupRun() {
    if (_sseClient) {
        _sseClient.close();
        _sseClient = null;
    }
    const btnStart = document.getElementById('btn-start');
    const btnCancel = document.getElementById('btn-cancel');
    btnStart.disabled = false;
    btnStart.classList.remove('hidden');
    btnCancel.classList.add('hidden');
    document.getElementById('chip-pulse').classList.remove('pulse-running');
    document.getElementById('chip-pulse').classList.add('pulse-idle');
    document.getElementById('chip-pulse').textContent = 'idle';
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('progress-pct').textContent = '0%';
}

function cancelRun() {
    if (!_sseClient) return;
    if (!confirm('确定要取消当前运行吗？')) return;
    apiPost('/api/run/cancel', {});
}
