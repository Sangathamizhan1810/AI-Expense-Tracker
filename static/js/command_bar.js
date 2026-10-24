/**
 * ExpenseAI — Quick Expense Log Controller
 * Provides natural-language expense logging with offline ML categorization.
 */
document.addEventListener('DOMContentLoaded', () => {
    const backdrop = document.getElementById('cmd-palette-backdrop');
    const input = document.getElementById('cmd-palette-input');
    const form = document.getElementById('cmd-palette-form');
    const previewStrip = document.getElementById('cmd-preview-strip');
    const parseStatus = document.getElementById('cmd-parse-status');
    const clearBtn = document.getElementById('cmd-clear-btn');
    const triggerBtns = document.querySelectorAll('.js-open-cmd');
    const closeBtns = document.querySelectorAll('.js-close-cmd');
    const suggestChips = document.querySelectorAll('.js-suggest');

    if (!backdrop || !input) return;

    let debounceTimer = null;

    function openPalette() {
        backdrop.classList.add('open');
        input.value = '';
        if (clearBtn) clearBtn.style.display = 'none';
        renderEmptyPreview();
        setTimeout(() => input.focus(), 60);
    }

    function closePalette() {
        backdrop.classList.remove('open');
        input.blur();
    }

    function renderEmptyPreview() {
        if (parseStatus) {
            parseStatus.textContent = 'Awaiting input';
            parseStatus.className = 'cmd-status-badge';
        }
        if (previewStrip) {
            previewStrip.innerHTML = '<span class="cmd-preview-placeholder">Type an amount and note above to see live category detection.</span>';
        }
    }

    // Modal Escape key support (accessibility standard)
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && backdrop.classList.contains('open')) {
            closePalette();
        }
    });

    // Open triggers
    triggerBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            openPalette();
        });
    });

    // Close triggers
    closeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            closePalette();
        });
    });

    // Click outside modal backdrop to close
    backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
            closePalette();
        }
    });

    // Clear button
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            input.value = '';
            clearBtn.style.display = 'none';
            renderEmptyPreview();
            input.focus();
        });
    }

    // Quick suggestion prompt chips
    suggestChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const sampleText = chip.getAttribute('data-text');
            if (sampleText) {
                input.value = sampleText;
                if (clearBtn) clearBtn.style.display = 'block';
                input.dispatchEvent(new Event('input'));
                input.focus();
            }
        });
    });

    // Debounced NLP Parse
    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();

        if (clearBtn) {
            clearBtn.style.display = query.length > 0 ? 'block' : 'none';
        }

        if (!query) {
            renderEmptyPreview();
            return;
        }

        if (parseStatus) {
            parseStatus.textContent = 'Parsing...';
            parseStatus.className = 'cmd-status-badge cmd-status-badge--parsing';
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

                    const hasAmount = p.amount !== null && p.amount > 0;

                    if (hasAmount) {
                        html += `<span class="cmd-token-chip cmd-token-chip--amount">₹${parseFloat(p.amount).toFixed(2)}</span>`;
                    } else {
                        html += `<span class="cmd-token-chip cmd-token-chip--missing">Amount missing</span>`;
                    }

                    if (p.category_name) {
                        const confPct = Math.round(p.confidence * 100);
                        html += `<span class="cmd-token-chip cmd-token-chip--category">Category: ${escapeHtml(p.category_name)} <span class="cmd-token-meta">(${confPct}%)</span></span>`;
                    }

                    if (p.expense_date) {
                        html += `<span class="cmd-token-chip cmd-token-chip--date">Date: ${p.expense_date}</span>`;
                    }

                    if (p.description) {
                        html += `<span class="cmd-token-chip cmd-token-chip--desc">"${escapeHtml(p.description)}"</span>`;
                    }

                    previewStrip.innerHTML = html;

                    if (parseStatus) {
                        if (hasAmount) {
                            parseStatus.textContent = 'Ready to save';
                            parseStatus.className = 'cmd-status-badge cmd-status-badge--ready';
                        } else {
                            parseStatus.textContent = 'Specify amount';
                            parseStatus.className = 'cmd-status-badge cmd-status-badge--warning';
                        }
                    }
                }
            } catch (err) {
                console.error('NLP parse error:', err);
            }
        }, 160);
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
