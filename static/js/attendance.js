/**
 * CloudAttend — Attendance Marking Interactive Controls
 */

document.addEventListener('DOMContentLoaded', () => {
    const markAllPresentBtn = document.getElementById('markAllPresentBtn');
    const markAllAbsentBtn = document.getElementById('markAllAbsentBtn');
    const markAllLateBtn = document.getElementById('markAllLateBtn');
    const attendanceForm = document.getElementById('attendanceForm');

    function bulkSetStatus(statusValue) {
        const radios = document.querySelectorAll(`input[type="radio"][value="${statusValue}"]`);
        radios.forEach((radio) => {
            radio.checked = true;
        });
        updateCounts();
    }

    if (markAllPresentBtn) {
        markAllPresentBtn.addEventListener('click', (e) => {
            e.preventDefault();
            bulkSetStatus('Present');
        });
    }

    if (markAllAbsentBtn) {
        markAllAbsentBtn.addEventListener('click', (e) => {
            e.preventDefault();
            bulkSetStatus('Absent');
        });
    }

    if (markAllLateBtn) {
        markAllLateBtn.addEventListener('click', (e) => {
            e.preventDefault();
            bulkSetStatus('Late');
        });
    }

    // Dynamic Live Counter
    function updateCounts() {
        const presentCount = document.querySelectorAll('input[type="radio"][value="Present"]:checked').length;
        const absentCount = document.querySelectorAll('input[type="radio"][value="Absent"]:checked').length;
        const lateCount = document.querySelectorAll('input[type="radio"][value="Late"]:checked').length;

        const pBadge = document.getElementById('selectedPresentCount');
        const aBadge = document.getElementById('selectedAbsentCount');
        const lBadge = document.getElementById('selectedLateCount');

        if (pBadge) pBadge.textContent = presentCount;
        if (aBadge) aBadge.textContent = absentCount;
        if (lBadge) lBadge.textContent = lateCount;
    }

    // Attach change listeners to all radios
    const allRadios = document.querySelectorAll('.attendance-picker input[type="radio"]');
    allRadios.forEach((r) => {
        r.addEventListener('change', updateCounts);
    });

    // Initial count
    updateCounts();
});
