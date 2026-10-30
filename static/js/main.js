/**
 * AI-Based Expense Tracker — Global JavaScript
 * Auto-dismiss flash messages, mobile nav toggle, and utilities.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ── Auto-dismiss flash messages after 5 seconds ────
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(function (flash) {
        setTimeout(function () {
            flash.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(30px)';
            setTimeout(function () { flash.remove(); }, 500);
        }, 5000);
    });

    // ── Mobile hamburger menu toggle ───────────────────
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function () {
            navToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        // Close menu when clicking a link
        navMenu.querySelectorAll('.nav-link').forEach(function (link) {
            link.addEventListener('click', function () {
                navToggle.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }

    // ── Dark / Light Theme Toggle Engine ───────────────
    function getPreferredTheme() {
        return localStorage.getItem('expenseai_theme') || 'dark';
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('expenseai_theme', theme);

        // Update aria-label and titles on all toggle buttons
        const isDark = theme === 'dark';
        const nextModeLabel = isDark ? 'Switch to light theme' : 'Switch to dark theme';
        document.querySelectorAll('.js-theme-toggle').forEach(function (btn) {
            btn.setAttribute('aria-label', nextModeLabel);
            btn.setAttribute('title', nextModeLabel);
        });

        // Dispatch global themechange event for reactive components (e.g. Chart.js)
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: theme } }));
    }

    // Attach listeners to all theme toggle buttons (.js-theme-toggle)
    const toggleBtns = document.querySelectorAll('.js-theme-toggle');
    toggleBtns.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(nextTheme);
        });
    });

    // Sync button aria-labels with initial active theme
    const initialTheme = document.documentElement.getAttribute('data-theme') || getPreferredTheme();
    applyTheme(initialTheme);

});
