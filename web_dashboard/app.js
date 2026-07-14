/**
 * app.js — Executive Agile & SQDP Web Dashboard Core Engine
 * ==========================================================
 * 
 * Implements the SOLID Event-Driven Graphic Architecture in modern ES6+ JavaScript:
 * 1. `TimeSpanContext` & `TimePeriodRegistry`: Centralized pub/sub reactive broadcaster.
 * 2. `SqdpBoardWidget`: Multi-granularity 13-column (Fiscal Weeks) & 31-column (Daily) matrix.
 * 3. `SqdpAspectChartWidget`: Interactive S, Q, D, P aspect switcher with high-res Canvas charts.
 * 4. `ProgressBarChartWidget`: Vertical output gradient bars + two tracking lines.
 * 5. `BurndownChartWidget`: Agile burndown curves with warning protection on non-sprint granularities.
 * 6. Interactive Tables, Physiological Questionnaire, and JSON Contract Viewer.
 */

// ── 1. TimeSpanContext & TimePeriodRegistry (Services Layer) ──
class TimeSpanContext {
    constructor({ granularity, windowLabel, fiscalYear, teamScope }) {
        this.granularity = granularity;
        this.windowLabel = windowLabel;
        this.fiscalYear = fiscalYear;
        this.teamScope = teamScope;
        
        // Burndown is supported only under 'Fiscal Weeks'
        this.isSprintCapable = (granularity === "Fiscal Weeks");
        
        // Determine grid capacity & X-axis sub-intervals
        if (granularity === "Fiscal Weeks") {
            this.cols = 13;
            this.validSubIntervals = ["W1", "W3", "W5", "W7", "W9", "W11", "W13"];
        } else if (granularity === "Days") {
            this.cols = 31;
            this.validSubIntervals = ["Day 1", "Day 6", "Day 11", "Day 16", "Day 21", "Day 26", "Day 31"];
        } else {
            // Months
            this.cols = 12;
            this.validSubIntervals = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        }
    }

    static fromForm() {
        const granularity = document.getElementById("combo-granularity").value;
        const windowLabel = document.getElementById("combo-window").value;
        const fiscalYear = document.getElementById("combo-year").value;
        const teamScope = document.getElementById("combo-team").value;
        return new TimeSpanContext({ granularity, windowLabel, fiscalYear, teamScope });
    }
}

class TimePeriodRegistry {
    constructor() {
        this.subscribers = new Set();
        this.activeContext = null;
    }

    subscribe(widget) {
        this.subscribers.add(widget);
        if (this.activeContext && typeof widget.onTimePeriodChanged === "function") {
            widget.onTimePeriodChanged(this.activeContext);
        }
    }

    unsubscribe(widget) {
        this.subscribers.delete(widget);
    }

    broadcastPeriod(ctx) {
        this.activeContext = ctx;
        console.log(`[UI REACTIVE LOOP] Broadcasting -> Granularity: ${ctx.granularity} | Window: ${ctx.windowLabel} | Scope: ${ctx.teamScope}`);
        this.subscribers.forEach(widget => {
            if (typeof widget.onTimePeriodChanged === "function") {
                widget.onTimePeriodChanged(ctx);
            }
        });
    }
}

const timeRegistry = new TimePeriodRegistry();

// ── 2. Unified SQDP Board Widget (`SqdpBoardWidget`) ──
class SqdpBoardWidget {
    constructor(containerId, titleId) {
        this.container = document.getElementById(containerId);
        this.titleElement = document.getElementById(titleId);
        timeRegistry.subscribe(this);
    }

    onTimePeriodChanged(ctx) {
        if (this.titleElement) {
            this.titleElement.textContent = `SQDP Board — ${ctx.teamScope} (${ctx.windowLabel})`;
        }
        this.renderBoard(ctx);
    }

    renderBoard(ctx) {
        if (!this.container) return;
        this.container.innerHTML = "";

        const aspects = [
            { code: "S", label: "S — Safety", badgeClass: "badge-S" },
            { code: "Q", label: "Q — Quality", badgeClass: "badge-Q" },
            { code: "D", label: "D — Delivery", badgeClass: "badge-D" },
            { code: "P", label: "P — Productivity", badgeClass: "badge-P" }
        ];

        aspects.forEach((aspect, rowIdx) => {
            const rowDiv = document.createElement("div");
            rowDiv.className = "sqdp-row";

            const badge = document.createElement("div");
            badge.className = `sqdp-row-badge ${aspect.badgeClass}`;
            badge.innerHTML = `<span>${aspect.label}</span> <span>[${ctx.cols}]</span>`;
            rowDiv.appendChild(badge);

            const track = document.createElement("div");
            track.className = "sqdp-cells-track";
            track.style.gridTemplateColumns = `repeat(${ctx.cols}, 1fr)`;

            for (let i = 1; i <= ctx.cols; i++) {
                const cell = document.createElement("div");
                const statusInfo = this.getCellStatus(aspect.code, i, ctx.cols, rowIdx);
                cell.className = `sqdp-cell ${statusInfo.className}`;
                cell.textContent = i;
                cell.setAttribute("data-aspect", aspect.code);
                cell.setAttribute("data-idx", i);
                cell.setAttribute("data-status", statusInfo.label);
                cell.setAttribute("data-comment", statusInfo.comment);

                // Attach interactive tooltip and modal feedback
                cell.addEventListener("mouseenter", (e) => this.showTooltip(e, cell));
                cell.addEventListener("mouseleave", () => this.hideTooltip());
                cell.addEventListener("click", () => this.onCellClicked(aspect.code, i, statusInfo));

                track.appendChild(cell);
            }
            rowDiv.appendChild(track);
            this.container.appendChild(rowDiv);
        });
    }

