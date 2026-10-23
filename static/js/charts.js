/**
 * CloudAttend — Zero-Dependency High-DPI HTML5 Canvas Chart Engine
 * Renders professional responsive charts without external CDNs
 */

function setupCanvas(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return { ctx, width: rect.width, height: rect.height };
}

/**
 * Render multi-bar trend chart for attendance history
 */
function renderAttendanceTrendChart(canvasId, trendData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !trendData || trendData.length === 0) return;

    const { ctx, width, height } = setupCanvas(canvas);
    ctx.clearRect(0, 0, width, height);

    const padding = { top: 30, right: 20, bottom: 40, left: 45 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Find max value
    let maxVal = 5;
    trendData.forEach(d => {
        const total = Math.max(d.present, d.absent, d.late);
        if (total > maxVal) maxVal = total;
    });
    maxVal = Math.ceil(maxVal * 1.15); // Add 15% headroom

    // Draw horizontal grid lines
    const gridLines = 4;
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    ctx.font = '11px Inter, sans-serif';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'right';

    for (let i = 0; i <= gridLines; i++) {
        const yVal = Math.round((maxVal / gridLines) * i);
        const y = padding.top + chartHeight - (i / gridLines) * chartHeight;

        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();

        ctx.fillText(yVal.toString(), padding.left - 8, y + 4);
    }

    // Colors
    const colors = {
        present: '#10b981',
        absent: '#ef4444',
        late: '#f59e0b'
    };

    // Draw grouped bars
    const groupWidth = chartWidth / trendData.length;
    const barWidth = Math.min(18, (groupWidth - 20) / 3);

    trendData.forEach((item, idx) => {
        const groupCenterX = padding.left + idx * groupWidth + groupWidth / 2;
        const startX = groupCenterX - (barWidth * 3) / 2;

        const metrics = [
            { val: item.present, color: colors.present, offset: 0 },
            { val: item.absent, color: colors.absent, offset: barWidth + 2 },
            { val: item.late, color: colors.late, offset: (barWidth + 2) * 2 }
        ];

        metrics.forEach(m => {
            const barH = (m.val / maxVal) * chartHeight;
            const barY = padding.top + chartHeight - barH;
            const barX = startX + m.offset;

            ctx.fillStyle = m.color;
            // Draw rounded top bar
            ctx.beginPath();
            ctx.roundRect(barX, barY, barWidth, Math.max(barH, 2), [3, 3, 0, 0]);
            ctx.fill();
        });

        // X-axis label (date formatted)
        ctx.textAlign = 'center';
        ctx.fillStyle = '#64748b';
        ctx.font = '10px Inter, sans-serif';
        const dateStr = item.attendance_date.substring(5); // e.g. "10-23"
        ctx.fillText(dateStr, groupCenterX, height - 12);
    });
}

/**
 * Render donut chart for status breakdown
 */
function renderDonutChart(canvasId, present, absent, late) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const total = present + absent + late;
    const { ctx, width, height } = setupCanvas(canvas);
    ctx.clearRect(0, 0, width, height);

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.38;
    const innerRadius = radius * 0.65;

    if (total === 0) {
        // Empty state ring
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.arc(centerX, centerY, innerRadius, 2 * Math.PI, 0, true);
        ctx.fillStyle = '#f1f5f9';
        ctx.fill();

        ctx.textAlign = 'center';
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px Inter, sans-serif';
        ctx.fillText('No Records', centerX, centerY + 4);
        return;
    }

    const segments = [
        { count: present, color: '#10b981', label: 'Present' },
        { count: absent, color: '#ef4444', label: 'Absent' },
        { count: late, color: '#f59e0b', label: 'Late' },
    ];

    let startAngle = -0.5 * Math.PI;

    segments.forEach(seg => {
        if (seg.count <= 0) return;
        const sliceAngle = (seg.count / total) * 2 * Math.PI;
        const endAngle = startAngle + sliceAngle;

        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, endAngle);
        ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
        ctx.closePath();
        ctx.fillStyle = seg.color;
        ctx.fill();

        startAngle = endAngle;
    });

    // Center percentage label
    const pct = Math.round((present / total) * 100);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 22px Inter, sans-serif';
    ctx.fillText(`${pct}%`, centerX, centerY + 2);

    ctx.fillStyle = '#64748b';
    ctx.font = '11px Inter, sans-serif';
    ctx.fillText('Attendance', centerX, centerY + 18);
}

// Window resize handler to re-draw canvases smoothly
window.addEventListener('resize', () => {
    if (window._cachedTrendData) {
        renderAttendanceTrendChart('trendChartCanvas', window._cachedTrendData);
    }
    if (window._cachedDonutData) {
        renderDonutChart(
            'donutChartCanvas',
            window._cachedDonutData.present,
            window._cachedDonutData.absent,
            window._cachedDonutData.late
        );
    }
});
