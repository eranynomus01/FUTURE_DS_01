// NexusRetention Dashboard Application Logic
document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize global state
    let activeTab = "overview";
    let filters = {
        plan: "all",
        interval: "all",
        region: "all"
    };
    let explorerSearchQuery = "";
    let explorerFilterStatus = "all";
    let explorerFilterPlan = "all";
    let explorerSortField = "signup_date";
    let explorerSortAsc = false;
    
    // Global chart references (for destroying/updating)
    let charts = {
        trends: null,
        regional: null,
        survival: null,
        engagement: null,
        churnReasons: null,
        npsChurn: null,
        planChurn: null,
        billingChurn: null,
        ticketsChurn: null
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
                
                // Redraw charts if tab changes to fix Chart.js width/height rendering issues
                Object.values(charts).forEach(chart => {
                    if (chart) chart.resize();
                });
            }
        });
    });

    // 3. Dynamic Filter Controls
    const filterPlan = document.getElementById("filter-plan");
    const filterInterval = document.getElementById("filter-interval");
    const filterRegion = document.getElementById("filter-region");
    const resetFiltersBtn = document.getElementById("reset-filters");

    const handleFilterChange = () => {
        filters.plan = filterPlan.value;
        filters.interval = filterInterval.value;
        filters.region = filterRegion.value;
        updateDashboard();
    };

    filterPlan.addEventListener("change", handleFilterChange);
    filterInterval.addEventListener("change", handleFilterChange);
    filterRegion.addEventListener("change", handleFilterChange);

    resetFiltersBtn.addEventListener("click", () => {
        filterPlan.value = "all";
        filterInterval.value = "all";
        filterRegion.value = "all";
        filters = { plan: "all", interval: "all", region: "all" };
        updateDashboard();
    });

    // 4. Data Explorer Controls
    const explorerSearch = document.getElementById("explorer-search");
    const expFilterStatus = document.getElementById("explorer-filter-status");
    const expFilterPlan = document.getElementById("explorer-filter-plan");

    explorerSearch.addEventListener("input", (e) => {
        explorerSearchQuery = e.target.value.toLowerCase().trim();
        renderExplorerTable();
    });

    expFilterStatus.addEventListener("change", (e) => {
        explorerFilterStatus = e.target.value;
        renderExplorerTable();
    });

    expFilterPlan.addEventListener("change", (e) => {
        explorerFilterPlan = e.target.value;
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
        const customers = CUSTOMER_DATA.customers;
        const filtered = customers.filter(c => {
            const matchesPlan = filters.plan === "all" || c.plan === filters.plan;
            const matchesInterval = filters.interval === "all" || c.billing_interval === filters.interval;
            const matchesRegion = filters.region === "all" || c.region === filters.region;
            return matchesPlan && matchesInterval && matchesRegion;
        });

        // B. Recompute KPIs
        const kpis = calculateKPIs(filtered);
        updateKPIsUI(kpis);

        // C. Update Overview Tab Charts & Table
        updateTrendsChart(filtered);
        updateRegionalChart(filtered);
        updateSurvivalChart(filtered);
        updateEngagementScatter(filtered);

        // D. Update Churn Factors Tab Charts
        updateChurnReasonsChart(filtered);
        updateNPSChurnChart(filtered);
        updatePlanChurnChart(filtered);
        updateBillingChurnChart(filtered);
        updateTicketsChurnChart(filtered);

        // E. Update Cohorts Tab Heatmap
        renderCohortTable(filtered);

        // F. Update Data Explorer
        renderExplorerTable(filtered);

        // G. Update Strategy / Insights Stats
        updateInsightsUI(kpis);
    };

    // 6. Mathematical & Aggregation Helper Functions
    const calculateKPIs = (data) => {
        let active = 0;
        let churned = 0;
        let activeMRR = 0;
        let sumTotalCharges = 0;
        let sumTenure = 0;
        let sumTenureChurned = 0;
        let sumMonthlyCharge = 0;

        data.forEach(c => {
            sumTotalCharges += c.total_charges;
            sumMonthlyCharge += c.monthly_charges;
            sumTenure += (c.total_charges / c.monthly_charges); // Approx Months Active
            
            if (c.status === "Active") {
                active++;
                activeMRR += c.monthly_charges;
            } else {
                churned++;
                sumTenureChurned += (c.total_charges / c.monthly_charges);
            }
        });

        const total = data.length;
        const churnRate = total > 0 ? (churned / total) : 0;
        const avgTenure = total > 0 ? (sumTenure / total) : 0;
        const avgTenureChurned = churned > 0 ? (sumTenureChurned / churned) : 0;
        const empiricalLtv = total > 0 ? (sumTotalCharges / total) : 0;

        return {
            total: total,
            active: active,
            churned: churned,
            churnRate: churnRate,
            avgTenure: avgTenure,
            avgTenureChurned: avgTenureChurned,
            mrr: activeMRR,
            ltv: empiricalLtv
        };
    };

    const updateKPIsUI = (kpis) => {
        document.querySelector("#kpi-customers .kpi-value").textContent = kpis.active.toLocaleString();
        document.getElementById("kpi-customers-sub").innerHTML = `<i class="fa-solid fa-user-check"></i> ${kpis.total.toLocaleString()} total historical`;
        
        document.querySelector("#kpi-mrr .kpi-value").textContent = formatCurrency(kpis.mrr);
        document.querySelector("#kpi-churn .kpi-value").textContent = formatPercent(kpis.churnRate);
        
        const churnCard = document.querySelector("#kpi-churn");
        const churnTrend = churnCard.querySelector(".trend");
        if (kpis.churnRate > 0.35) {
            churnTrend.className = "trend negative";
            churnTrend.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> Critical Risk`;
        } else if (kpis.churnRate < 0.15) {
            churnTrend.className = "trend positive";
            churnTrend.innerHTML = `<i class="fa-solid fa-arrow-trend-down"></i> Under Control`;
        } else {
            churnTrend.className = "trend neutral";
            churnTrend.innerHTML = `<i class="fa-solid fa-minus"></i> Standard`;
        }

        document.querySelector("#kpi-ltv .kpi-value").textContent = formatCurrency(kpis.ltv);
        document.getElementById("kpi-ltv-sub").innerHTML = `<i class="fa-solid fa-calendar-day"></i> Avg Tenure: ${kpis.avgTenure.toFixed(1)} mo`;
    };

    const updateInsightsUI = (kpis) => {
        document.getElementById("insight-stat-mrr").textContent = formatShortCurrency(kpis.mrr);
        document.getElementById("insight-stat-ltv").textContent = formatCurrency(kpis.ltv);
        
        const churnEl = document.getElementById("insight-stat-churn");
        churnEl.textContent = formatPercent(kpis.churnRate);
        if (kpis.churnRate > 0.35) {
            churnEl.className = "bullet-val text-accent-red";
        } else if (kpis.churnRate < 0.15) {
            churnEl.className = "bullet-val text-accent-green";
        } else {
            churnEl.className = "bullet-val text-accent-amber";
        }
        
        document.getElementById("insight-stat-active").textContent = kpis.active.toLocaleString();
    };

    // 7. Chart Renderers
    const updateTrendsChart = (data) => {
        // We will generate the monthly trends dynamically based on the filtered list of customers
        const months = getMonthSeries("2023-01", "2025-12");
        const activeSeries = [];
        const churnSeries = [];
        const mrrSeries = [];
        const rateSeries = [];

        months.forEach(m => {
            const mStart = new Date(`${m}-01`);
            const [y, mn] = m.split("-").map(Number);
            const mEnd = mn === 12 ? new Date(`${y+1}-01-01`) : new Date(`${y}-${String(mn+1).padStart(2, '0')}-01`);
            
            let activeCount = 0;
            let churnedCount = 0;
            let currentMRR = 0;

            data.forEach(c => {
                const signup = new Date(c.signup_date);
                if (signup < mEnd) {
                    if (c.status === "Active") {
                        activeCount++;
                        currentMRR += c.monthly_charges;
                    } else {
                        const churn = new Date(c.churn_date);
                        if (churn >= mStart) {
                            activeCount++;
                            currentMRR += c.monthly_charges;
                            if (c.churn_date.startsWith(m)) {
                                churnedCount++;
                            }
                        }
                    }
                }
            });

            activeSeries.push(activeCount);
            churnSeries.push(churnedCount);
            mrrSeries.push(currentMRR);
            rateSeries.push(activeCount > 0 ? (churnedCount / activeCount * 100) : 0);
        });

        if (charts.trends) charts.trends.destroy();

        const ctx = document.getElementById("chart-trends").getContext("2d");
        charts.trends = new Chart(ctx, {
            type: "line",
            data: {
                labels: months.map(m => formatMonthLabel(m)),
                datasets: [
                    {
                        label: "Active Subscribers",
                        data: activeSeries,
                        borderColor: "#06b6d4",
                        backgroundColor: "rgba(6, 182, 212, 0.05)",
                        fill: true,
                        yAxisID: "y-subscribers",
                        tension: 0.3,
                        borderWidth: 2.5
                    },
                    {
                        label: "Monthly MRR ($)",
                        data: mrrSeries,
                        borderColor: "#4f46e5",
                        backgroundColor: "transparent",
                        borderDash: [5, 5],
                        fill: false,
                        yAxisID: "y-mrr",
                        tension: 0.3,
                        borderWidth: 2
                    },
                    {
                        label: "Monthly Churned Accounts",
                        data: churnSeries,
                        type: "bar",
                        backgroundColor: "rgba(239, 68, 68, 0.4)",
                        hoverBackgroundColor: "#ef4444",
                        yAxisID: "y-subscribers",
                        barThickness: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#9ca3af", font: { family: "Outfit" } } },
                    tooltip: { mode: "index", intersect: false }
                },
                scales: {
                    x: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#9ca3af", font: { family: "Outfit" } } },
                    "y-subscribers": {
                        type: "linear",
                        position: "left",
                        grid: { color: "rgba(255,255,255,0.05)" },
                        ticks: { color: "#9ca3af", font: { family: "Outfit" } },
                        title: { display: true, text: "Subscriber Count", color: "#9ca3af" }
                    },
                    "y-mrr": {
                        type: "linear",
                        position: "right",
                        grid: { drawOnChartArea: false },
                        ticks: { color: "#9ca3af", font: { family: "Outfit" } },
                        title: { display: true, text: "MRR ($)", color: "#9ca3af" }
                    }
                }
            }
        });
    };

    const updateRegionalChart = (data) => {
        const counts = { East: 0, West: 0, Central: 0, South: 0 };
        data.forEach(c => {
            if (c.status === "Active") counts[c.region]++;
        });

        if (charts.regional) charts.regional.destroy();

        const ctx = document.getElementById("chart-regional").getContext("2d");
        charts.regional = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: Object.keys(counts),
                datasets: [{
                    data: Object.values(counts),
                    backgroundColor: ["#4f46e5", "#06b6d4", "#f59e0b", "#10b981"],
                    borderWidth: 2,
                    borderColor: "#1f2937"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: "#9ca3af", font: { family: "Outfit" }, boxWidth: 12 }
                    }
                }
            }
        });
    };

    const updateSurvivalChart = (data) => {
        // Average survival curve: cohort decay.
        // For ages 0 to 12 months, what % of users reached this tenure.
        const maxMonths = 12;
        const reachedTenure = Array(maxMonths + 1).fill(0);
        let totalReachable = 0;

        data.forEach(c => {
            const tenure = c.total_charges / c.monthly_charges;
            totalReachable++;
            for (let i = 0; i <= maxMonths; i++) {
                if (c.status === "Active" || tenure >= i) {
                    reachedTenure[i]++;
                }
            }
        });

        const survivalRates = reachedTenure.map(count => totalReachable > 0 ? (count / totalReachable * 100) : 0);

        if (charts.survival) charts.survival.destroy();

        const ctx = document.getElementById("chart-survival").getContext("2d");
        charts.survival = new Chart(ctx, {
            type: "line",
            data: {
                labels: Array.from({length: maxMonths + 1}, (_, i) => `Month ${i}`),
                datasets: [{
                    label: "Survival Rate (%)",
                    data: survivalRates,
                    borderColor: "#10b981",
                    backgroundColor: "rgba(16, 185, 129, 0.08)",
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2.5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#9ca3af", font: { family: "Outfit" } } },
                    y: { 
                        grid: { color: "rgba(255,255,255,0.05)" }, 
                        ticks: { color: "#9ca3af", font: { family: "Outfit" } },
                        min: 0,
                        max: 100,
                        title: { display: true, text: "% Retained", color: "#9ca3af" }
                    }
                }
            }
        });
    };

    const updateEngagementScatter = (data) => {
        // Plot active vs churned by support tickets (Y) and monthly usage logins (X).
        // To prevent UI lag with 5000 dots, let's take a sample of 250 active and 250 churned users.
        const activeSample = data.filter(c => c.status === "Active").slice(0, 250);
        const churnedSample = data.filter(c => c.status === "Churned").slice(0, 250);

        const activeDots = activeSample.map(c => ({ x: c.usage_frequency, y: c.support_tickets }));
        const churnedDots = churnedSample.map(c => ({ x: c.usage_frequency, y: c.support_tickets }));

        if (charts.engagement) charts.engagement.destroy();

        const ctx = document.getElementById("chart-engagement").getContext("2d");
        charts.engagement = new Chart(ctx, {
            type: "scatter",
            data: {
                datasets: [
                    {
                        label: "Active Accounts",
                        data: activeDots,
                        backgroundColor: "rgba(16, 185, 129, 0.6)",
                        borderColor: "rgba(16, 185, 129, 0.8)",
                        pointRadius: 5
                    },
                    {
                        label: "Churned Accounts",
                        data: churnedDots,
                        backgroundColor: "rgba(239, 68, 68, 0.6)",
                        borderColor: "rgba(239, 68, 68, 0.8)",
                        pointRadius: 5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#9ca3af", font: { family: "Outfit" } } }
                },
                scales: {
                    x: { 
                        grid: { color: "rgba(255,255,255,0.03)" }, 
                        ticks: { color: "#9ca3af", font: { family: "Outfit" } },
                        title: { display: true, text: "Usage Logins (per Month)", color: "#9ca3af" }
                    },
                    y: { 
                        grid: { color: "rgba(255,255,255,0.05)" }, 
                        ticks: { color: "#9ca3af", font: { family: "Outfit" } },
                        title: { display: true, text: "Support Ticket Count", color: "#9ca3af" }
                    }
                }
            }
        });
    };

    const updateChurnReasonsChart = (data) => {
        const churned = data.filter(c => c.status === "Churned");
        const reasons = {};
        churned.forEach(c => {
            const reason = c.churn_reason || "Unknown";
            reasons[reason] = (reasons[reason] || 0) + 1;
        });

        // Sort reasons descending
        const sortedReasons = Object.entries(reasons)
            .sort((a,b) => b[1] - a[1]);

        if (charts.churnReasons) charts.churnReasons.destroy();

        const ctx = document.getElementById("chart-churn-reasons").getContext("2d");
        charts.churnReasons = new Chart(ctx, {
            type: "bar",
            data: {
                labels: sortedReasons.map(r => r[0]),
                datasets: [{
                    label: "Churn Count",
                    data: sortedReasons.map(r => r[1]),
                    backgroundColor: "rgba(239, 68, 68, 0.65)",
                    borderColor: "#ef4444",
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "#9ca3af", font: { family: "Outfit" } } },
                    y: { grid: { display: false }, ticks: { color: "#9ca3af", font: { family: "Outfit" } } }
                }
            }
        });
    };

    const updateNPSChurnChart = (data) => {
        // NPS Category: Promoter (9-10), Passive (7-8), Detractor (1-6), No Response (null)
        const groups = {
            "Promoters (9-10)": { total: 0, churned: 0 },
            "Passives (7-8)": { total: 0, churned: 0 },
            "Detractors (1-6)": { total: 0, churned: 0 },
            "No Response": { total: 0, churned: 0 }
        };

        data.forEach(c => {
            let cat = "No Response";
            if (c.nps_score !== null) {
                if (c.nps_score >= 9) cat = "Promoters (9-10)";
                else if (c.nps_score >= 7) cat = "Passives (7-8)";
                else cat = "Detractors (1-6)";
            }
            groups[cat].total++;
            if (c.status === "Churned") groups[cat].churned++;
        });

        const labels = Object.keys(groups);
        const rates = labels.map(l => groups[l].total > 0 ? (groups[l].churned / groups[l].total * 100) : 0);

        if (charts.npsChurn) charts.npsChurn.destroy();

        const ctx = document.getElementById("chart-nps-churn").getContext("2d");
        charts.npsChurn = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    data: rates,
                    backgroundColor: ["#10b981", "#f59e0b", "#ef4444", "#6b7280"],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#9ca3af", font: { family: "Outfit" } } },
                    y: { 
                        min: 0, max: 100, 
                        ticks: { color: "#9ca3af", font: { family: "Outfit" }, callback: v => `${v}%` } 
                    }
                }
            }
        });
    };

    const updatePlanChurnChart = (data) => {
        const groups = {
            "Basic": { total: 0, churned: 0 },
            "Pro": { total: 0, churned: 0 },
            "Enterprise": { total: 0, churned: 0 }
        };
        data.forEach(c => {
            if (groups[c.plan]) {
                groups[c.plan].total++;
                if (c.status === "Churned") groups[c.plan].churned++;
            }
        });

        const labels = Object.keys(groups);
        const rates = labels.map(l => groups[l].total > 0 ? (groups[l].churned / groups[l].total * 100) : 0);

        if (charts.planChurn) charts.planChurn.destroy();

        const ctx = document.getElementById("chart-plan-churn").getContext("2d");
        charts.planChurn = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    data: rates,
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
                    x: { ticks: { color: "#9ca3af", font: { family: "Outfit" } } },
                    y: { min: 0, max: 100, ticks: { color: "#9ca3af", font: { family: "Outfit" }, callback: v => `${v}%` } }
                }
            }
        });
    };

    const updateBillingChurnChart = (data) => {
        const groups = {
            "Monthly": { total: 0, churned: 0 },
            "Annually": { total: 0, churned: 0 }
        };
        data.forEach(c => {
            const intv = c.billing_interval;
            if (groups[intv]) {
                groups[intv].total++;
                if (c.status === "Churned") groups[intv].churned++;
            }
        });

        const labels = Object.keys(groups);
        const rates = labels.map(l => groups[l].total > 0 ? (groups[l].churned / groups[l].total * 100) : 0);

        if (charts.billingChurn) charts.billingChurn.destroy();

        const ctx = document.getElementById("chart-billing-churn").getContext("2d");
        charts.billingChurn = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    data: rates,
                    backgroundColor: ["#f87171", "#34d399"],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#9ca3af", font: { family: "Outfit" } } },
                    y: { min: 0, max: 100, ticks: { color: "#9ca3af", font: { family: "Outfit" }, callback: v => `${v}%` } }
                }
            }
        });
    };

    const updateTicketsChurnChart = (data) => {
        const groups = {
            "0-2 tickets": { total: 0, churned: 0 },
            "3-5 tickets": { total: 0, churned: 0 },
            "6-9 tickets": { total: 0, churned: 0 },
            "10+ tickets": { total: 0, churned: 0 }
        };

        data.forEach(c => {
            let band = "10+ tickets";
            if (c.support_tickets <= 2) band = "0-2 tickets";
            else if (c.support_tickets <= 5) band = "3-5 tickets";
            else if (c.support_tickets <= 9) band = "6-9 tickets";
            
            groups[band].total++;
            if (c.status === "Churned") groups[band].churned++;
        });

        const labels = Object.keys(groups);
        const rates = labels.map(l => groups[l].total > 0 ? (groups[l].churned / groups[l].total * 100) : 0);

        if (charts.ticketsChurn) charts.ticketsChurn.destroy();

        const ctx = document.getElementById("chart-tickets-churn").getContext("2d");
        charts.ticketsChurn = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    data: rates,
                    backgroundColor: "rgba(245, 158, 11, 0.75)",
                    borderColor: "#f59e0b",
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#9ca3af", font: { family: "Outfit" } } },
                    y: { min: 0, max: 100, ticks: { color: "#9ca3af", font: { family: "Outfit" }, callback: v => `${v}%` } }
                }
            }
        });
    };

    // 8. Cohorts Heatmap Grid Renderer
    const renderCohortTable = (data) => {
        const tbody = document.querySelector("#table-cohort tbody");
        tbody.innerHTML = "";

        // Group data by signup month
        const cohorts = {};
        data.forEach(c => {
            const month = c.signup_date.substring(0, 7);
            if (!cohorts[month]) cohorts[month] = [];
            cohorts[month].push(c);
        });

        const sortedMonths = Object.keys(cohorts).sort();

        sortedMonths.forEach(month => {
            const cUsers = cohorts[month];
            const size = cUsers.length;

            const tr = document.createElement("tr");
            
            // Cohort Label
            const tdMonth = document.createElement("td");
            tdMonth.textContent = formatMonthLabel(month);
            tr.appendChild(tdMonth);

            // Cohort Size
            const tdSize = document.createElement("td");
            tdSize.textContent = size.toLocaleString();
            tr.appendChild(tdSize);

            // M0 to M12 rates
            for (let age = 0; age <= 12; age++) {
                const tdRate = document.createElement("td");
                
                // Filter out users who haven't existed long enough yet
                // E.g., if signup is Dec 2025, and dataset end is Dec 2025, age > 0 is not reachable.
                const signupDate = new Date(`${month}-01`);
                const datasetEnd = new Date("2025-12-31");
                const monthsReachable = Math.round((datasetEnd - signupDate) / (30.4 * 24 * 60 * 60 * 1000));
                
                if (age > monthsReachable) {
                    tdRate.textContent = "-";
                    tdRate.className = "level-empty";
                } else {
                    const retained = cUsers.filter(c => {
                        const tenure = c.total_charges / c.monthly_charges;
                        return c.status === "Active" || tenure >= age;
                    }).length;
                    
                    const rate = size > 0 ? (retained / size) : 0;
                    tdRate.textContent = `${(rate * 100).toFixed(0)}%`;
                    
                    // Assign heatmap colors class
                    if (rate >= 0.90) tdRate.className = "level-100";
                    else if (rate >= 0.70) tdRate.className = "level-75";
                    else if (rate >= 0.50) tdRate.className = "level-50";
                    else if (rate >= 0.30) tdRate.className = "level-25";
                    else tdRate.className = "level-0";
                }
                tr.appendChild(tdRate);
            }
            tbody.appendChild(tr);
        });
    };

    // 9. Data Explorer Table Renderer
    const renderExplorerTable = (optData) => {
        const tbody = document.querySelector("#table-explorer tbody");
        tbody.innerHTML = "";

        const allCustomers = optData || CUSTOMER_DATA.customers;

        // Apply Explorer-specific tab filters (Status, Plan, Search query)
        let filtered = allCustomers.filter(c => {
            const matchesStatus = explorerFilterStatus === "all" || c.status === explorerFilterStatus;
            const matchesPlan = explorerFilterPlan === "all" || c.plan === explorerFilterPlan;
            
            const matchQuery = explorerSearchQuery === "" || 
                c.customer_id.toLowerCase().includes(explorerSearchQuery) ||
                c.customer_name.toLowerCase().includes(explorerSearchQuery) ||
                c.region.toLowerCase().includes(explorerSearchQuery) ||
                (c.churn_reason && c.churn_reason.toLowerCase().includes(explorerSearchQuery));
                
            return matchesStatus && matchesPlan && matchQuery;
        });

        // Set row count
        document.getElementById("explorer-row-count").textContent = filtered.length.toLocaleString();

        // Apply Sorting
        filtered.sort((a, b) => {
            let valA = a[explorerSortField];
            let valB = b[explorerSortField];

            if (typeof valA === "string") {
                return explorerSortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else {
                // Numbers/floats
                if (valA === null) return explorerSortAsc ? 1 : -1;
                if (valB === null) return explorerSortAsc ? -1 : 1;
                return explorerSortAsc ? valA - valB : valB - valA;
            }
        });

        // Limit showing to latest 300 records for browser performance
        const recordsToShow = filtered.slice(0, 300);

        recordsToShow.forEach(c => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td><strong>${c.customer_id}</strong></td>
                <td>${c.customer_name}</td>
                <td>${c.region}</td>
                <td>${c.signup_date}</td>
                <td>${c.plan}</td>
                <td>${c.billing_interval}</td>
                <td><span class="badge ${c.status.toLowerCase()}">${c.status}</span></td>
                <td class="num-col">${formatCurrency(c.monthly_charges)}</td>
                <td class="num-col">${formatCurrency(c.total_charges)}</td>
                <td class="num-col">${c.support_tickets}</td>
                <td class="num-col">${c.usage_frequency}</td>
                <td class="num-col">${c.nps_score !== null ? c.nps_score : "-"}</td>
                <td><span class="text-secondary" style="font-size: 0.8rem;">${c.churn_reason || "-"}</span></td>
            `;

            tbody.appendChild(tr);
        });
    };

    // 10. Format and Date Utility Helpers
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
        let current = new Date(`${start}-02`); // Mid month to prevent TZ issues
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

    // 11. Initial Dashboard Run
    updateDashboard();
});