    getCellStatus(code, idx, maxCols, rowIdx) {
        // Future / unreached cells in current sprint window
        if (idx > maxCols * 0.75) {
            return { className: "cell-grey", label: "Planned / Future", comment: "Cell capacity allocated; tracking pending sprint progression." };
        }
        // Specific mock incidents for rich realistic demonstration
        if ((code === "S" && idx === 4) || (code === "Q" && idx === 7) || (code === "D" && idx === 3)) {
            return { className: "cell-red", label: "Missed / Incident", comment: `${code === "S" ? "Minor First Aid cut at Cell 4 bench." : code === "Q" ? "Scrap rate exceeded 3% threshold due to feed calibration." : "Logistics delay: raw material shortage on Line 2."}` };
        }
        if ((code === "Q" && idx === 2) || (code === "P" && idx === 5) || (code === "D" && idx === 8)) {
            return { className: "cell-yellow", label: "Warning / Near Miss", comment: `${code === "Q" ? "Tooling wear detected during dimensional check." : code === "P" ? "OEE at 88% (Target 90%). Operator changeover delay." : "Carrier truck 45 mins late; order dispatched within grace window."}` };
        }
        return { className: "cell-green", label: "Target Met", comment: "All operational, quality, and physiological safety benchmarks achieved 100%." };
    }

    showTooltip(event, cell) {
        const portal = document.getElementById("tooltip-portal");
        if (!portal) return;
        const aspect = cell.getAttribute("data-aspect");
        const idx = cell.getAttribute("data-idx");
        const status = cell.getAttribute("data-status");
        const comment = cell.getAttribute("data-comment");

        portal.innerHTML = `
            <h5>${aspect} — Unit/Period ${idx}</h5>
            <p><strong>Status:</strong> ${status}</p>
            <p style="margin-top: 4px; font-size: 0.82rem; color: #CCCCCC;">${comment}</p>
        `;
        portal.classList.remove("hidden");

        const rect = cell.getBoundingClientRect();
        portal.style.left = `${Math.min(window.innerWidth - 330, rect.left + window.scrollX)}px`;
        portal.style.top = `${rect.bottom + window.scrollY + 8}px`;
    }

    hideTooltip() {
        const portal = document.getElementById("tooltip-portal");
        if (portal) portal.classList.add("hidden");
    }

    onCellClicked(code, idx, statusInfo) {
        alert(`⚡ SQDP Cell Inspection\n\nAspect: [${code}] | Period: #${idx}\nStatus: ${statusInfo.label}\n\nAudit Note: ${statusInfo.comment}`);
    }
}

// ── 3. SQDP Aspect Interactive Chart (`SqdpAspectChartWidget`) ──
class SqdpAspectChartWidget {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas ? this.canvas.getContext("2d") : null;
        this.activeAspect = "P";
        this.initButtons();
        this.render();
    }

    initButtons() {
        const btns = document.querySelectorAll(".btn-aspect");
        btns.forEach(btn => {
            btn.addEventListener("click", () => {
                btns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this.activeAspect = btn.getAttribute("data-aspect");
                this.render();
            });
        });
    }

    render() {
        if (!this.canvas || !this.ctx) return;
        const c = this.canvas;
        const ctx = this.ctx;
        ctx.clearRect(0, 0, c.width, c.height);

        const isDark = document.documentElement.getAttribute("data-theme") !== "light";
        const gridColor = isDark ? "#2A303C" : "#E2E8F0";
        const textColor = isDark ? "#8B949E" : "#475569";

        // Chart configuration based on active aspect
        let categories = ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12"];
        let values = [];
        let barColor = "#00E676";
        let target = 0.90;
        let yTitle = "Score / Efficiency Ratio";

        if (this.activeAspect === "S") {
            categories = ["Motivation", "Connected", "Workload", "Teamwork", "Ergonomics", "PPE Compliance"];
            values = [0.94, 0.96, 0.89, 0.98, 0.91, 0.99];
            barColor = "#00E676";
            target = 0.90;
            yTitle = "Physiological Compliance Ratio";
        } else if (this.activeAspect === "Q") {
            values = [0.95, 0.98, 0.92, 0.88, 0.94, 0.97, 0.91, 0.89, 0.96, 0.99, 0.93, 0.90];
            barColor = "#FFAB00";
            target = 0.93;
            yTitle = "First-Time Yield & Scrap Ratio";
        } else if (this.activeAspect === "D") {
            values = [0.85, 0.92, 0.96, 0.91, 0.87, 0.94, 0.89, 0.93, 0.95, 0.88, 0.97, 0.92];
            barColor = "#448AFF";
            target = 0.90;
            yTitle = "On-Time Order Fulfillment Ratio";
        } else {
            // P
            values = [0.92, 0.88, 0.95, 0.84, 0.91, 0.96, 0.93, 0.89, 0.94, 0.97, 0.90, 0.95];
            barColor = "#00E676";
            target = 0.90;
            yTitle = "OEE & Productivity Output Ratio";
        }

        // Draw Y Gridlines & Labels
        const topM = 30, bottomM = 50, leftM = 60, rightM = 30;
        const chartW = c.width - leftM - rightM;
        const chartH = c.height - topM - bottomM;

        ctx.font = "12px Inter, sans-serif";
        ctx.fillStyle = textColor;
        ctx.textAlign = "right";

        for (let i = 0; i <= 5; i++) {
            const val = (i * 0.2).toFixed(1);
            const y = topM + chartH - (i / 5) * chartH;
            ctx.fillText(val, leftM - 12, y + 4);

            ctx.beginPath();
            ctx.strokeStyle = gridColor;
            ctx.lineWidth = 1;
            ctx.moveTo(leftM, y);
            ctx.lineTo(leftM + chartW, y);
            ctx.stroke();
        }

        // Draw Target Threshold Line
        const targetY = topM + chartH - target * chartH;
        ctx.beginPath();
        ctx.setLineDash([6, 4]);
        ctx.strokeStyle = "#FF5252";
        ctx.lineWidth = 2;
        ctx.moveTo(leftM, targetY);
        ctx.lineTo(leftM + chartW, targetY);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = "#FF5252";
        ctx.textAlign = "left";
        ctx.font = "bold 11px Inter, sans-serif";
        ctx.fillText(`Target Threshold (${(target * 100).toFixed(0)}%)`, leftM + 8, targetY - 6);

        // Draw Bars & X Labels
        const n = categories.length;
        const slotW = chartW / n;
        const barW = Math.min(slotW * 0.55, 60);

        ctx.textAlign = "center";
        categories.forEach((cat, i) => {
            const val = values[i];
            const bh = val * chartH;
            const bx = leftM + i * slotW + (slotW - barW) / 2;
            const by = topM + chartH - bh;

            // Gradient bar
            const grad = ctx.createLinearGradient(0, by, 0, by + bh);
            grad.addColorStop(0, barColor);
            grad.addColorStop(1, isDark ? "#161B22" : "#E2E8F0");
            ctx.fillStyle = grad;
            ctx.fillRect(bx, by, barW, bh);

            // Value label above bar
            ctx.fillStyle = isDark ? "#F0F6FC" : "#0F172A";
            ctx.font = "bold 11px Inter, sans-serif";
            ctx.fillText(`${(val * 100).toFixed(0)}%`, bx + barW / 2, by - 6);

            // X Category Label
            ctx.fillStyle = textColor;
            ctx.font = "12px Inter, sans-serif";
            ctx.fillText(cat, bx + barW / 2, topM + chartH + 24);
        });
    }
}

