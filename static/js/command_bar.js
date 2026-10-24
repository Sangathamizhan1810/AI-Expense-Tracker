/**
 * ExpenseAI — Command Palette HUD Controller
 * Provides global Ctrl+K / Cmd+K instant NLP expense logging.
 */
document.addEventListener('DOMContentLoaded', () => {
    const backdrop = document.getElementById('cmd-palette-backdrop');
    const input = document.getElementById('cmd-palette-input');
    const form = document.getElementById('cmd-palette-form');
    const previewStrip = document.getElementById('cmd-preview-strip');
    const triggerBtns = document.querySelectorAll('.js-open-cmd');

    if (!backdrop || !input) return;

    let debounceTimer = null;

    function openPalette() {
        backdrop.classList.add('open');
        input.value = '';
        renderEmptyPreview();
        setTimeout(() => input.focus(), 50);
    }

    function closePalette() {
        backdrop.classList.remove('open');
        input.blur();
    }

    function renderEmptyPreview() {
        previewStrip.innerHTML = '<span style="color: var(--text-muted); font-size: 11px;">Type naturally (e.g. "Swiggy 350 lunch" or "Metro 40 to office")</span>';
    }

    // Global Key Listener (Ctrl+K / Cmd+K / Slash)
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (backdrop.classList.contains('open')) {
                closePalette();
            } else {
                openPalette();
            }
        } else if (e.key === 'Escape' && backdrop.classList.contains('open')) {
            closePalette();
        }
    });

    triggerBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            openPalette();
        });
    });

    backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
            closePalette();
        }
    });

    // Debounced NLP Parse
    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();

        if (!query) {
            renderEmptyPreview();
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch('/expenses/ai-parse', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sentence: query })
                });

                if (!res.ok) return;
                const data = await res.json();

                if (data.success && data.parsed) {
                    const p = data.parsed;
                    let html = '';

                    if (p.amount !== null && p.amount > 0) {
                        html += `<span class="cmd-token-chip cmd-token-chip--amount">₹${parseFloat(p.amount).toFixed(2)}</span>`;
                    } else {
                        html += `<span class="cmd-token-chip" style="color: var(--warning);">Amount missing</span>`;
                    }

                    if (p.category_name) {
                        const confPct = Math.round(p.confidence * 100);
                        html += `<span class="cmd-token-chip">📁 ${escapeHtml(p.category_name)} <span style="color: var(--text-muted);">(${confPct}%)</span></span>`;
                    }

                    if (p.expense_date) {
                        html += `<span class="cmd-token-chip">📅 ${p.expense_date}</span>`;
                    }

                    if (p.description) {
                        html += `<span style="color: var(--text-muted); font-size: 11px; margin-left: 6px;">"${escapeHtml(p.description)}"</span>`;
                    }

                    previewStrip.innerHTML = html;
                }
            } catch (err) {
                console.error('NLP parse error:', err);
            }
        }, 180);
    });

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>"']/g, (m) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[m]));
    }
});
