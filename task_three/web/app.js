// NexusFunnel Dashboard Application Logic
document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize global state
    let activeTab = "overview";
    let filters = {
        source: "all",
        campaign: "all",
        device: "all"
    };
    let explorerSearchQuery = "";
    let explorerFilterStage = "all";
    let explorerFilterSource = "all";
    let explorerSortField = "session_start";
    let explorerSortAsc = false;
    
    // Global chart references (for destroying/updating)
    let charts = {
        funnel: null,
        device: null,
        trends: null,
        transitions: null,
        channelConv: null,
        channelCac: null,
        deviceConv: null,
        dropoffRates: null
    };

    // 2. Tab Navigation
    const navItems = document.querySelectorAll(".sidebar-nav li");
    const tabContents = document.querySelectorAll(".tab-content");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            if (tabId) {
                // Remove active classes
                navItems.forEach(nav => nav.classList.remove("active"));
                tabContents.forEach(tab => tab.classList.remove("active"));
                
                // Add active classes
                item.classList.add("active");
                document.getElementById(`tab-${tabId}`).classList.add("active");
                activeTab = tabId;
                
                // Redraw charts if tab changes to fix Chart.js sizing glitches
                Object.values(charts).forEach(chart => {
                    if (chart) chart.resize();
                });
            }
        });
    });

    // 3. Dynamic Filter Controls
    const filterSource = document.getElementById("filter-source");
    const filterCampaign = document.getElementById("filter-campaign");
    const filterDevice = document.getElementById("filter-device");
    const resetFiltersBtn = document.getElementById("reset-filters");

    const handleFilterChange = () => {
        filters.source = filterSource.value;
        filters.campaign = filterCampaign.value;
        filters.device = filterDevice.value;
        updateDashboard();
    };

    filterSource.addEventListener("change", handleFilterChange);
    filterCampaign.addEventListener("change", handleFilterChange);
    filterDevice.addEventListener("change", handleFilterChange);

    resetFiltersBtn.addEventListener("click", () => {
        filterSource.value = "all";
        filterCampaign.value = "all";
        filterDevice.value = "all";
        filters = { source: "all", campaign: "all", device: "all" };
        updateDashboard();
    });

    // 4. Session Explorer Controls
    const explorerSearch = document.getElementById("explorer-search");
    const expFilterStage = document.getElementById("explorer-filter-stage");
    const expFilterSource = document.getElementById("explorer-filter-source");

    explorerSearch.addEventListener("input", (e) => {
        explorerSearchQuery = e.target.value.toLowerCase().trim();
        renderExplorerTable();
    });

    expFilterStage.addEventListener("change", (e) => {
        explorerFilterStage = e.target.value;
        renderExplorerTable();
    });

    expFilterSource.addEventListener("change", (e) => {
        explorerFilterSource = e.target.value;
        renderExplorerTable();
    });

    const sortableHeaders = document.querySelectorAll("#table-explorer th.sortable");
    sortableHeaders.forEach(header => {
        header.addEventListener("click", () => {
            const field = header.getAttribute("data-sort");
            if (explorerSortField === field) {
                explorerSortAsc = !explorerSortAsc; // Toggle direction
            } else {
                explorerSortField = field;
                explorerSortAsc = true;
            }
            
            // Update sort icons
            sortableHeaders.forEach(h => {
                const icon = h.querySelector("i");
                icon.className = "fa-solid fa-sort";
            });
            const currentIcon = header.querySelector("i");
            currentIcon.className = explorerSortAsc ? "fa-solid fa-sort-up" : "fa-solid fa-sort-down";
            
            renderExplorerTable();
        });
    });

    // 5. Core Dashboard Update Engine
    const updateDashboard = () => {
        // A. Filter Dataset based on header controls
        const sessions = FUNNEL_DATA.sessions;
        const filtered = sessions.filter(s => {
            const matchesSource = filters.source === "all" || s.source === filters.source;
            const matchesCampaign = filters.campaign === "all" || s.campaign === filters.campaign;
            const matchesDevice = filters.device === "all" || s.device === filters.device;
            return matchesSource && matchesCampaign && matchesDevice;
        });

        // B. Recompute KPIs
        const kpis = calculateKPIs(filtered);
        updateKPIsUI(kpis);

        // C. Update Overview Tab Charts & Table
        updateFunnelChart(kpis);
        updateDeviceChart(filtered);
        updateTrendsChart(filtered);
        updateTransitionsChart(kpis);

        // D. Update Acquisition Tab Charts & Table
        updateAcquisitionTab(filtered);

        // E. Update Dropoffs Tab
        updateDropoffsTab(filtered, kpis);

        // F. Update Data Explorer
        renderExplorerTable(filtered);

        // G. Update Strategy / Insights Stats
        updateInsightsUI(kpis);
    };

    // 6. Mathematical & Aggregation Helper Functions
    const calculateKPIs = (data) => {
        let visitors = data.length;
        let leads = 0;
        let trials = 0;
        let customers = 0;
        let spend = 0;

        data.forEach(s => {
            spend += s.click_cost;
            if (s.lead_time !== "") leads++;
            if (s.trial_time !== "") trials++;
            if (s.purchase_time !== "") customers++;
        });

        return {
            visitors: visitors,
            leads: leads,
            trials: trials,
            customers: customers,
            spend: spend,
            cpl: leads > 0 ? (spend / leads) : 0,
            cac: customers > 0 ? (spend / customers) : 0,
            convVisitorToLead: visitors > 0 ? (leads / visitors) : 0,
            convLeadToTrial: leads > 0 ? (trials / leads) : 0,
            convTrialToCustomer: trials > 0 ? (customers / trials) : 0,
            convOverall: visitors > 0 ? (customers / visitors) : 0
        };
    };

    const updateKPIsUI = (kpis) => {
        document.querySelector("#kpi-visitors .kpi-value").textContent = kpis.visitors.toLocaleString();
        document.querySelector("#kpi-spend .kpi-value").textContent = formatCurrency(kpis.spend);
        
        document.querySelector("#kpi-cac .kpi-value").textContent = formatCurrency(kpis.cac);
        const cacCard = document.querySelector("#kpi-cac");
        const cacTrend = cacCard.querySelector(".trend");
        if (kpis.cac > 75) {
            cacTrend.className = "trend negative";
            cacTrend.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> Elevated`;
        } else if (kpis.cac > 0 && kpis.cac < 45) {
            cacTrend.className = "trend positive";
            cacTrend.innerHTML = `<i class="fa-solid fa-arrow-trend-down"></i> Highly Efficient`;
        } else {
            cacTrend.className = "trend neutral";
            cacTrend.innerHTML = `<i class="fa-solid fa-minus"></i> Standard`;
        }

        document.querySelector("#kpi-conversion .kpi-value").textContent = formatPercent(kpis.convOverall);
        const convCard = document.querySelector("#kpi-conversion");
        const convTrend = convCard.querySelector(".trend");
        if (kpis.convOverall > 0.04) {
            convTrend.className = "trend positive";
            convTrend.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> Exceptional`;
        } else if (kpis.convOverall < 0.02) {
            convTrend.className = "trend negative";
            convTrend.innerHTML = `<i class="fa-solid fa-arrow-trend-down"></i> Needs Optimization`;
        } else {
            convTrend.className = "trend neutral";
            convTrend.innerHTML = `<i class="fa-solid fa-minus"></i> Stable`;
        }
    };

    const updateInsightsUI = (kpis) => {
        document.getElementById("insight-stat-visitors").textContent = kpis.visitors.toLocaleString();
        document.getElementById("insight-stat-conversion").textContent = formatPercent(kpis.convOverall);
        
        const cacEl = document.getElementById("insight-stat-cac");
        cacEl.textContent = formatCurrency(kpis.cac);
        if (kpis.cac > 75) {
            cacEl.className = "bullet-val text-accent-red";
        } else if (kpis.cac > 0 && kpis.cac < 45) {
            cacEl.className = "bullet-val text-accent-green";
        } else {
            cacEl.className = "bullet-val text-accent-amber";
        }
        
        document.getElementById("insight-stat-spend").textContent = formatShortCurrency(kpis.spend);
    };

    // 7. Chart Renderers
    const updateFunnelChart = (kpis) => {
        if (charts.funnel) charts.funnel.destroy();

        const ctx = document.getElementById("chart-funnel").getContext("2d");
        charts.funnel = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["Sessions (100%)", `Leads (${formatPercent(kpis.convVisitorToLead)})`, `Trials (${formatPercent(kpis.convVisitorToLead * kpis.convLeadToTrial)})`, `Customers (${formatPercent(kpis.convOverall)})`],
                datasets: [{
                    data: [kpis.visitors, kpis.leads, kpis.trials, kpis.customers],
                    backgroundColor: ["#4f46e5", "#06b6d4", "#f59e0b", "#10b981"],
                    borderRadius: 8,
                    barThickness: 35
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const val = context.raw;
                                const rate = kpis.visitors > 0 ? (val / kpis.visitors * 100).toFixed(1) : 0;
                                return `Volume: ${val.toLocaleString()} (${rate}% of start)`;
                            }
                        }
                    }
                },
                scales: {
                    x: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { grid: { display: false }, ticks: { color: "#94a3b8", font: { family: "Outfit", weight: "bold" } } }
                }
            }
        });
    };

    const updateDeviceChart = (data) => {
        const counts = { Desktop: 0, Mobile: 0, Tablet: 0 };
        data.forEach(s => {
            if (counts[s.device] !== undefined) counts[s.device]++;
        });

        if (charts.device) charts.device.destroy();

        const ctx = document.getElementById("chart-device").getContext("2d");
        charts.device = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: Object.keys(counts),
                datasets: [{
                    data: Object.values(counts),
                    backgroundColor: ["#4f46e5", "#06b6d4", "#f59e0b"],
                    borderWidth: 2,
                    borderColor: "#172033"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: "#94a3b8", font: { family: "Outfit" }, boxWidth: 12 }
                    }
                }
            }
        });
    };

    const updateTrendsChart = (data) => {
        const months = getMonthSeries("2026-01", "2026-06");
        const activeSeries = [];
        const leadSeries = [];
        const trialSeries = [];
        const customerSeries = [];

        months.forEach(m => {
            let vis = 0;
            let lds = 0;
            let tls = 0;
            let cust = 0;

            data.forEach(s => {
                if (s.session_start.startsWith(m)) {
                    vis++;
                    if (s.lead_time !== "") lds++;
                    if (s.trial_time !== "") tls++;
                    if (s.purchase_time !== "") cust++;
                }
            });

            activeSeries.push(vis);
            leadSeries.push(lds);
            trialSeries.push(tls);
            customerSeries.push(cust);
        });

        if (charts.trends) charts.trends.destroy();

        const ctx = document.getElementById("chart-trends").getContext("2d");
        charts.trends = new Chart(ctx, {
            type: "line",
            data: {
                labels: months.map(m => formatMonthLabel(m)),
                datasets: [
                    {
                        label: "Website Visitors",
                        data: activeSeries,
                        borderColor: "#4f46e5",
                        backgroundColor: "transparent",
                        tension: 0.3,
                        borderWidth: 2
                    },
                    {
                        label: "Leads",
                        data: leadSeries,
                        borderColor: "#f59e0b",
                        backgroundColor: "transparent",
                        tension: 0.3,
                        borderWidth: 2
                    },
                    {
                        label: "Trials started",
                        data: trialSeries,
                        borderColor: "#06b6d4",
                        backgroundColor: "transparent",
                        tension: 0.3,
                        borderWidth: 2
                    },
                    {
                        label: "Paying Customers",
                        data: customerSeries,
                        borderColor: "#10b981",
                        backgroundColor: "rgba(16, 185, 129, 0.05)",
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2.5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#94a3b8", font: { family: "Outfit" } } }
                },
                scales: {
                    x: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8", font: { family: "Outfit" } } }
                }
            }
        });
    };

    const updateTransitionsChart = (kpis) => {
        if (charts.transitions) charts.transitions.destroy();

        const ctx = document.getElementById("chart-transitions").getContext("2d");
        charts.transitions = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["Visitor-to-Lead", "Lead-to-Trial", "Trial-to-Customer"],
                datasets: [{
                    data: [kpis.convVisitorToLead * 100, kpis.convLeadToTrial * 100, kpis.convTrialToCustomer * 100],
                    backgroundColor: "rgba(6, 182, 212, 0.75)",
                    borderColor: "#06b6d4",
                    borderWidth: 1.5,
                    borderRadius: 6,
                    barThickness: 25
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { 
                        min: 0, max: 100, 
                        ticks: { color: "#94a3b8", font: { family: "Outfit" }, callback: v => `${v}%` } 
                    }
                }
            }
        });
    };

    // 8. Acquisition Performance Tab
    const updateAcquisitionTab = (data) => {
        // Group by Source to get channel performance
        const sourceGroups = {};
        data.forEach(s => {
            if (!sourceGroups[s.source]) {
                sourceGroups[s.source] = { visitors: 0, leads: 0, trials: 0, customers: 0, spend: 0 };
            }
            const group = sourceGroups[s.source];
            group.visitors++;
            group.spend += s.click_cost;
            if (s.lead_time !== "") group.leads++;
            if (s.trial_time !== "") group.trials++;
            if (s.purchase_time !== "") group.customers++;
        });

        const channels = Object.keys(sourceGroups);
        const conversionRates = channels.map(ch => {
            const group = sourceGroups[ch];
            return group.visitors > 0 ? (group.customers / group.visitors * 100) : 0;
        });
        const cacs = channels.map(ch => {
            const group = sourceGroups[ch];
            return group.customers > 0 ? (group.spend / group.customers) : 0;
        });

        // Channel conversion chart
        if (charts.channelConv) charts.channelConv.destroy();
        const ctxConv = document.getElementById("chart-channel-conv").getContext("2d");
        charts.channelConv = new Chart(ctxConv, {
            type: "bar",
            data: {
                labels: channels,
                datasets: [{
                    data: conversionRates,
                    backgroundColor: "rgba(79, 70, 229, 0.75)",
                    borderColor: "#4f46e5",
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { min: 0, ticks: { color: "#94a3b8", font: { family: "Outfit" }, callback: v => `${v.toFixed(1)}%` } }
                }
            }
        });

        // Channel CAC chart
        if (charts.channelCac) charts.channelCac.destroy();
        const ctxCac = document.getElementById("chart-channel-cac").getContext("2d");
        charts.channelCac = new Chart(ctxCac, {
            type: "bar",
            data: {
                labels: channels,
                datasets: [{
                    data: cacs,
                    backgroundColor: "rgba(239, 68, 68, 0.75)",
                    borderColor: "#ef4444",
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { ticks: { color: "#94a3b8", font: { family: "Outfit" }, callback: v => `$${v}` } }
                }
            }
        });

        // Group by Campaign for Table
        const campaignGroups = {};
        data.forEach(s => {
            if (!campaignGroups[s.campaign]) {
                campaignGroups[s.campaign] = { visitors: 0, leads: 0, trials: 0, customers: 0, spend: 0 };
            }
            const group = campaignGroups[s.campaign];
            group.visitors++;
            group.spend += s.click_cost;
            if (s.lead_time !== "") group.leads++;
            if (s.trial_time !== "") group.trials++;
            if (s.purchase_time !== "") group.customers++;
        });

        // Render Campaign Table
        const tbody = document.querySelector("#table-campaigns tbody");
        tbody.innerHTML = "";
        
        Object.entries(campaignGroups)
            .sort((a,b) => b[1].visitors - a[1].visitors)
            .forEach(([camp, g]) => {
                const tr = document.createElement("tr");
                const convRate = g.visitors > 0 ? (g.customers / g.visitors * 100) : 0;
                const cpl = g.leads > 0 ? (g.spend / g.leads) : 0;
                const cac = g.customers > 0 ? (g.spend / g.customers) : 0;

                tr.innerHTML = `
                    <td><strong>${camp}</strong></td>
                    <td class="num-col">${g.visitors.toLocaleString()}</td>
                    <td class="num-col">${g.leads.toLocaleString()}</td>
                    <td class="num-col">${g.trials.toLocaleString()}</td>
                    <td class="num-col">${g.customers.toLocaleString()}</td>
                    <td class="num-col">${formatCurrency(g.spend)}</td>
                    <td class="num-col">${g.spend > 0 ? formatCurrency(cpl) : "-"}</td>
                    <td class="num-col">${g.spend > 0 ? formatCurrency(cac) : "-"}</td>
                    <td class="num-col">${convRate.toFixed(2)}%</td>
                `;
                tbody.appendChild(tr);
            });

        // Group by Device for Device Conversions chart
        const deviceGroups = { Desktop: { v: 0, c: 0 }, Mobile: { v: 0, c: 0 }, Tablet: { v: 0, c: 0 } };
        data.forEach(s => {
            if (deviceGroups[s.device]) {
                deviceGroups[s.device].v++;
                if (s.purchase_time !== "") deviceGroups[s.device].c++;
            }
        });

        const devices = Object.keys(deviceGroups);
        const deviceConvs = devices.map(d => {
            const g = deviceGroups[d];
            return g.v > 0 ? (g.c / g.v * 100) : 0;
        });

        if (charts.deviceConv) charts.deviceConv.destroy();
        const ctxDevConv = document.getElementById("chart-device-conv").getContext("2d");
        charts.deviceConv = new Chart(ctxDevConv, {
            type: "bar",
            data: {
                labels: devices,
                datasets: [{
                    data: deviceConvs,
                    backgroundColor: ["#4f46e5", "#06b6d4", "#f59e0b"],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { min: 0, ticks: { color: "#94a3b8", font: { family: "Outfit" }, callback: v => `${v.toFixed(1)}%` } }
                }
            }
        });
    };

    // 9. Drop-offs Tab
    const updateDropoffsTab = (data, kpis) => {
        const dropoffVisitorToLead = kpis.visitors - kpis.leads;
        const dropoffVisitorToLeadRate = kpis.visitors > 0 ? (dropoffVisitorToLead / kpis.visitors * 100) : 0;

        const dropoffLeadToTrial = kpis.leads - kpis.trials;
        const dropoffLeadToTrialRate = kpis.leads > 0 ? (dropoffLeadToTrial / kpis.leads * 100) : 0;

        const dropoffTrialToCustomer = kpis.trials - kpis.customers;
        const dropoffTrialToCustomerRate = kpis.trials > 0 ? (dropoffTrialToCustomer / kpis.trials * 100) : 0;

        // Render drop-offs summary panel
        const container = document.getElementById("dropoffs-summary-container");
        container.innerHTML = `
            <div class="dropoff-metric-row">
                <div class="dropoff-stage-info">
                    <span class="dropoff-stage-title">Visitor → Lead Drops</span>
                    <span class="dropoff-stage-volume">${dropoffVisitorToLead.toLocaleString()} users dropped out</span>
                </div>
                <span class="dropoff-stage-rate">${dropoffVisitorToLeadRate.toFixed(1)}%</span>
            </div>
            <div class="dropoff-metric-row">
                <div class="dropoff-stage-info">
                    <span class="dropoff-stage-title">Lead → Trial Drops</span>
                    <span class="dropoff-stage-volume">${dropoffLeadToTrial.toLocaleString()} users dropped out</span>
                </div>
                <span class="dropoff-stage-rate">${dropoffLeadToTrialRate.toFixed(1)}%</span>
            </div>
            <div class="dropoff-metric-row">
                <div class="dropoff-stage-info">
                    <span class="dropoff-stage-title">Trial → Customer Drops</span>
                    <span class="dropoff-stage-volume">${dropoffTrialToCustomer.toLocaleString()} users dropped out</span>
                </div>
                <span class="dropoff-stage-rate">${dropoffTrialToCustomerRate.toFixed(1)}%</span>
            </div>
        `;

        if (charts.dropoffRates) charts.dropoffRates.destroy();
        const ctxDrop = document.getElementById("chart-dropoff-rates").getContext("2d");
        charts.dropoffRates = new Chart(ctxDrop, {
            type: "bar",
            data: {
                labels: ["Visitor-to-Lead Drop-off", "Lead-to-Trial Drop-off", "Trial-to-Customer Drop-off"],
                datasets: [{
                    data: [dropoffVisitorToLeadRate, dropoffLeadToTrialRate, dropoffTrialToCustomerRate],
                    backgroundColor: "rgba(239, 68, 68, 0.65)",
                    borderColor: "#ef4444",
                    borderWidth: 1.5,
                    borderRadius: 6,
                    barThickness: 30
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#94a3b8", font: { family: "Outfit" } } },
                    y: { 
                        min: 0, max: 100, 
                        ticks: { color: "#94a3b8", font: { family: "Outfit" }, callback: v => `${v}%` } 
                    }
                }
            }
        });
    };

    // 10. Data Explorer Table Renderer
    const renderExplorerTable = (optData) => {
        const tbody = document.querySelector("#table-explorer tbody");
        tbody.innerHTML = "";

        const allSessions = optData || FUNNEL_DATA.sessions;

        // Apply filters
        let filtered = allSessions.filter(s => {
            // Filter by stage
            let matchesStage = true;
            if (explorerFilterStage === "Customer") matchesStage = s.purchase_time !== "";
            else if (explorerFilterStage === "Trial") matchesStage = s.trial_time !== "" && s.purchase_time === "";
            else if (explorerFilterStage === "Lead") matchesStage = s.lead_time !== "" && s.trial_time === "";
            else if (explorerFilterStage === "Visitor") matchesStage = s.lead_time === "";

            // Filter by Channel
            const matchesSource = explorerFilterSource === "all" || s.source === explorerFilterSource;

            // Search query
            const matchesQuery = explorerSearchQuery === "" ||
                s.session_id.toLowerCase().includes(explorerSearchQuery) ||
                s.user_id.toLowerCase().includes(explorerSearchQuery) ||
                s.campaign.toLowerCase().includes(explorerSearchQuery);

            return matchesStage && matchesSource && matchesQuery;
        });

        // Set row count
        document.getElementById("explorer-row-count").textContent = filtered.length.toLocaleString();

        // Sort rows
        filtered.sort((a, b) => {
            let valA = a[explorerSortField];
            let valB = b[explorerSortField];

            if (explorerSortAsc) {
                return valA.localeCompare(valB);
            } else {
                return valB.localeCompare(valA);
            }
        });

        // Limit showing to latest 300 rows for browser performance
        const recordsToShow = filtered.slice(0, 300);

        recordsToShow.forEach(s => {
            const tr = document.createElement("tr");

            // Calculate stage badge
            let badgeClass = "visitor";
            let badgeText = "Visitor";
            if (s.purchase_time !== "") { badgeClass = "customer"; badgeText = "Customer"; }
            else if (s.trial_time !== "") { badgeClass = "trial"; badgeText = "Trial"; }
            else if (s.lead_time !== "") { badgeClass = "lead"; badgeText = "Lead"; }

            tr.innerHTML = `
                <td><strong>${s.session_id}</strong></td>
                <td>${s.user_id}</td>
                <td><span class="badge ${badgeClass}">${badgeText}</span> ${s.source}</td>
                <td>${s.campaign}</td>
                <td>${s.device}</td>
                <td>${s.session_start}</td>
                <td>${s.lead_time || "-"}</td>
                <td>${s.trial_time || "-"}</td>
                <td>${s.purchase_time || "-"}</td>
            `;

            tbody.appendChild(tr);
        });
    };

    // 11. Format Utility Helpers
    const formatCurrency = (val) => {
        return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(val);
    };

    const formatShortCurrency = (val) => {
        if (val >= 1e6) {
            return `$${(val / 1e6).toFixed(1)}M`;
        } else if (val >= 1e3) {
            return `$${(val / 1e3).toFixed(1)}K`;
        }
        return formatCurrency(val);
    };

    const formatPercent = (val) => {
        return `${(val * 100).toFixed(2)}%`;
    };

    const getMonthSeries = (start, end) => {
        const months = [];
        let current = new Date(`${start}-02`);
        const endDate = new Date(`${end}-02`);
        while (current <= endDate) {
            months.push(current.toISOString().substring(0, 7));
            current.setMonth(current.getMonth() + 1);
        }
        return months;
    };

    const formatMonthLabel = (monthStr) => {
        const [year, month] = monthStr.split("-");
        const monthsNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        return `${monthsNames[parseInt(month, 10) - 1]} ${year.substring(2)}`;
    };

    // 12. Initial Dashboard Run
    updateDashboard();
});