// ── 4. Efficiency & Progress Combo Chart (`ProgressBarChartWidget`) ──
class ProgressBarChartWidget {
    constructor(canvasId, titleId) {
        this.canvas = document.getElementById(canvasId);
        this.titleElement = document.getElementById(titleId);
        this.ctx = this.canvas ? this.canvas.getContext("2d") : null;
        timeRegistry.subscribe(this);
    }

    onTimePeriodChanged(ctx) {
        if (this.titleElement) {
            this.titleElement.textContent = `Efficiency & Progress Ratio — ${ctx.teamScope} (${ctx.fiscalYear} • ${ctx.windowLabel})`;
        }
        this.render();
    }

    render() {
        if (!this.canvas || !this.ctx) return;
        const c = this.canvas;
        const ctx = this.ctx;
        ctx.clearRect(0, 0, c.width, c.height);

        const isDark = document.documentElement.getAttribute("data-theme") !== "light";
        const gridColor = isDark ? "#2A303C" : "#E2E8F0";
        const textColor = isDark ? "#8B949E" : "#475569";

        const categories = ["Cell A (Machining)", "Cell B (Stamping)", "Cell C (Assembly)", "Cell D (Coating)", "Cell E (Inspection)", "Cell F (Packaging)"];
        const barValues = [0.92, 0.88, 0.95, 0.84, 0.91, 0.96];
        const lineCompleted = [0.90, 0.85, 0.94, 0.82, 0.89, 0.95];
        const lineTotal = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0];

        const topM = 30, bottomM = 45, leftM = 60, rightM = 30;
        const chartW = c.width - leftM - rightM;
        const chartH = c.height - topM - bottomM;

        ctx.font = "12px Inter, sans-serif";
        ctx.fillStyle = textColor;
        ctx.textAlign = "right";

        for (let i = 0; i <= 5; i++) {
            const val = `${(i * 20)}%`;
            const y = topM + chartH - (i / 5) * chartH;
            ctx.fillText(val, leftM - 12, y + 4);

            ctx.beginPath();
            ctx.strokeStyle = gridColor;
            ctx.lineWidth = 1;
            ctx.moveTo(leftM, y);
            ctx.lineTo(leftM + chartW, y);
            ctx.stroke();
        }

        const n = categories.length;
        const slotW = chartW / n;
        const barW = slotW * 0.45;

        ctx.textAlign = "center";
        categories.forEach((cat, i) => {
            const val = barValues[i];
            const bh = val * chartH;
            const bx = leftM + i * slotW + (slotW - barW) / 2;
            const by = topM + chartH - bh;

            const grad = ctx.createLinearGradient(0, by, 0, by + bh);
            grad.addColorStop(0, "#58A6FF");
            grad.addColorStop(1, "#1D3557");
            ctx.fillStyle = grad;
            ctx.fillRect(bx, by, barW, bh);

            ctx.fillStyle = textColor;
            ctx.font = "11px Inter, sans-serif";
            ctx.fillText(cat.split(" ")[0] + " " + cat.split(" ")[1], bx + barW / 2, topM + chartH + 22);
        });

        // Helper coordinate converter
        const getPt = (i, val) => ({
            x: leftM + i * slotW + slotW / 2,
            y: topM + chartH - val * chartH
        });

