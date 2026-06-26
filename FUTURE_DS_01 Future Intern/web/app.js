// NexusRetail Dashboard Application Logic
document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize global state
    let activeTab = "overview";
    let filters = {
        year: "all",
        region: "all",
        category: "all"
    };
    let explorerSearchQuery = "";
    let explorerSortField = "order_date";
    let explorerSortAsc = false;
    
    // Global chart references (for destroying/updating)
    let charts = {
        trends: null,
        regional: null,
        categories: null,
        segments: null,
        subcategories: null,
        states: null
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
                
                // Redraw specific charts if tab changes (to fix Chart.js sizing glitches)
                if (tabId === "products" && charts.subcategories) {
                    charts.subcategories.resize();
                } else if (tabId === "regions" && charts.states) {
                    charts.states.resize();
                }
            }
        });
    });

    // 3. Dynamic Filter Controls
    const filterYear = document.getElementById("filter-year");
    const filterRegion = document.getElementById("filter-region");
    const filterCategory = document.getElementById("filter-category");
    const resetFiltersBtn = document.getElementById("reset-filters");

    const handleFilterChange = () => {
        filters.year = filterYear.value;
        filters.region = filterRegion.value;
        filters.category = filterCategory.value;
        updateDashboard();
    };

    filterYear.addEventListener("change", handleFilterChange);
    filterRegion.addEventListener("change", handleFilterChange);
    filterCategory.addEventListener("change", handleFilterChange);

    resetFiltersBtn.addEventListener("click", () => {
        filterYear.value = "all";
        filterRegion.value = "all";
        filterCategory.value = "all";
        filters = { year: "all", region: "all", category: "all" };
        updateDashboard();
    });

    // 4. Data Explorer Controls
    const explorerSearch = document.getElementById("explorer-search");
    explorerSearch.addEventListener("input", (e) => {
        explorerSearchQuery = e.target.value.toLowerCase().strip ? e.target.value.toLowerCase().strip() : e.target.value.toLowerCase();
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
        // A. Filter Raw Dataset
        const transactions = SALES_DATA.transactions;
        const filtered = transactions.filter(tx => {
            const txYear = new Date(tx.order_date).getFullYear().toString();
            const matchesYear = filters.year === "all" || txYear === filters.year;
            const matchesRegion = filters.region === "all" || tx.region === filters.region;
            const matchesCategory = filters.category === "all" || tx.category === filters.category;
            return matchesYear && matchesRegion && matchesCategory;
        });

        // B. Recompute KPIs
        const kpis = calculateKPIs(filtered);
        updateKPIsUI(kpis);

        // C. Update Overview Tab Charts
        updateTrendsChart(filtered);
        updateRegionalChart(filtered);
        updateCategoriesChart(filtered);
        updateSegmentsChart(filtered);

        // D. Update Products Tab
        updateProductsTab(filtered);

        // E. Update Regions Tab
        updateRegionsTab(filtered);

        // F. Update Data Explorer
        renderExplorerTable(filtered);

        // G. Update Strategy / Insights Stats
        updateInsightsUI(kpis);
    };

    // 6. Mathematical Helper Functions
    const calculateKPIs = (data) => {
        let sales = 0;
        let profit = 0;
        const orderIds = new Set();
        
        data.forEach(tx => {
            sales += tx.sales;
            profit += tx.profit;
            orderIds.add(tx.order_id);
        });

        const margin = sales > 0 ? profit / sales : 0;
        return {
            sales: sales,
            profit: profit,
            margin: margin,
            orders: orderIds.size
        };
    };

    const updateKPIsUI = (kpis) => {
        document.querySelector("#kpi-sales .kpi-value").textContent = formatCurrency(kpis.sales);
        document.querySelector("#kpi-profit .kpi-value").textContent = formatCurrency(kpis.profit);
        document.querySelector("#kpi-margin .kpi-value").textContent = formatPercent(kpis.margin);
        document.querySelector("#kpi-orders .kpi-value").textContent = kpis.orders.toLocaleString();
        
        // Dynamic KPI footer trend adjustment (mock variations based on filters for realism)
        const profitCard = document.querySelector("#kpi-profit");
        const profitTrend = profitCard.querySelector(".trend");
        if (kpis.margin < 0.15) {
            profitTrend.className = "trend negative";
            profitTrend.innerHTML = '<i class="fa-solid fa-arrow-trend-down"></i> Underperforming';
        } else if (kpis.margin > 0.28) {
            profitTrend.className = "trend positive";
            profitTrend.innerHTML = '<i class="fa-solid fa-arrow-trend-up"></i> Exceptional';
        } else {
            profitTrend.className = "trend positive";
            profitTrend.innerHTML = '<i class="fa-solid fa-arrow-trend-up"></i> Reconciled';
        }
    };

    const updateInsightsUI = (kpis) => {
        document.getElementById("insight-stat-sales").textContent = formatShortCurrency(kpis.sales);
        document.getElementById("insight-stat-profit").textContent = formatShortCurrency(kpis.profit);
        
        const marginEl = document.getElementById("insight-stat-margin");
        marginEl.textContent = formatPercent(kpis.margin);
        if (kpis.margin < 0.15) {
            marginEl.className = "bullet-val text-accent-red";
        } else if (kpis.margin < 0.23) {
            marginEl.className = "bullet-val text-accent-amber";
        } else {
            marginEl.className = "bullet-val text-accent-green";
        }
        
        document.getElementById("insight-stat-orders").textContent = kpis.orders.toLocaleString();
    };

    // 7. Chart Rendering Logics
    const getChartStyles = () => {
        return {
            fontFamily: "'Outfit', sans-serif",
            textSecondary: "#94a3b8",
            gridColor: "rgba(255, 255, 255, 0.05)",
            accentCyan: "#06b6d4",
            accentGreen: "#10b981",
            accentAmber: "#f59e0b",
            accentPurple: "#8b5cf6",
            accentPink: "#ec4899",
            colorsList: ["#06b6d4", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#ef4444", "#3b82f6"]
        };
    };

    const updateTrendsChart = (data) => {
        // Group by YearMonth
        const monthlyMap = {};
        data.forEach(tx => {
            const dateObj = new Date(tx.order_date);
            const ym = dateObj.getFullYear() + "-" + String(dateObj.getMonth() + 1).padStart(2, "0");
            if (!monthlyMap[ym]) {
                monthlyMap[ym] = { sales: 0, profit: 0 };
            }
            monthlyMap[ym].sales += tx.sales;
            monthlyMap[ym].profit += tx.profit;
        });

        const sortedMonths = Object.keys(monthlyMap).sort();
        const salesData = sortedMonths.map(m => monthlyMap[m].sales);
        const profitData = sortedMonths.map(m => monthlyMap[m].profit);
        const marginData = sortedMonths.map(m => monthlyMap[m].sales > 0 ? (monthlyMap[m].profit / monthlyMap[m].sales) * 100 : 0);

        const styles = getChartStyles();
        const ctx = document.getElementById("chart-trends").getContext("2d");

        if (charts.trends) {
            charts.trends.destroy();
        }

        charts.trends = new Chart(ctx, {
            type: "line",
            data: {
                labels: sortedMonths.map(m => {
                    const [y, mm] = m.split("-");
                    const date = new Date(parseInt(y), parseInt(mm) - 1, 1);
                    return date.toLocaleString("en-US", { month: "short", year: "2-digit" });
                }),
                datasets: [
                    {
                        label: "Revenue ($)",
                        data: salesData,
                        borderColor: styles.accentCyan,
                        backgroundColor: "rgba(6, 182, 212, 0.05)",
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        yAxisID: "y-sales"
                    },
                    {
                        label: "Net Profit ($)",
                        data: profitData,
                        borderColor: styles.accentGreen,
                        backgroundColor: "transparent",
                        borderWidth: 2,
                        tension: 0.35,
                        borderDash: [4, 4],
                        yAxisID: "y-sales"
                    },
                    {
                        label: "Profit Margin (%)",
                        data: marginData,
                        borderColor: styles.accentAmber,
                        backgroundColor: "transparent",
                        borderWidth: 1.5,
                        pointRadius: 1,
                        tension: 0.3,
                        yAxisID: "y-margin"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                        labels: { color: styles.textSecondary, font: { family: styles.fontFamily, size: 12 } }
                    },
                    tooltip: {
                        padding: 12,
                        backgroundColor: "#1e293b",
                        titleColor: "#fff",
                        bodyColor: "#cbd5e1",
                        borderColor: "rgba(255,255,255,0.1)",
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: { color: styles.gridColor },
                        ticks: { color: styles.textSecondary, font: { family: styles.fontFamily } }
                    },
                    "y-sales": {
                        type: "linear",
                        position: "left",
                        grid: { color: styles.gridColor },
                        ticks: {
                            color: styles.textSecondary,
                            font: { family: styles.fontFamily },
                            callback: value => "$" + formatNumberShort(value)
                        }
                    },
                    "y-margin": {
                        type: "linear",
                        position: "right",
                        grid: { drawOnChartArea: false },
                        ticks: {
                            color: styles.textSecondary,
                            font: { family: styles.fontFamily },
                            callback: value => value.toFixed(0) + "%"
                        },
                        min: -10,
                        max: 60
                    }
                }
            }
        });
    };

    const updateRegionalChart = (data) => {
        // Group by Region
        const regMap = {};
        data.forEach(tx => {
            regMap[tx.region] = (regMap[tx.region] || 0) + tx.sales;
        });

        const labels = Object.keys(regMap);
        const values = Object.values(regMap);

        const styles = getChartStyles();
        const ctx = document.getElementById("chart-regional").getContext("2d");

        if (charts.regional) {
            charts.regional.destroy();
        }

        charts.regional = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [styles.accentCyan, styles.accentGreen, styles.accentAmber, styles.accentPurple],
                    borderColor: "#0f172a",
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: styles.textSecondary, padding: 15, font: { family: styles.fontFamily, size: 11 } }
                    },
                    tooltip: {
                        callbacks: {
                            label: context => {
                                const val = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = ((val / total) * 100).toFixed(1);
                                return `${context.label}: $${val.toLocaleString(undefined, {maximumFractionDigits:0})} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    };

    const updateCategoriesChart = (data) => {
        // Group by Category
        const catMap = {};
        data.forEach(tx => {
            if (!catMap[tx.category]) {
                catMap[tx.category] = { sales: 0, profit: 0 };
            }
            catMap[tx.category].sales += tx.sales;
            catMap[tx.category].profit += tx.profit;
        });

        const labels = Object.keys(catMap);
        const sales = labels.map(c => catMap[c].sales);
        const profits = labels.map(c => catMap[c].profit);

        const styles = getChartStyles();
        const ctx = document.getElementById("chart-categories").getContext("2d");

        if (charts.categories) {
            charts.categories.destroy();
        }

        charts.categories = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Sales ($)",
                        data: sales,
                        backgroundColor: "rgba(6, 182, 212, 0.75)",
                        borderColor: styles.accentCyan,
                        borderWidth: 1,
                        borderRadius: 6
                    },
                    {
                        label: "Profit ($)",
                        data: profits,
                        backgroundColor: "rgba(16, 185, 129, 0.75)",
                        borderColor: styles.accentGreen,
                        borderWidth: 1,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                        labels: { color: styles.textSecondary, font: { family: styles.fontFamily } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: styles.gridColor },
                        ticks: { color: styles.textSecondary, font: { family: styles.fontFamily } }
                    },
                    y: {
                        grid: { color: styles.gridColor },
                        ticks: {
                            color: styles.textSecondary,
                            font: { family: styles.fontFamily },
                            callback: value => "$" + formatNumberShort(value)
                        }
                    }
                }
            }
        });
    };

    const updateSegmentsChart = (data) => {
        const segMap = {};
        data.forEach(tx => {
            segMap[tx.segment] = (segMap[tx.segment] || 0) + tx.sales;
        });

        const labels = Object.keys(segMap);
        const values = Object.values(segMap);

        const styles = getChartStyles();
        const ctx = document.getElementById("chart-segments").getContext("2d");

        if (charts.segments) {
            charts.segments.destroy();
        }

        charts.segments = new Chart(ctx, {
            type: "pie",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [styles.accentCyan, styles.accentPurple, styles.accentAmber],
                    borderColor: "#0f172a",
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: styles.textSecondary, padding: 12, font: { family: styles.fontFamily, size: 11 } }
                    }
                }
            }
        });
    };

    // 8. Products Tab Logic
    const updateProductsTab = (data) => {
        // A. Populate Top Products Table
        // Aggregate by Product Name
        const prodMap = {};
        data.forEach(tx => {
            if (!prodMap[tx.product_name]) {
                prodMap[tx.product_name] = {
                    name: tx.product_name,
                    category: tx.category,
                    sub_category: tx.sub_category,
                    quantity: 0,
                    sales: 0,
                    profit: 0
                };
            }
            prodMap[tx.product_name].quantity += tx.quantity;
            prodMap[tx.product_name].sales += tx.sales;
            prodMap[tx.product_name].profit += tx.profit;
        });

        const sortedProds = Object.values(prodMap)
            .sort((a, b) => b.sales - a.sales)
            .slice(0, 15);

        const tbody = document.querySelector("#table-top-products tbody");
        tbody.innerHTML = "";
        
        sortedProds.forEach(p => {
            const margin = p.sales > 0 ? (p.profit / p.sales) : 0;
            const tr = document.createElement("tr");
            
            // Choose margin badge color
            let badgeClass = "badge-green";
            if (margin < 0.10) badgeClass = "badge-red";
            else if (margin < 0.20) badgeClass = "badge-amber";

            tr.innerHTML = `
                <td title="${p.name}">${truncateText(p.name, 45)}</td>
                <td><span class="badge badge-cyan">${p.category}</span></td>
                <td>${p.sub_category}</td>
                <td class="num-col">${p.quantity.toLocaleString()}</td>
                <td class="num-col">${formatCurrency(p.sales)}</td>
                <td class="num-col ${p.profit < 0 ? 'text-accent-red' : ''}">${formatCurrency(p.profit)}</td>
                <td class="num-col"><span class="badge ${badgeClass}">${formatPercent(margin)}</span></td>
            `;
            tbody.appendChild(tr);
        });

        // B. Populate Sub-Category Chart
        const subcatMap = {};
        data.forEach(tx => {
            if (!subcatMap[tx.sub_category]) {
                subcatMap[tx.sub_category] = { sales: 0, profit: 0 };
            }
            subcatMap[tx.sub_category].sales += tx.sales;
            subcatMap[tx.sub_category].profit += tx.profit;
        });

        const subcats = Object.keys(subcatMap).sort((a,b) => subcatMap[b].sales - subcatMap[a].sales);
        const margins = subcats.map(s => subcatMap[s].sales > 0 ? (subcatMap[s].profit / subcatMap[s].sales) * 100 : 0);
        const sales = subcats.map(s => subcatMap[s].sales);

        const styles = getChartStyles();
        const ctx = document.getElementById("chart-subcategories").getContext("2d");

        if (charts.subcategories) {
            charts.subcategories.destroy();
        }

        charts.subcategories = new Chart(ctx, {
            type: "bar",
            data: {
                labels: subcats,
                datasets: [
                    {
                        label: "Sales Vol ($)",
                        data: sales,
                        backgroundColor: "rgba(6, 182, 212, 0.4)",
                        borderColor: styles.accentCyan,
                        borderWidth: 1.5,
                        borderRadius: 4,
                        yAxisID: "y-sales"
                    },
                    {
                        label: "Net Margin (%)",
                        data: margins,
                        type: "line",
                        borderColor: styles.accentGreen,
                        backgroundColor: "transparent",
                        borderWidth: 2,
                        pointBackgroundColor: styles.accentGreen,
                        yAxisID: "y-margin"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                        labels: { color: styles.textSecondary, font: { family: styles.fontFamily } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: styles.gridColor },
                        ticks: { color: styles.textSecondary, font: { family: styles.fontFamily, size: 10 } }
                    },
                    "y-sales": {
                        type: "linear",
                        position: "left",
                        grid: { color: styles.gridColor },
                        ticks: {
                            color: styles.textSecondary,
                            font: { family: styles.fontFamily },
                            callback: value => "$" + formatNumberShort(value)
                        }
                    },
                    "y-margin": {
                        type: "linear",
                        position: "right",
                        grid: { drawOnChartArea: false },
                        ticks: {
                            color: styles.textSecondary,
                            font: { family: styles.fontFamily },
                            callback: value => value.toFixed(0) + "%"
                        }
                    }
                }
            }
        });
    };

    // 9. Regions & Segments Tab Logic
    const updateRegionsTab = (data) => {
        // A. Dynamic Regional Card Summaries
        const regMap = {};
        data.forEach(tx => {
            if (!regMap[tx.region]) {
                regMap[tx.region] = { sales: 0, profit: 0, orders: new Set(), qty: 0 };
            }
            regMap[tx.region].sales += tx.sales;
            regMap[tx.region].profit += tx.profit;
            regMap[tx.region].orders.add(tx.order_id);
            regMap[tx.region].qty += tx.quantity;
        });

        const regContainer = document.getElementById("regional-metrics-container");
        regContainer.innerHTML = "";

        const allRegionsList = ["East", "West", "Central", "South"];
        allRegionsList.forEach(r => {
            const stats = regMap[r] || { sales: 0, profit: 0, orders: new Set(), qty: 0 };
            const salesVal = stats.sales;
            const profitVal = stats.profit;
            const marginVal = salesVal > 0 ? profitVal / salesVal : 0;
            
            let badgeClass = "badge-green";
            if (marginVal < 0.15) badgeClass = "badge-red";
            else if (marginVal < 0.23) badgeClass = "badge-amber";

            const card = document.createElement("div");
            card.className = "regional-detail-card";
            card.innerHTML = `
                <div class="reg-card-header">
                    <span class="reg-name"><i class="fa-solid fa-map-pin text-accent-cyan"></i> ${r} Region</span>
                    <span class="badge ${badgeClass}">${formatPercent(marginVal)} Margin</span>
                </div>
                <div class="reg-stats-row">
                    <div class="stat-box">
                        <span class="stat-val">${formatCurrency(salesVal)}</span>
                        <span class="stat-lbl">Revenue</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-val ${profitVal < 0 ? 'text-accent-red' : ''}">${formatCurrency(profitVal)}</span>
                        <span class="stat-lbl">Profit</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-val">${stats.orders.size}</span>
                        <span class="stat-lbl">Orders</span>
                    </div>
                </div>
            `;
            regContainer.appendChild(card);
        });

        // B. Top Regional Markets (States & Cities)
        const stateMap = {};
        data.forEach(tx => {
            const key = tx.state + ", " + tx.city;
            if (!stateMap[key]) {
                stateMap[key] = { sales: 0, profit: 0 };
            }
            stateMap[key].sales += tx.sales;
            stateMap[key].profit += tx.profit;
        });

        const sortedStates = Object.keys(stateMap)
            .sort((a,b) => stateMap[b].sales - stateMap[a].sales)
            .slice(0, 10);
            
        const stateLabels = sortedStates.map(s => s);
        const stateSales = sortedStates.map(s => stateMap[s].sales);
        const stateProfits = sortedStates.map(s => stateMap[s].profit);

        const styles = getChartStyles();
        const ctx = document.getElementById("chart-top-states").getContext("2d");

        if (charts.states) {
            charts.states.destroy();
        }

        charts.states = new Chart(ctx, {
            type: "bar",
            data: {
                labels: stateLabels.map(lbl => truncateText(lbl, 16)),
                datasets: [
                    {
                        label: "Sales ($)",
                        data: stateSales,
                        backgroundColor: "rgba(6, 182, 212, 0.8)",
                        borderRadius: 4
                    },
                    {
                        label: "Profit ($)",
                        data: stateProfits,
                        backgroundColor: "rgba(16, 185, 129, 0.8)",
                        borderRadius: 4
                    }
                ]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                        labels: { color: styles.textSecondary, font: { family: styles.fontFamily } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: styles.gridColor },
                        ticks: {
                            color: styles.textSecondary,
                            font: { family: styles.fontFamily },
                            callback: value => "$" + formatNumberShort(value)
                        }
                    },
                    y: {
                        grid: { color: styles.gridColor },
                        ticks: { color: styles.textSecondary, font: { family: styles.fontFamily, size: 9.5 } }
                    }
                }
            }
        });
    };

    // 10. Data Explorer Table Populate, Filter, Sort and Search
    let cachedFilteredData = [];

    const renderExplorerTable = (dataToRender = null) => {
        if (dataToRender !== null) {
            cachedFilteredData = dataToRender;
        }

        let workingData = [...cachedFilteredData];

        // Apply Explorer Search
        if (explorerSearchQuery) {
            workingData = workingData.filter(tx => {
                return (
                    tx.order_id.toLowerCase().includes(explorerSearchQuery) ||
                    tx.customer_name.toLowerCase().includes(explorerSearchQuery) ||
                    tx.product_name.toLowerCase().includes(explorerSearchQuery) ||
                    tx.state.toLowerCase().includes(explorerSearchQuery) ||
                    tx.city.toLowerCase().includes(explorerSearchQuery) ||
                    tx.category.toLowerCase().includes(explorerSearchQuery) ||
                    tx.sub_category.toLowerCase().includes(explorerSearchQuery)
                );
            });
        }

        // Apply Explorer Sort
        workingData.sort((a, b) => {
            let valA = a[explorerSortField];
            let valB = b[explorerSortField];
            
            // Treat strings and numbers appropriately
            if (typeof valA === "string") {
                valA = valA.toLowerCase();
                valB = valB.toLowerCase();
            }

            if (valA < valB) return explorerSortAsc ? -1 : 1;
            if (valA > valB) return explorerSortAsc ? 1 : -1;
            return 0;
        });

        // Set row count status
        document.getElementById("explorer-row-count").textContent = workingData.length.toLocaleString();

        // Populate table (limit display to 200 rows for scrolling speed, paging could be added if requested)
        const tbody = document.querySelector("#table-explorer tbody");
        tbody.innerHTML = "";

        const sliceToRender = workingData.slice(0, 150);
        if (sliceToRender.length === 0) {
            tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--text-muted); padding: 40px;">No matching records found</td></tr>`;
            return;
        }

        sliceToRender.forEach(tx => {
            const tr = document.createElement("tr");
            
            let badgeClass = "badge-green";
            if (tx.profit < 0) badgeClass = "badge-red";
            else if (tx.profit / tx.sales < 0.15) badgeClass = "badge-amber";

            tr.innerHTML = `
                <td><strong class="text-accent-cyan">${tx.order_id}</strong></td>
                <td>${tx.order_date}</td>
                <td>${tx.customer_name}</td>
                <td><small>${tx.segment}</small></td>
                <td><small>${tx.city}, ${tx.state}</small></td>
                <td><span class="badge badge-cyan">${tx.category}</span></td>
                <td title="${tx.product_name}">${truncateText(tx.product_name, 25)}</td>
                <td class="num-col">${formatCurrency(tx.sales)}</td>
                <td class="num-col">${tx.quantity}</td>
                <td class="num-col">${tx.discount > 0 ? (tx.discount * 100).toFixed(0) + "%" : "-"}</td>
                <td class="num-col"><span class="badge ${badgeClass}">${formatCurrency(tx.profit)}</span></td>
            `;
            tbody.appendChild(tr);
        });
    };

    // 11. String formatting helper functions
    const formatCurrency = (val) => {
        return "$" + val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };

    const formatPercent = (val) => {
        return (val * 100).toFixed(1) + "%";
    };

    const formatShortCurrency = (val) => {
        if (val >= 1e6) {
            return "$" + (val / 1e6).toFixed(2) + "M";
        } else if (val >= 1e3) {
            return "$" + (val / 1e3).toFixed(1) + "K";
        }
        return "$" + val.toFixed(2);
    };

    const formatNumberShort = (val) => {
        if (val >= 1e6) {
            return (val / 1e6).toFixed(1) + "M";
        } else if (val >= 1e3) {
            return (val / 1e3).toFixed(0) + "K";
        }
        return val.toString();
    };

    const truncateText = (text, maxLength) => {
        if (!text) return "";
        return text.length > maxLength ? text.slice(0, maxLength - 3) + "..." : text;
    };

    // 12. Kickoff initial render
    updateDashboard();
});
