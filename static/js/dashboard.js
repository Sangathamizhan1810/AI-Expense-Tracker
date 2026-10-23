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
        Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.92)';
        Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.12)';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.plugins.tooltip.titleFont = { size: 13, weight: 'bold' };
        Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
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
            new Chart(donutCtx, {
                type: 'doughnut',
                data: {
                    labels: category_distribution.labels,
                    datasets: [{
                        data: category_distribution.amounts,
                        backgroundColor: category_distribution.colors,
                        borderColor: '#0f172a',
                        borderWidth: 2,
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '68%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#cbd5e1',
                                padding: 14,
                                font: { size: 11, weight: '500' },
                                usePointStyle: true,
                                pointStyle: 'circle'
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
        const ctx2d = lineCtx.getContext('2d');
        const gradient = ctx2d.createLinearGradient(0, 0, 0, 260);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.45)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

        new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: spending_trends.months,
                datasets: [{
                    label: 'Monthly Spend',
                    data: spending_trends.amounts,
                    borderColor: '#6366f1',
                    borderWidth: 3,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#a855f7',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 1.5,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    pointHoverBackgroundColor: '#6366f1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 11 }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 11 },
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
            // Highlight exceeded budgets with alert red
            const actualColors = budget_vs_actual.actual_amounts.map((spend, i) => {
                const limit = budget_vs_actual.budget_amounts[i] || 0;
                if (limit > 0 && spend > limit) {
                    return 'rgba(239, 68, 68, 0.88)'; // Exceeded Red
                }
                if (limit > 0 && spend >= limit * 0.8) {
                    return 'rgba(245, 158, 11, 0.88)'; // Warning Amber
                }
                return 'rgba(16, 185, 129, 0.88)';     // Healthy Emerald
            });

            new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: budget_vs_actual.categories,
                    datasets: [
                        {
                            label: 'Budget Limit',
                            data: budget_vs_actual.budget_amounts,
                            backgroundColor: 'rgba(99, 102, 241, 0.75)',
                            borderColor: '#6366f1',
                            borderWidth: 1,
                            borderRadius: 6
                        },
                        {
                            label: 'Actual Spend',
                            data: budget_vs_actual.actual_amounts,
                            backgroundColor: actualColors,
                            borderColor: 'rgba(255, 255, 255, 0.2)',
                            borderWidth: 1,
                            borderRadius: 6
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
                                color: '#cbd5e1',
                                font: { size: 11, weight: '500' }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                font: { size: 11 },
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
                                color: '#cbd5e1',
                                font: { size: 11, weight: '500' },
                                usePointStyle: true,
                                pointStyle: 'circle'
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