        // Total capacity line (dashed blue)
        ctx.beginPath();
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = "#58A6FF";
        ctx.lineWidth = 2.5;
        for (let i = 0; i < n; i++) {
            const pt = getPt(i, lineTotal[i]);
            if (i === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // Completed line (solid near-black/white + markers)
        const lineColor = isDark ? "#F0F6FC" : "#0F172A";
        ctx.beginPath();
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 3;
        for (let i = 0; i < n; i++) {
            const pt = getPt(i, lineCompleted[i]);
            if (i === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        }
        ctx.stroke();

        // Markers
        for (let i = 0; i < n; i++) {
            const pt = getPt(i, lineCompleted[i]);
            ctx.beginPath();
            ctx.fillStyle = lineColor;
            ctx.arc(pt.x, pt.y, 4.5, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

// ── 5. Burndown Curve Chart with Warning Protection (`BurndownChartWidget`) ──
class BurndownChartWidget {
    constructor(canvasId, titleId) {
        this.canvas = document.getElementById(canvasId);
        this.titleElement = document.getElementById(titleId);
        this.legendElement = document.getElementById("burndown-legend");
        this.ctx = this.canvas ? this.canvas.getContext("2d") : null;
        timeRegistry.subscribe(this);
    }

    onTimePeriodChanged(ctx) {
        if (this.titleElement) {
            this.titleElement.textContent = `Burndown Curve (${ctx.windowLabel}) — ${ctx.teamScope}`;
        }
        if (this.legendElement) {
            this.legendElement.style.display = ctx.isSprintCapable ? "flex" : "none";
        }
        this.render(ctx);
    }

    render(ctxTime) {
        if (!this.canvas || !this.ctx) return;
        const c = this.canvas;
        const ctx = this.ctx;
        ctx.clearRect(0, 0, c.width, c.height);

        const isDark = document.documentElement.getAttribute("data-theme") !== "light";
        const gridColor = isDark ? "#2A303C" : "#E2E8F0";
        const textColor = isDark ? "#8B949E" : "#475569";

        // ── Check if granularity supports Sprint Burndown (`Fiscal Weeks`) ──
        if (!ctxTime.isSprintCapable) {
            // Render styled safety warning exact to walkthrough specs!
            ctx.textAlign = "center";
            ctx.font = "bold 20px Outfit, sans-serif";
            ctx.fillStyle = "#FF5252";
            ctx.fillText("Sprint Burndown Unavailable", c.width / 2, c.height / 2 - 25);

            ctx.font = "14px Inter, sans-serif";
            ctx.fillStyle = textColor;
            ctx.fillText("Sprint Burndown tracking is supported only under 'Fiscal Weeks' (FW) granularity.", c.width / 2, c.height / 2 + 10);
            
            ctx.font = "italic 13px Inter, sans-serif";
            ctx.fillStyle = isDark ? "#6E7681" : "#64748B";
            ctx.fillText(`Currently selected: '${ctxTime.granularity}'. Please switch to Fiscal Weeks in the top header filter bar above.`, c.width / 2, c.height / 2 + 38);
            return;
        }

        // Render full Sprint Burndown curves
        const categories = ctxTime.validSubIntervals;
        const n = categories.length;
        const yMax = 550.0;

        const topM = 30, bottomM = 45, leftM = 60, rightM = 60;
        const chartW = c.width - leftM - rightM;
        const chartH = c.height - topM - bottomM;

        // Gridlines
        ctx.font = "12px Inter, sans-serif";
        ctx.fillStyle = textColor;
        ctx.textAlign = "right";

        for (let i = 0; i <= 5; i++) {
            const val = Math.round((i / 5) * yMax);
            const y = topM + chartH - (i / 5) * chartH;
            ctx.fillText(`${val} pts`, leftM - 12, y + 4);

            ctx.beginPath();
            ctx.strokeStyle = gridColor;
            ctx.lineWidth = 1;
            ctx.moveTo(leftM, y);
            ctx.lineTo(leftM + chartW, y);
            ctx.stroke();
        }

        // X labels and vertical ticks
        ctx.textAlign = "center";
        categories.forEach((cat, i) => {
            const x = leftM + (i / (n - 1)) * chartW;
            ctx.fillStyle = textColor;
            ctx.fillText(cat, x, topM + chartH + 24);

            if (i > 0 && i < n - 1) {
                ctx.beginPath();
                ctx.setLineDash([2, 4]);
                ctx.strokeStyle = gridColor;
                ctx.moveTo(x, topM);
                ctx.lineTo(x, topM + chartH);
                ctx.stroke();
                ctx.setLineDash([]);
            }
        });

        const getPt = (xNorm, val) => ({
            x: leftM + xNorm * chartW,
            y: topM + chartH - (val / yMax) * chartH
        });

        // 1. Master Baseline (dashed grey)
        ctx.beginPath();
        ctx.setLineDash([6, 4]);
        ctx.strokeStyle = "#8D99AE";
        ctx.lineWidth = 2.5;
        for (let i = 0; i < n; i++) {
            const pt = getPt(i / (n - 1), 500 * (1 - i / (n - 1)));
            if (i === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // 2. Catch-up Target (solid navy)
        const liveLen = Math.ceil(n / 2);
        const lastLiveVal = 240.0;
        ctx.beginPath();
        ctx.strokeStyle = "#58A6FF";
        ctx.lineWidth = 2.5;
        for (let i = liveLen - 1; i < n; i++) {
            const xNorm = i / (n - 1);
            const val = lastLiveVal * (1 - (i - (liveLen - 1)) / (n - liveLen));
            const pt = getPt(xNorm, val);
            if (i === liveLen - 1) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        }
        ctx.stroke();

        // 3. Slip Forecast (+Delta orange dashed)
        ctx.beginPath();
        ctx.setLineDash([5, 4]);
        ctx.strokeStyle = "#F4A261";
        ctx.lineWidth = 2.5;
        let slipEndPt = null;
        for (let i = liveLen - 1; i < n; i++) {
            const xNorm = i / (n - 1);
            const val = lastLiveVal - (lastLiveVal - 40.0) * ((i - (liveLen - 1)) / (n - liveLen));
            const pt = getPt(xNorm, val);
            if (i === liveLen - 1) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
            slipEndPt = pt;
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // Callout Badge for +40.0 pts late
        if (slipEndPt) {
            const badgeW = 96, badgeH = 22;
            ctx.fillStyle = "#F4A261";
            ctx.beginPath();
            ctx.roundRect(slipEndPt.x - badgeW - 10, slipEndPt.y - badgeH - 6, badgeW, badgeH, 5);
            ctx.fill();

            ctx.fillStyle = "#000000";
            ctx.font = "bold 11px Inter, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("+40.0 pts late", slipEndPt.x - badgeW / 2 - 10, slipEndPt.y - badgeH / 2 + 1);
        }

        // 4. Live Sprint Actuals (solid red + bold dots)
        const liveY = [500.0, 420.0, 310.0, 240.0];
        ctx.beginPath();
        ctx.strokeStyle = "#FF5252";
        ctx.lineWidth = 3.5;
        for (let i = 0; i < liveLen; i++) {
            const pt = getPt(i / (n - 1), liveY[i]);
            if (i === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
        }
        ctx.stroke();

        for (let i = 0; i < liveLen; i++) {
            const pt = getPt(i / (n - 1), liveY[i]);
            ctx.beginPath();
            ctx.fillStyle = "#FF5252";
            ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

// ── 6. Safety Summary Bar Chart (Safety Tab) ──
function renderSafetyBarChart() {
    const c = document.getElementById("safety-bar-canvas");
    if (!c) return;
    const ctx = c.getContext("2d");
    ctx.clearRect(0, 0, c.width, c.height);

    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    const gridColor = isDark ? "#2A303C" : "#E2E8F0";
    const textColor = isDark ? "#8B949E" : "#475569";

    const factors = ["Motivation", "Connectedness", "Workload Balance", "Teamwork"];
    const values = [0.94, 0.96, 0.89, 0.98];
    const topM = 30, bottomM = 45, leftM = 60, rightM = 30;
    const chartW = c.width - leftM - rightM;
    const chartH = c.height - topM - bottomM;

    ctx.font = "12px Inter, sans-serif";
    ctx.fillStyle = textColor;
    ctx.textAlign = "right";

    for (let i = 0; i <= 5; i++) {
        const val = `${(i * 20)}%`;
        const y = topM + chartH - (i / 5) * chartH;
        ctx.fillText(val, leftM - 12, y + 4);

        ctx.beginPath();
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        ctx.moveTo(leftM, y);
        ctx.lineTo(leftM + chartW, y);
        ctx.stroke();
    }

    // Benchmark threshold (90%)
    const targetY = topM + chartH - 0.90 * chartH;
    ctx.beginPath();
    ctx.setLineDash([5, 4]);
    ctx.strokeStyle = "#FF5252";
    ctx.lineWidth = 2;
    ctx.moveTo(leftM, targetY);
    ctx.lineTo(leftM + chartW, targetY);
    ctx.stroke();
    ctx.setLineDash([]);

    const slotW = chartW / factors.length;
    const barW = 64;

    ctx.textAlign = "center";
    factors.forEach((factor, i) => {
        const val = values[i];
        const bh = val * chartH;
        const bx = leftM + i * slotW + (slotW - barW) / 2;
        const by = topM + chartH - bh;

        const color = val >= 0.90 ? "#00E676" : "#FFAB00";
        ctx.fillStyle = color;
        ctx.fillRect(bx, by, barW, bh);

        ctx.fillStyle = isDark ? "#F0F6FC" : "#0F172A";
        ctx.font = "bold 12px Inter, sans-serif";
        ctx.fillText(`${(val * 100).toFixed(0)}%`, bx + barW / 2, by - 8);

        ctx.fillStyle = textColor;
        ctx.font = "12px Inter, sans-serif";
        ctx.fillText(factor, bx + barW / 2, topM + chartH + 24);
    });
}

// ── 7. Data Tables & KPI Generators ──
function initTablesAndKpis() {
    // KPI Cards
    const kpis = [
        { label: "Days Since Last Accident", value: "142 Days", sub: "Goal: 365+ Days", color: "#00E676" },
        { label: "First Aid Cases (Q1)", value: "2 Cases", sub: "Cell 4 Assembly", color: "#FFAB00" },
        { label: "Near Miss Logs", value: "8 Logged", sub: "100% Investigated", color: "#58A6FF" },
        { label: "Safety Audit Compliance", value: "98.4%", sub: "+1.2% vs last shift", color: "#00E676" }
    ];

    ["home-safety-kpis", "safety-view-kpis"].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = kpis.map(k => `
            <div class="kpi-card" style="--kpi-color: ${k.color};">
                <span class="kpi-label">${k.label}</span>
                <span class="kpi-value">${k.value}</span>
                <span class="kpi-subtext">${k.sub}</span>
            </div>
        `).join("");
    });

    // Pareto Dashboard Loss Analysis Table
    const paretoTableBody = document.querySelector("#home-pareto-table tbody");
    if (paretoTableBody) {
        const paretoData = [
            { rank: 1, category: "Milling Tool Wear / Broken Cutter", occ: 38, cum: "34.5%", sev: "Critical", cell: "Cell 1 (Machining)" },
            { rank: 2, category: "Raw Material Thickness Variance", occ: 27, cum: "59.1%", sev: "High", cell: "Cell 2 (Stamping)" },
            { rank: 3, category: "Conveyor Sensor Alignment Slip", occ: 19, cum: "76.4%", sev: "Moderate", cell: "Cell 4 (Assembly)" },
            { rank: 4, category: "Coating Nozzle Clog / Pressure", occ: 15, cum: "90.0%", sev: "Moderate", cell: "Cell 3 (Coating)" },
            { rank: 5, category: "Operator Changeover Setup Delay", occ: 11, cum: "100.0%", sev: "Low", cell: "Cell 5 (Inspection)" }
        ];
        paretoTableBody.innerHTML = paretoData.map(row => `
            <tr>
                <td><strong>#${row.rank}</strong></td>
                <td>${row.category}</td>
                <td><strong>${row.occ}</strong></td>
                <td>${row.cum}</td>
                <td><span class="badge badge-${row.sev.toLowerCase()}">${row.sev}</span></td>
                <td>${row.cell}</td>
            </tr>
        `).join("");
    }

    // Pareto Admin Yellow Concern Logs (`home-pareto-admin-table` & `pareto-tab-admin-table`)
    const adminConcerns = [
        { date: "2026-07-11 14:20", cat: "Quality / Tooling", comment: "Tooling wear detected during dimensional check on part #A-402.", action: "Replace carbide insert and recalibrate probe offset.", owner: "J. Miller (Tooling Lead)", status: "<span class='badge badge-medium'>In Progress</span>" },
        { date: "2026-07-10 09:15", cat: "Safety / Ergonomics", comment: "Assembly fixture height causing operator shoulder strain.", action: "Install adjustable lift table under Station 4.", owner: "M. Torres (Safety Rep)", status: "<span class='badge badge-high'>Open</span>" },
        { date: "2026-07-08 16:45", cat: "Delivery / Logistics", comment: "Pallet wrapper jam delayed shipping dispatch by 35 minutes.", action: "Replace optical feed sensor and tension spring.", owner: "R. Davis (Maintenance)", status: "<span class='badge badge-low'>Resolved</span>" }
    ];

    ["#home-pareto-admin-table tbody", "#pareto-tab-admin-table tbody"].forEach(sel => {
        const tbody = document.querySelector(sel);
        if (tbody) {
            tbody.innerHTML = adminConcerns.map(c => `
                <tr>
                    <td><code>${c.date}</code></td>
                    <td><strong>${c.cat}</strong></td>
                    <td>${c.comment}</td>
                    <td>${c.action}</td>
                    <td>${c.owner}</td>
                    <td>${c.status}</td>
                </tr>
            `).join("");
        }
    });

    // Safety Admin Incident Table (`safety-admin-table`)
    const safetyAdminTbody = document.querySelector("#safety-admin-table tbody");
    if (safetyAdminTbody) {
        const safetyLogs = [
            { id: "S-2026-014", date: "2026-07-09 • Shift 1", loc: "Cell 4 (Assembly)", desc: "Minor First Aid cut from sharp metal burr on chassis bracket.", sev: "Low", action: "Issue Kevlar gloves and deburr parts prior to assembly bench.", status: "<span class='badge badge-low'>Closed</span>" },
            { id: "S-2026-015", date: "2026-07-11 • Shift 2", loc: "Cell 1 (Machining)", desc: "Near miss: coolant mist hose coupling came loose under pressure.", sev: "Moderate", action: "Replace quick-disconnect couplers across all 6 CNC mills.", status: "<span class='badge badge-medium'>In Progress</span>" }
        ];
        safetyAdminTbody.innerHTML = safetyLogs.map(l => `
            <tr>
                <td><strong>${l.id}</strong></td>
                <td><code>${l.date}</code></td>
                <td>${l.loc}</td>
                <td>${l.desc}</td>
                <td><span class="badge badge-${l.sev.toLowerCase()}">${l.sev}</span></td>
                <td>${l.action}</td>
                <td>${l.status}</td>
            </tr>
        `).join("");
    }

    // Pareto Category Table (`pareto-category-table`)
    const paretoCatTbody = document.querySelector("#pareto-category-table tbody");
    if (paretoCatTbody) {
        const catData = [
            { code: "CAT-101", name: "Mechanical & Tooling Failure", hours: "42.5 hrs", cost: "$14,200", driver: "Carbide tool wear & spindle runout", trend: "📉 Decreasing" },
            { code: "CAT-102", name: "Material Variance & Scrap", hours: "31.0 hrs", cost: "$9,800", driver: "Supplier sheet gauge tolerance", trend: "━ Stable" },
            { code: "CAT-103", name: "Automation & Sensor Jams", hours: "18.5 hrs", cost: "$6,100", driver: "Optical sensor dust accumulation", trend: "📉 Decreasing" }
        ];
        paretoCatTbody.innerHTML = catData.map(c => `
            <tr>
                <td><code>${c.code}</code></td>
                <td><strong>${c.name}</strong></td>
                <td>${c.hours}</td>
                <td><strong>${c.cost}</strong></td>
                <td>${c.driver}</td>
                <td>${c.trend}</td>
            </tr>
        `).join("");
    }

    // Log New Concern Button Modal Trigger
    const btnAdd = document.getElementById("btn-add-concern");
    if (btnAdd) {
        btnAdd.addEventListener("click", () => {
            const comment = prompt("Enter Concern / Root Cause description:", "New observed concern on work bench...");
            if (comment) {
                const now = new Date().toISOString().slice(0, 16).replace("T", " ");
                const newRow = `
                    <tr>
                        <td><code>${now}</code></td>
                        <td><strong>Quality / Audit</strong></td>
                        <td>${comment}</td>
                        <td>Pending lead review & assignment</td>
                        <td>Unassigned</td>
                        <td><span class='badge badge-high'>Open</span></td>
                    </tr>
                `;
                ["#home-pareto-admin-table tbody", "#pareto-tab-admin-table tbody"].forEach(sel => {
                    const tbody = document.querySelector(sel);
                    if (tbody) tbody.insertAdjacentHTML("afterbegin", newRow);
                });
                alert("✅ New Concern Logged successfully into the Pareto Admin Audit Trail!");
            }
        });
    }
}

// ── 8. Interactive Physiological Questionnaire (`SafetyAnswerWidget`) ──
function initQuestionnaire() {
    const container = document.getElementById("questionnaire-items");
    const scoreEl = document.getElementById("questionnaire-score");
    if (!container || !scoreEl) return;

    const questions = [
        { id: "q1", title: "Motivation & Cognitive Readiness", desc: "Operator reports high focus and alertness without signs of acute fatigue.", checked: true },
        { id: "q2", title: "Connectedness & Communication", desc: "Two-way radio / shift handover briefing completed and verified.", checked: true },
        { id: "q3", title: "Workload & Pacing Balance", desc: "Takt time balanced; no excessive ergonomic strain or rushing required.", checked: true },
        { id: "q4", title: "Teamwork & Peer Support", desc: "Cell partner assigned and backup assistance protocols established.", checked: true },
        { id: "q5", title: "Personal Protective Equipment (PPE)", desc: "Safety glasses, steel-toe boots, and hearing protection verified 100%.", checked: true },
        { id: "q6", title: "Ergonomic Station Calibration", desc: "Work bench height and anti-fatigue floor mat positioned properly.", checked: true },
        { id: "q7", title: "Emergency Exits & E-Stops Clear", desc: "All aisleways free of obstructions and emergency stop buttons tested.", checked: false },
        { id: "q8", title: "First Aid & Spill Kit Readiness", desc: "Eye wash station inspected and chemical spill kit fully stocked.", checked: true }
    ];

    const updateScore = () => {
        const checkboxes = container.querySelectorAll("input[type='checkbox']");
        const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
        const score = Math.round((checkedCount / checkboxes.length) * 100);
        scoreEl.textContent = `${score}%`;
        scoreEl.style.color = score >= 90 ? "var(--status-green)" : score >= 75 ? "var(--status-yellow)" : "var(--status-red)";
    };

    container.innerHTML = questions.map(q => `
        <label class="q-item" for="${q.id}">
            <input type="checkbox" id="${q.id}" ${q.checked ? "checked" : ""}>
            <div class="q-text">
                <h4>${q.title}</h4>
                <p>${q.desc}</p>
            </div>
        </label>
    `).join("");

    container.querySelectorAll("input[type='checkbox']").forEach(cb => {
        cb.addEventListener("change", updateScore);
    });

    updateScore();
}

// ── 9. JSON Contract Viewer (`JsonContractViewerWidget`) ──
function initJsonViewer() {
    const container = document.getElementById("json-contract-viewer");
    if (!container) return;

    const contractJson = {
        "$schema": "https://dashboard-testing.internal/schemas/v2/sqdp-contract.json",
        "systemVersion": "2.4.0-SOLID-Web",
        "activeContext": {
            "granularity": "Fiscal Weeks",
            "windowLabel": "Q1 (Weeks 1–13)",
            "fiscalYear": 2026,
            "teamScope": "All Work Cells",
            "isSprintCapable": true,
            "columns": 13
        },
        "widgets": [
            {
                "id": "sqdp_board_home",
                "type": "SqdpBoardWidget",
                "mixins": ["TimeAware", "BaseGraphicWidget"],
                "reactivity": "Auto-subscribed to TimePeriodRegistry"
            },
            {
                "id": "burndown_home",
                "type": "BurndownChartWidget",
                "mixins": ["TimeAware", "BaseChartWidget"],
                "fallbackWarning": "Sprint Burndown Unavailable (Triggered on Days/Months)"
            }
        ],
        "kpiThresholds": {
            "safetyMinScore": 0.90,
            "qualityTargetYield": 0.93,
            "deliveryOnTimeTarget": 0.90
        }
    };

    // Syntax highlight JSON string
    const jsonString = JSON.stringify(contractJson, null, 4);
    const highlighted = jsonString.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, match => {
        let cls = "json-number";
        if (/^"/.test(match)) {
            cls = /:$/.test(match) ? "json-key" : "json-string";
        } else if (/true|false/.test(match)) {
            cls = "json-boolean";
        } else if (/null/.test(match)) {
            cls = "json-null";
        }
        return `<span class="${cls}">${match}</span>`;
    });

    container.innerHTML = `<pre>${highlighted}</pre>`;

    const btnCopy = document.getElementById("btn-copy-json");
    if (btnCopy) {
        btnCopy.addEventListener("click", () => {
            navigator.clipboard.writeText(jsonString).then(() => {
                const orig = btnCopy.textContent;
                btnCopy.textContent = "✅ Copied to Clipboard!";
                setTimeout(() => { btnCopy.textContent = orig; }, 2000);
            });
        });
    }
}

// ── 10. Navigation & Theme Controller ──
function initNavigationAndTheme() {
    // Collapsible Sidebar
    const sidebar = document.getElementById("sidebar");
    const toggleBtn = document.getElementById("sidebar-toggle");
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("collapsed");
        });
    }

    // Menu Navigation
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item[data-tab]");
    const tabViews = document.querySelectorAll(".tab-view[data-view]");
    const pageTitle = document.getElementById("page-title");

    const titles = {
        0: "Home — Executive Agile Dashboard (Where graphs exist)",
        1: "Safety — Complete Physiological Assessment View",
        2: "Pareto — Loss Analysis & Audit Log",
        3: "Data — Operations & Efficiency",
        4: "Users — User Management & Access",
        5: "Calculations — CI Contract Viewer",
        6: "Settings — System & Controls",
        7: "About — No-Code Grid Architecture"
    };

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const tabIdx = item.getAttribute("data-tab");
            navItems.forEach(btn => btn.classList.remove("active"));
            item.classList.add("active");

            if (pageTitle && titles[tabIdx]) {
                pageTitle.textContent = titles[tabIdx];
            }

            tabViews.forEach(view => {
                view.classList.toggle("active", view.getAttribute("data-view") === tabIdx);
            });

            // Re-render canvases if chart tabs are activated
            if (tabIdx === "0") {
                timeRegistry.broadcastPeriod(TimeSpanContext.fromForm());
                if (window.sqdpAspectChart) window.sqdpAspectChart.render();
            } else if (tabIdx === "1") {
                renderSafetyBarChart();
            }
        });
    });

    // Exit Demo button
    const closeBtn = document.getElementById("sidebar-close");
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            if (confirm("Exit Demo Dashboard?")) {
                window.location.reload();
            }
        });
    }

