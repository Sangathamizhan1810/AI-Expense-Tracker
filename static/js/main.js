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

});
