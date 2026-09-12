/* ═══════════════════════════════════════════════════════════════════════
   Text → Chart JSON — Client-side Application Logic
   Fully offline · Powered by Outlines + Local Transformer
   ═══════════════════════════════════════════════════════════════════════ */

(function () {
    "use strict";

    // ── DOM references ────────────────────────────────────────────────
    const inputText = document.getElementById("input-text");
    const charCount = document.getElementById("char-count");
    const extractBtn = document.getElementById("extract-btn");
    const clearBtn = document.getElementById("clear-btn");
    const badgeModelName = document.getElementById("badge-model-name");
    const examplesChips = document.getElementById("examples-chips");

    const outputEmpty = document.getElementById("output-empty");
    const outputError = document.getElementById("output-error");
    const errorMessage = document.getElementById("error-message");
    const outputJson = document.getElementById("output-json");
    const metaChips = document.getElementById("meta-chips");
    const jsonCode = document.getElementById("json-code");

    const copyBtn = document.getElementById("copy-btn");
    const copyLabel = copyBtn.querySelector(".copy-label");

    const chartPreview = document.getElementById("chart-preview");
    const chartCanvas = document.getElementById("chart-canvas");

    let currentPayload = null;
    let chartInstance = null;

    // ── Load model info ───────────────────────────────────────────────
    async function loadModelInfo() {
        try {
            const res = await fetch("/api/model-info");
            if (!res.ok) return;
            const info = await res.json();
            const name = info.model || "local";
            // Show only the last part of the model path for brevity
            badgeModelName.textContent = name.includes("/")
                ? name.split("/").pop()
                : name;
        } catch (_) {
            badgeModelName.textContent = "local";
        }
    }
    loadModelInfo();

    // ── Character counter ─────────────────────────────────────────────
    inputText.addEventListener("input", () => {
        const len = inputText.value.length;
        charCount.textContent = `${len.toLocaleString()} char${len !== 1 ? "s" : ""}`;
    });

    // ── Clear ─────────────────────────────────────────────────────────
    clearBtn.addEventListener("click", () => {
        inputText.value = "";
        charCount.textContent = "0 chars";
        showEmpty();
        inputText.focus();
    });

    // ── Load examples ─────────────────────────────────────────────────
    async function loadExamples() {
        try {
            const res = await fetch("/api/examples");
            if (!res.ok) return;
            const examples = await res.json();
            examplesChips.innerHTML = "";
            examples.forEach((ex) => {
                const chip = document.createElement("button");
                chip.className = "chip";
                chip.type = "button";
                chip.textContent = ex.label;
                chip.addEventListener("click", () => {
                    inputText.value = ex.text;
                    inputText.dispatchEvent(new Event("input"));
                    inputText.focus();
                });
                examplesChips.appendChild(chip);
            });
        } catch (_) {
            /* silently skip */
        }
    }
    loadExamples();

    // ── State management ──────────────────────────────────────────────
    function showEmpty() {
        outputEmpty.classList.remove("hidden");
        outputError.classList.add("hidden");
        outputJson.classList.add("hidden");
        chartPreview.classList.add("hidden");
        copyBtn.disabled = true;
        currentPayload = null;
        destroyChart();
    }

    function showError(msg) {
        outputEmpty.classList.add("hidden");
        outputError.classList.remove("hidden");
        outputJson.classList.add("hidden");
        chartPreview.classList.add("hidden");
        errorMessage.textContent = msg;
        copyBtn.disabled = true;
        currentPayload = null;
        destroyChart();
    }

    function showResult(payload) {
        currentPayload = payload;
        outputEmpty.classList.add("hidden");
        outputError.classList.add("hidden");
        outputJson.classList.remove("hidden");
        copyBtn.disabled = false;

        // Meta chips
        renderMetaChips(payload);

        // Syntax-highlighted JSON
        jsonCode.innerHTML = syntaxHighlight(JSON.stringify(payload, null, 2));

        // Chart preview
        renderChart(payload);
    }

    // ── Meta chips ────────────────────────────────────────────────────
    function renderMetaChips(payload) {
        const items = [
            { label: "Type", value: payload.chart_type },
            { label: "X", value: payload.xAxis },
            { label: "Y", value: payload.yAxis },
            { label: "Points", value: payload.data.length },
        ];
        metaChips.innerHTML = items
            .map(
                (i) =>
                    `<span class="meta-chip">
                        <span class="chip-label">${i.label}</span>
                        <span class="chip-value">${i.value}</span>
                    </span>`
            )
            .join("");
    }

    // ── JSON Syntax Highlighting ──────────────────────────────────────
    function syntaxHighlight(json) {
        return json.replace(
            /("(\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g,
            (match) => {
                let cls = "json-number";
                if (/^"/.test(match)) {
                    cls = /:$/.test(match) ? "json-key" : "json-string";
                } else if (/true|false/.test(match)) {
                    cls = "json-bool";
                } else if (/null/.test(match)) {
                    cls = "json-null";
                }
                return `<span class="${cls}">${escapeHtml(match)}</span>`;
            }
        );
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    // ── Chart.js preview ──────────────────────────────────────────────
    const CHART_COLORS = [
        "rgba(138, 120, 255, 0.85)",
        "rgba(52, 211, 153, 0.85)",
        "rgba(251, 191, 36, 0.85)",
        "rgba(248, 113, 113, 0.85)",
        "rgba(96, 165, 250, 0.85)",
        "rgba(244, 114, 182, 0.85)",
        "rgba(167, 139, 250, 0.85)",
        "rgba(45, 212, 191, 0.85)",
    ];

    const CHART_BORDERS = CHART_COLORS.map((c) => c.replace("0.85", "1"));

    function destroyChart() {
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }
    }

    function renderChart(payload) {
        destroyChart();

        if (!payload.data || payload.data.length === 0) {
            chartPreview.classList.add("hidden");
            return;
        }

        chartPreview.classList.remove("hidden");

        const labels = payload.data.map((d) => d.label ?? "");
        const values = payload.data.map((d) => {
            const v = d.value;
            return typeof v === "number" ? v : parseFloat(v) || 0;
        });

        const chartTypeMap = {
            time_series: "line",
            line: "line",
            bar: "bar",
            pie: "pie",
            scatter: "scatter",
            histogram: "bar",
            area: "line",
            table: "bar",
        };

        let cjsType = chartTypeMap[payload.chart_type] || "bar";

        // If the model selected a scatter plot but the labels are categorical strings,
        // it will plot them all at x=0. Fallback to a bar chart instead.
        if (cjsType === "scatter") {
            const hasStringLabels = payload.data.some((d) => isNaN(parseFloat(d.label)));
            if (hasStringLabels) {
                cjsType = "bar";
            }
        }
        const isPie = cjsType === "pie";
        const isArea = payload.chart_type === "area";

        const dataset = {
            label: payload.yAxis,
            data: values,
            backgroundColor: isPie
                ? CHART_COLORS.slice(0, values.length)
                : isArea
                    ? "rgba(138, 120, 255, 0.15)"
                    : CHART_COLORS[0],
            borderColor: isPie
                ? CHART_BORDERS.slice(0, values.length)
                : CHART_COLORS[0],
            borderWidth: isPie ? 2 : 2.5,
            tension: 0.4,
            fill: isArea,
            pointRadius: cjsType === "line" ? 5 : undefined,
            pointBackgroundColor: CHART_COLORS[0],
            pointBorderColor: "#0b0d1a",
            pointBorderWidth: 2,
        };

        const config = {
            type: cjsType === "scatter" ? "scatter" : cjsType,
            data: {
                labels: labels,
                datasets: [dataset],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: isPie,
                        position: "bottom",
                        labels: {
                            color: "#9399c4",
                            font: { family: "'Inter', sans-serif", size: 11 },
                            padding: 16,
                        },
                    },
                    title: {
                        display: true,
                        text: payload.title,
                        color: "#e8eaf6",
                        font: {
                            family: "'Inter', sans-serif",
                            size: 14,
                            weight: "600",
                        },
                        padding: { bottom: 16 },
                    },
                    tooltip: {
                        backgroundColor: "rgba(16, 19, 40, 0.92)",
                        titleColor: "#e8eaf6",
                        bodyColor: "#9399c4",
                        borderColor: "rgba(100, 116, 200, 0.2)",
                        borderWidth: 1,
                        cornerRadius: 8,
                        titleFont: { family: "'Inter', sans-serif" },
                        bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
                    },
                },
                scales: isPie
                    ? {}
                    : {
                        x: {
                            ticks: { color: "#5c6190", font: { size: 11 } },
                            grid: { color: "rgba(100, 116, 200, 0.06)" },
                            title: {
                                display: true,
                                text: payload.xAxis,
                                color: "#9399c4",
                                font: { size: 12, weight: "500" },
                            },
                        },
                        y: {
                            ticks: { color: "#5c6190", font: { size: 11 } },
                            grid: { color: "rgba(100, 116, 200, 0.06)" },
                            title: {
                                display: true,
                                text: payload.yAxis,
                                color: "#9399c4",
                                font: { size: 12, weight: "500" },
                            },
                            beginAtZero: true,
                        },
                    },
                animation: {
                    duration: 800,
                    easing: "easeOutQuart",
                },
            },
        };

        // For scatter, convert data format
        if (cjsType === "scatter") {
            config.data.labels = undefined;
            dataset.data = payload.data.map((d) => ({
                x: parseFloat(d.label) || 0,
                y: parseFloat(d.value) || 0,
            }));
        }

        chartInstance = new Chart(chartCanvas, config);
    }

    // ── Copy to clipboard ─────────────────────────────────────────────
    copyBtn.addEventListener("click", async () => {
        if (!currentPayload) return;
        try {
            await navigator.clipboard.writeText(
                JSON.stringify(currentPayload, null, 2)
            );
            copyBtn.classList.add("copied");
            copyLabel.textContent = "Copied!";
            setTimeout(() => {
                copyBtn.classList.remove("copied");
                copyLabel.textContent = "Copy";
            }, 2000);
        } catch (_) {
            /* fallback: do nothing */
        }
    });

    // ── Extract handler ───────────────────────────────────────────────
    async function handleExtract() {
        const text = inputText.value.trim();
        if (!text) {
            inputText.focus();
            return;
        }

        // Enter loading state
        extractBtn.classList.add("loading");
        extractBtn.disabled = true;

        try {
            const res = await fetch("/api/extract", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text }),
            });

            const data = await res.json();

            if (data.success) {
                showResult(data.payload);
            } else {
                showError(data.error || "Unknown error occurred.");
            }
        } catch (err) {
            showError(`Network error: ${err.message}`);
        } finally {
            extractBtn.classList.remove("loading");
            extractBtn.disabled = false;
        }
    }

    extractBtn.addEventListener("click", handleExtract);

    // Ctrl+Enter / Cmd+Enter shortcut
    inputText.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            handleExtract();
        }
    });
})();