    // Top Filter Bar Dropdowns auto-emit
    const granularitySelect = document.getElementById("combo-granularity");
    const windowSelect = document.getElementById("combo-window");
    const yearSelect = document.getElementById("combo-year");
    const teamSelect = document.getElementById("combo-team");

    const updateWindowOptions = () => {
        const gran = granularitySelect.value;
        windowSelect.innerHTML = "";
        if (gran === "Fiscal Weeks") {
            ["Q1 (Weeks 1–13)", "Q2 (Weeks 14–26)", "Q3 (Weeks 27–39)", "Q4 (Weeks 40–52)"].forEach(w => {
                windowSelect.appendChild(new Option(w, w));
            });
        } else if (gran === "Days") {
            ["January (Days 1–31)", "February (Days 1–28)", "March (Days 1–31)", "April (Days 1–30)"].forEach(w => {
                windowSelect.appendChild(new Option(w, w));
            });
        } else {
            // Months
            ["H1 (Jan–Jun)", "H2 (Jul–Dec)", "Full FY 2026"].forEach(w => {
                windowSelect.appendChild(new Option(w, w));
            });
        }
    };

    if (granularitySelect) {
        granularitySelect.addEventListener("change", () => {
            updateWindowOptions();
            timeRegistry.broadcastPeriod(TimeSpanContext.fromForm());
        });
    }

