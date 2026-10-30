/**
 * ExpenseAI — Quick Add Controller
 * Split-input (alphabet description + numerical amount),
 * explicit on-click Gemini AI categorization (zero keystroke API calls),
 * and 1-tap editable pills.
 */
document.addEventListener('DOMContentLoaded', () => {
    const backdrop = document.getElementById('cmd-palette-backdrop');
    const form = document.getElementById('cmd-palette-form');
    const descInput = document.getElementById('cmd-input-desc');
    const amtInput = document.getElementById('cmd-input-amt');
    const clearBtn = document.getElementById('cmd-clear-btn');
    const quickAddBtn = document.getElementById('cmd-quick-add-btn');
    const suggestions = document.getElementById('cmd-suggestions');
    const suggestChips = document.querySelectorAll('.js-suggest');

    const resultContainer = document.getElementById('cmd-result-container');
    const fallbackNotice = document.getElementById('cmd-fallback-notice');
    const resultAmount = document.getElementById('cmd-result-amount');
    const resultNote = document.getElementById('cmd-result-note');
    const categoryText = document.getElementById('cmd-category-text');
    const categorySelect = document.getElementById('cmd-category-select');
    const dateText = document.getElementById('cmd-date-text');
    const dateInput = document.getElementById('cmd-date-input');
    const confidencePill = document.getElementById('cmd-confidence-pill');

    const submitBtn = document.getElementById('cmd-submit-btn');
    const manualEntryBtn = document.getElementById('cmd-manual-entry-btn');

    const hiddenSentence = document.getElementById('cmd-hidden-sentence');
    const hiddenAmount = document.getElementById('cmd-hidden-amount');
    const hiddenCategory = document.getElementById('cmd-hidden-category-id');
    const hiddenNote = document.getElementById('cmd-hidden-note');
    const hiddenDate = document.getElementById('cmd-hidden-date');

    const triggerBtns = document.querySelectorAll('.js-open-cmd');
    const closeBtns = document.querySelectorAll('.js-close-cmd');

    if (!backdrop || !descInput || !amtInput) return;

    let isParsed = false;
    let isParsing = false;

    // Default to today's ISO date string
    const getTodayISO = () => new Date().toISOString().slice(0, 10);

    function formatDateLabel(isoDate) {
        if (!isoDate) return 'Today';
        const today = getTodayISO();
        if (isoDate === today) return 'Today';
        try {
            const [y, m, d] = isoDate.split('-');
            const dt = new Date(parseInt(y, 10), parseInt(m, 10) - 1, parseInt(d, 10));
            return dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        } catch (e) {
            return isoDate;
        }
    }

    function openPalette() {
        backdrop.classList.add('open');
        descInput.value = '';
        amtInput.value = '';
        if (clearBtn) clearBtn.style.display = 'none';
        if (quickAddBtn) quickAddBtn.style.display = 'none';
        if (suggestions) suggestions.style.display = 'flex';
        resetParsedResult();
        setTimeout(() => descInput.focus(), 60);
    }

    function closePalette() {
        backdrop.classList.remove('open');
        descInput.blur();
        amtInput.blur();
    }

    function resetParsedResult() {
        isParsed = false;
        isParsing = false;

        if (hiddenSentence) hiddenSentence.value = '';
        if (hiddenAmount) hiddenAmount.value = '';
        if (hiddenCategory) hiddenCategory.value = '';
        if (hiddenNote) hiddenNote.value = '';
        if (hiddenDate) hiddenDate.value = getTodayISO();

        if (resultContainer) resultContainer.style.display = 'none';
        if (fallbackNotice) fallbackNotice.style.display = 'none';
        if (confidencePill) confidencePill.style.display = 'none';

        resetQuickAddBtnState();

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Save expense';
        }

        if (manualEntryBtn) {
            manualEntryBtn.href = '/expenses/add';
        }
    }

    function resetQuickAddBtnState() {
        if (!quickAddBtn) return;
        quickAddBtn.disabled = false;
        quickAddBtn.innerHTML = `
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M12 2L14.4 8.6L21 11L14.4 13.4L12 20L9.6 13.4L3 11L9.6 8.6L12 2Z"/>
            </svg>
            <span>Quick add</span>
        `;
    }

    function updateManualEntryLink() {
        if (!manualEntryBtn) return;
        const note = hiddenNote ? hiddenNote.value : descInput.value.trim();
        const amt = hiddenAmount ? hiddenAmount.value : amtInput.value.trim();
        const cat = hiddenCategory ? hiddenCategory.value : '';
        manualEntryBtn.href = `/expenses/add?note=${encodeURIComponent(note)}&amount=${encodeURIComponent(amt)}&category_id=${encodeURIComponent(cat)}`;
    }

    /**
     * Inspect input state client-side. Zero API calls made here!
     */
    function onFieldsChanged() {
        const desc = descInput.value.trim();
        const amtRaw = amtInput.value.trim();
        const amtVal = parseFloat(amtRaw);
        const hasContent = desc.length > 0 || amtRaw.length > 0;
        const hasBoth = desc.length >= 2 && !isNaN(amtVal) && amtVal > 0;

        // Clear button visibility
        if (clearBtn) {
            clearBtn.style.display = hasContent ? 'block' : 'none';
        }

        // Example chips: only visible when both inputs are completely empty
        if (suggestions) {
            suggestions.style.display = hasContent ? 'none' : 'flex';
        }

        // If user modifies inputs after parsing, hide previous result & reset save button
        if (isParsed) {
            isParsed = false;
            if (resultContainer) resultContainer.style.display = 'none';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Save expense';
            }
        }

        // "Quick add" button is visible ONLY after filling both fields
        if (quickAddBtn) {
            if (hasBoth) {
                resetQuickAddBtnState();
                quickAddBtn.style.display = 'inline-flex';
            } else {
                quickAddBtn.style.display = 'none';
            }
        }

        updateManualEntryLink();
    }

    // Left Input: strictly alphabet & spaces only
    descInput.addEventListener('input', () => {
        const cleaned = descInput.value.replace(/[^a-zA-Z\s]/g, '');
        if (descInput.value !== cleaned) {
            descInput.value = cleaned;
        }
        onFieldsChanged();
    });

    // Right Input: strictly numerical digits and decimal point only
    amtInput.addEventListener('input', () => {
        let val = amtInput.value.replace(/[^0-9.]/g, '');
        const parts = val.split('.');
        if (parts.length > 2) {
            val = parts[0] + '.' + parts.slice(1).join('');
        }
        if (amtInput.value !== val) {
            amtInput.value = val;
        }
        onFieldsChanged();
    });

    /**
     * Triggered EXCLUSIVELY on clicking "Quick add" (or pressing Enter when both fields filled).
     * Makes exactly ONE API request to classify category.
     */
    async function triggerAiClassification() {
        const desc = descInput.value.trim();
        const amt = parseFloat(amtInput.value.trim());

        if (!desc || isNaN(amt) || amt <= 0 || isParsing) return;

        isParsing = true;
        if (quickAddBtn) {
            quickAddBtn.disabled = true;
            quickAddBtn.innerHTML = `<span>⏳</span> <span>AI Categorizing...</span>`;
        }

        const sentenceQuery = `${desc} ${amt}`;

        try {
            const res = await fetch('/expenses/ai-parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sentence: sentenceQuery, prefer_gemini: true })
            });

            if (!res.ok) throw new Error('Network error');
            const data = await res.json();

            if (data.success && data.parsed) {
                const p = data.parsed;
                const finalDate = p.expense_date || getTodayISO();
                const finalCategoryId = p.category_id || (categorySelect ? categorySelect.value : 8);

                isParsed = true;

                // Sync hidden inputs
                if (hiddenSentence) hiddenSentence.value = sentenceQuery;
                if (hiddenAmount) hiddenAmount.value = amt;
                if (hiddenCategory) hiddenCategory.value = finalCategoryId;
                if (hiddenNote) hiddenNote.value = desc;
                if (hiddenDate) hiddenDate.value = finalDate;

                updateManualEntryLink();

                // 1. Amount
                if (resultAmount) {
                    resultAmount.textContent = `₹${amt.toFixed(2)}`;
                }

                // 2. Note / description
                if (resultNote) {
                    resultNote.textContent = desc;
                }

                // 3. Category Pill
                if (categorySelect) {
                    categorySelect.value = String(finalCategoryId);
                    const opt = categorySelect.options[categorySelect.selectedIndex];
                    if (categoryText) {
                        categoryText.textContent = opt ? opt.text : (p.category_name || 'Other');
                    }
                } else if (categoryText) {
                    categoryText.textContent = p.category_name || 'Other';
                }

                // 4. Date Pill
                if (dateInput) {
                    dateInput.value = finalDate;
                }
                if (dateText) {
                    dateText.textContent = formatDateLabel(finalDate);
                }

                // 5. Fallback Notice (Only if Gemini limit reached)
                if (fallbackNotice) {
                    fallbackNotice.style.display = p.quota_exceeded ? 'block' : 'none';
                }

                // 6. Low Confidence Indicator (Only when low)
                if (confidencePill) {
                    const isLow = p.is_low_confidence || (p.confidence !== null && p.confidence < 0.5);
                    if (isLow) {
                        const pct = Math.round((p.confidence || 0) * 100);
                        confidencePill.textContent = `Low confidence (${pct}%)`;
                        confidencePill.style.display = 'inline-flex';
                    } else {
                        confidencePill.style.display = 'none';
                    }
                }

                // 7. Show result container & hide quickAddBtn
                if (resultContainer) {
                    resultContainer.style.display = 'flex';
                }
                if (quickAddBtn) {
                    quickAddBtn.style.display = 'none';
                }

                // 8. Enable primary Save Expense button
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Save expense';
                }
            }
        } catch (err) {
            console.error('Quick add categorization error:', err);
            // Fallback gracefully without breaking
            isParsed = true;
            if (hiddenSentence) hiddenSentence.value = sentenceQuery;
            if (hiddenAmount) hiddenAmount.value = amt;
            if (hiddenNote) hiddenNote.value = desc;
            if (resultAmount) resultAmount.textContent = `₹${amt.toFixed(2)}`;
            if (resultNote) resultNote.textContent = desc;
            if (resultContainer) resultContainer.style.display = 'flex';
            if (quickAddBtn) quickAddBtn.style.display = 'none';
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save expense';
            }
        } finally {
            isParsing = false;
            resetQuickAddBtnState();
        }
    }

    // Attach click to Quick Add button
    if (quickAddBtn) {
        quickAddBtn.addEventListener('click', (e) => {
            e.preventDefault();
            triggerAiClassification();
        });
    }

    // Clear button
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            descInput.value = '';
            amtInput.value = '';
            clearBtn.style.display = 'none';
            if (quickAddBtn) quickAddBtn.style.display = 'none';
            if (suggestions) suggestions.style.display = 'flex';
            resetParsedResult();
            descInput.focus();
        });
    }

    // Example suggestion chips: pre-fill fields and show Quick Add button
    suggestChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const desc = chip.getAttribute('data-desc') || '';
            const amt = chip.getAttribute('data-amt') || '';
            descInput.value = desc;
            amtInput.value = amt;
            onFieldsChanged();
            descInput.focus();
        });
    });

    // Editable Category Pill (1-tap change)
    if (categorySelect) {
        categorySelect.addEventListener('change', () => {
            const selectedOpt = categorySelect.options[categorySelect.selectedIndex];
            if (categoryText && selectedOpt) {
                categoryText.textContent = selectedOpt.text;
            }
            if (hiddenCategory) {
                hiddenCategory.value = categorySelect.value;
            }
            updateManualEntryLink();
        });
    }

    // Editable Date Pill (1-tap change)
    if (dateInput) {
        dateInput.value = getTodayISO();
        dateInput.addEventListener('change', () => {
            const selectedDate = dateInput.value;
            if (dateText) {
                dateText.textContent = formatDateLabel(selectedDate);
            }
            if (hiddenDate) {
                hiddenDate.value = selectedDate;
            }
        });
    }

    // Enter key handling
    function handleEnter(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (isParsed && submitBtn && !submitBtn.disabled) {
                form.submit();
            } else {
                const desc = descInput.value.trim();
                const amt = parseFloat(amtInput.value.trim());
                if (desc.length >= 2 && !isNaN(amt) && amt > 0) {
                    triggerAiClassification();
                }
            }
        }
    }

    descInput.addEventListener('keydown', handleEnter);
    amtInput.addEventListener('keydown', handleEnter);

    // Escape key closes modal
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

    // Click backdrop to close
    backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
            closePalette();
        }
    });

    // Form submission
    if (form) {
        form.addEventListener('submit', async (e) => {
            if (!isParsed) {
                e.preventDefault();
                await triggerAiClassification();
                if (isParsed && submitBtn && !submitBtn.disabled) {
                    form.submit();
                }
            }
        });
    }
});
