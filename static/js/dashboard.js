/**
 * AI-Based Expense Tracker — Dashboard Controller
 * ================================================
 * Renders and manages Chart.js interactive charts (Donut, Line, Bar),
 * tooltips, month navigation, and empty-state fallbacks.
 */

document.addEventListener('DOMContentLoaded', function () {
    // ── Read Pre-injected JSON State ────────────────────
    const dataElement = document.getElementById('dashboard-data');
    if (!dataElement) return;

    let dashboardData;
    try {
        dashboardData = JSON.parse(dataElement.textContent);
    } catch (err) {
        console.error('Failed to parse dashboard data:', err);
        return;
    }

    const { kpis, category_distribution, spending_trends, budget_vs_actual } = dashboardData;

    // ── Global Chart.js Dark Theme Configuration ────────
    if (typeof Chart !== 'undefined') {
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', system-ui, -apple-system, sans-serif";
        Chart.defaults.plugins.tooltip.backgroundColor = '#141924';
        Chart.defaults.plugins.tooltip.borderColor = '#222b3d';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.cornerRadius = 4;
        Chart.defaults.plugins.tooltip.titleFont = { size: 12, weight: '600' };
        Chart.defaults.plugins.tooltip.bodyFont = { size: 12, family: "'Geist Mono', Consolas, monospace" };
    } else {
        console.warn('Chart.js library is not loaded.');
        return;
    }

    // ── Chart 1: Category Breakdown Donut (DASH-02) ─────
    const donutCtx = document.getElementById('categoryDonutChart');
    const donutEmptyNotice = document.getElementById('donut-empty-notice');

    if (donutCtx) {
        if (!category_distribution.amounts || category_distribution.amounts.length === 0) {
            donutCtx.style.display = 'none';
            if (donutEmptyNotice) donutEmptyNotice.style.display = 'block';
        } else {
            // Architectural subdued categorical palette
            const terminalPalette = [
                '#f1f5f9', '#94a3b8', '#64748b', '#475569', '#38bdf8', '#0ea5e9', '#334155', '#1e293b'
            ];
            const sliceColors = category_distribution.amounts.map((_, i) => terminalPalette[i % terminalPalette.length]);

            new Chart(donutCtx, {
                type: 'doughnut',
                data: {
                    labels: category_distribution.labels,
                    datasets: [{
                        data: category_distribution.amounts,
                        backgroundColor: sliceColors,
                        borderColor: '#0c0e12',
                        borderWidth: 2,
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '76%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#94a3b8',
                                padding: 12,
                                font: { size: 11, weight: '500' },
                                usePointStyle: true,
                                pointStyle: 'circle',
                                boxWidth: 6
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const value = context.parsed || 0;
                                    const total = category_distribution.total_spent || 1;
                                    const pct = ((value / total) * 100).toFixed(1);
                                    return ` ₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2 })} (${pct}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // ── Chart 2: 6-Month Spending Trend Line (DASH-03) ──
    const lineCtx = document.getElementById('trendLineChart');
    if (lineCtx) {
        new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: spending_trends.months,
                datasets: [{
                    label: 'Monthly Spend',
                    data: spending_trends.amounts,
                    borderColor: '#f1f5f9',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#ffffff',
                    pointHoverBorderColor: '#0c0e12',
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#64748b',
                            font: { size: 11 }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#222b3d',
                            drawTicks: false
                        },
                        ticks: {
                            color: '#64748b',
                            font: { size: 11, family: "'Geist Mono', monospace" },
                            callback: function (val) {
                                return '₹' + val.toLocaleString('en-IN');
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const val = context.parsed.y || 0;
                                return ` Spend: ₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // ── Chart 3: Budget vs. Actual Bar Chart (DASH-04) ──
    const barCtx = document.getElementById('budgetBarChart');
    const barEmptyNotice = document.getElementById('bar-empty-notice');

    if (barCtx) {
        if (!budget_vs_actual.has_data) {
            barCtx.style.display = 'none';
            if (barEmptyNotice) barEmptyNotice.style.display = 'block';
        } else {
            const actualColors = budget_vs_actual.actual_amounts.map((spend, i) => {
                const limit = budget_vs_actual.budget_amounts[i] || 0;
                if (limit > 0 && spend > limit) {
                    return '#ef4444'; // Exceeded Red
                }
                if (limit > 0 && spend >= limit * 0.8) {
                    return '#f59e0b'; // Warning Amber
                }
                return '#38bdf8';     // Normal Sky Accent
            });

            new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: budget_vs_actual.categories,
                    datasets: [
                        {
                            label: 'Budget Limit',
                            data: budget_vs_actual.budget_amounts,
                            backgroundColor: '#1a2233',
                            borderColor: '#25324a',
                            borderWidth: 1,
                            borderRadius: 2
                        },
                        {
                            label: 'Actual Spend',
                            data: budget_vs_actual.actual_amounts,
                            backgroundColor: actualColors,
                            borderWidth: 0,
                            borderRadius: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: '#94a3b8',
                                font: { size: 11 }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: '#222b3d',
                                drawTicks: false
                            },
                            ticks: {
                                color: '#64748b',
                                font: { size: 11, family: "'Geist Mono', monospace" },
                                callback: function (val) {
                                    return '₹' + val.toLocaleString('en-IN');
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            align: 'end',
                            labels: {
                                color: '#94a3b8',
                                font: { size: 11, weight: '500' },
                                usePointStyle: true,
                                pointStyle: 'circle',
                                boxWidth: 6
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const label = context.dataset.label || '';
                                    const val = context.parsed.y || 0;
                                    return ` ${label}: ₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // ── Month Picker & Navigation Controls ──────────────
    const monthInput = document.getElementById('dashboard-month-input');
    const monthForm = document.getElementById('month-select-form');
    const prevBtn = document.getElementById('prev-month-btn');
    const nextBtn = document.getElementById('next-month-btn');

    if (monthInput && monthForm) {
        monthInput.addEventListener('change', function () {
            monthForm.submit();
        });

        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                shiftMonth(-1);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                shiftMonth(1);
            });
        }
    }

    function shiftMonth(offset) {
        if (!monthInput || !monthInput.value) return;
        const parts = monthInput.value.split('-');
        if (parts.length !== 2) return;

        let year = parseInt(parts[0], 10);
        let month = parseInt(parts[1], 10) - 1; // 0-indexed in Date

        const date = new Date(year, month + offset, 1);
        const newYear = date.getFullYear();
        const newMonth = String(date.getMonth() + 1).padStart(2, '0');

        monthInput.value = `${newYear}-${newMonth}`;
        monthForm.submit();
    }
});