    [windowSelect, yearSelect, teamSelect].forEach(sel => {
        if (sel) {
            sel.addEventListener("change", () => {
                timeRegistry.broadcastPeriod(TimeSpanContext.fromForm());
            });
        }
    });

    // Theme Toggle (`#theme-toggle`)
    const themeBtn = document.getElementById("theme-toggle");
    const themeIcon = document.getElementById("theme-icon");
    const themeText = document.getElementById("theme-text");

    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            const html = document.documentElement;
            const current = html.getAttribute("data-theme");
            if (current === "dark") {
                html.setAttribute("data-theme", "light");
                if (themeIcon) themeIcon.textContent = "☀️";
                if (themeText) themeText.textContent = "Light";
            } else {
                html.setAttribute("data-theme", "dark");
                if (themeIcon) themeIcon.textContent = "🌙";
                if (themeText) themeText.textContent = "Dark";
            }
            // Re-render all active canvas charts with the updated theme color scheme
            timeRegistry.broadcastPeriod(TimeSpanContext.fromForm());
            if (window.sqdpAspectChart) window.sqdpAspectChart.render();
            renderSafetyBarChart();
        });
    }
}

// ── 11. Application Initialization (`window.onload`) ──
window.addEventListener("DOMContentLoaded", () => {
    console.log("⚡ Dashboard Testing Web Engine Initializing...");

    // Initialize widgets
    const sqdpBoard = new SqdpBoardWidget("sqdp-grid-container", "sqdp-board-title");
    window.sqdpAspectChart = new SqdpAspectChartWidget("aspect-chart-canvas");
    const progressChart = new ProgressBarChartWidget("progress-chart-canvas", "progress-chart-title");
    const burndownChart = new BurndownChartWidget("burndown-chart-canvas", "burndown-chart-title");

    initTablesAndKpis();
    initQuestionnaire();
    initJsonViewer();
    initNavigationAndTheme();

    // Broadcast initial query on startup to populate all subscribed components
    timeRegistry.broadcastPeriod(TimeSpanContext.fromForm());
});
