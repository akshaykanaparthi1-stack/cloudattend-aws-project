/**
 * CloudAttend — Main UI Script
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');

    if (mobileBtn && sidebar) {
        mobileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
                if (!sidebar.contains(e.target) && e.target !== mobileBtn) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }

    // 2. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach((alert) => {
        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 250);
            });
        }

        // Auto fade out
        setTimeout(() => {
            if (alert.parentElement) {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }
        }, 5500);
    });

    // 3. Confirm Delete Actions
    const deleteForms = document.querySelectorAll('.confirm-delete');
    deleteForms.forEach((form) => {
        form.addEventListener('submit', (e) => {
            const studentName = form.getAttribute('data-name') || 'this student';
            const confirmed = window.confirm(
                `Are you sure you want to delete ${studentName}? This will permanently remove their records and attendance history.`
            );
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});
