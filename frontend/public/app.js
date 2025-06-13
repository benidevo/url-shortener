// Utility functions
const Utils = {
    createErrorElement(title, message) {
        return `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex">
                    <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-800">${title}</h3>
                        <p class="mt-1 text-sm text-red-700">${message}</p>
                    </div>
                </div>
            </div>
        `;
    },

    createMetricCard(title, value, color, iconPath) {
        return `
            <div class="bg-white border rounded-lg p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">${title}</p>
                        <p class="text-2xl font-bold text-${color}-600">${value}</p>
                    </div>
                    <svg class="w-8 h-8 text-${color}-200" fill="currentColor" viewBox="0 0 20 20">
                        ${iconPath}
                    </svg>
                </div>
            </div>
        `;
    }
};

// Alpine.js app data
function app() {
    return {
        currentPage: 'shortener',
        showResult: false,

        submitAnalytics(event) {
            event.preventDefault();

            const input = document.getElementById('analytics-input');
            let shortLink = input.value.trim();

            // Extract short code from full URL if needed
            if (shortLink.includes('/')) {
                shortLink = shortLink.split('/').pop();
            }

            // Show loading indicator
            document.getElementById('analytics-loading').style.display = 'block';

            // Make the HTMX request
            htmx.ajax('GET', `/api/analytics/api/v1/${shortLink}`, {
                target: '#analytics-result',
                swap: 'innerHTML'
            }).then(() => {
                document.getElementById('analytics-loading').style.display = 'none';
            });
        }
    }
}

// HTMX event handlers
document.body.addEventListener('htmx:responseError', function(evt) {
    const target = evt.detail.target;
    if (evt.detail.xhr.status === 404) {
        target.innerHTML = Utils.createErrorElement(
            'URL Not Found',
            'The shortened URL you entered was not found. Please check the URL and try again.'
        );
    } else {
        target.innerHTML = Utils.createErrorElement(
            'Error',
            'An error occurred. Please try again.'
        );
    }
});

// Handle successful shortener response
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.xhr.status === 201 && evt.detail.target.id === 'shortener-result') {
        try {
            const response = JSON.parse(evt.detail.xhr.responseText);
            if (response.success && response.data && response.data.short_link) {
                const fullUrl = `${window.location.origin}/${response.data.short_link}`;
                evt.detail.target.innerHTML = `
                    <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                        <div class="text-center">
                            <svg class="w-12 h-12 text-green-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <h3 class="text-lg font-medium text-green-800 mb-2">URL Shortened Successfully!</h3>
                            <div class="bg-white border rounded-lg p-4 mb-4">
                                <p class="text-sm text-gray-600 mb-2">Your shortened URL:</p>
                                <div class="flex items-center justify-between bg-gray-50 rounded border p-3">
                                    <span class="font-mono text-blue-600 break-all">${fullUrl}</span>
                                    <button
                                        onclick="copyToClipboard('${fullUrl}', this)"
                                        class="ml-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                                    >
                                        Copy
                                    </button>
                                </div>
                            </div>
                            <p class="text-sm text-gray-600">Click the copy button to copy the link to your clipboard</p>
                        </div>
                    </div>
                `;
            }
        } catch (e) {
            console.error('Error parsing response:', e);
        }
    }
});

// Handle successful analytics response
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.xhr.status === 200 && evt.detail.target.id === 'analytics-result') {
        try {
            const response = JSON.parse(evt.detail.xhr.responseText);
            if (response.success && response.data) {
                const analytics = response.data;
                renderAnalyticsDashboard(analytics, evt.detail.target);
            }
        } catch (e) {
            console.error('Error parsing analytics response:', e);
            evt.detail.target.innerHTML = Utils.createErrorElement(
                'Error',
                'Unable to parse analytics data.'
            );
        }
    }
});

// Copy to clipboard function
function copyToClipboard(text, buttonElement) {
    const button = buttonElement || (window.event && window.event.target);

    navigator.clipboard.writeText(text).then(function() {
        if (button) {
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.classList.add('bg-green-600');
            button.classList.remove('bg-blue-600');

            setTimeout(function() {
                button.textContent = originalText;
                button.classList.remove('bg-green-600');
                button.classList.add('bg-blue-600');
            }, 2000);
        }
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
    });
}

// Process analytics data
function processAnalyticsData(analytics) {
    const totalClicks = analytics.clicks.length;
    const countryStats = {};
    const cityStats = {};
    const clicksByDate = {};
    const clicksByHour = new Array(24).fill(0);
    const recentClicks = analytics.clicks.slice(-20).reverse();

    analytics.clicks.forEach(click => {
        countryStats[click.country] = (countryStats[click.country] || 0) + 1;
        cityStats[click.city] = (cityStats[click.city] || 0) + 1;

        const date = new Date(click.created_at);
        const dateKey = date.toISOString().split('T')[0];
        clicksByDate[dateKey] = (clicksByDate[dateKey] || 0) + 1;
        clicksByHour[date.getHours()]++;
    });

    return {
        totalClicks,
        uniqueCountries: Object.keys(countryStats).length,
        uniqueCities: Object.keys(cityStats).length,
        avgClicksPerDay: totalClicks > 0 ? (totalClicks / Math.max(1, Object.keys(clicksByDate).length)).toFixed(1) : 0,
        topCountries: Object.entries(countryStats).sort(([,a], [,b]) => b - a).slice(0, 10),
        topCities: Object.entries(cityStats).sort(([,a], [,b]) => b - a).slice(0, 10),
        sortedDates: Object.entries(clicksByDate).sort(([a], [b]) => a.localeCompare(b)),
        clicksByHour,
        recentClicks
    };
}

// Render analytics dashboard
function renderAnalyticsDashboard(analytics, targetElement) {
    const data = processAnalyticsData(analytics);
    const fullUrl = window.location.origin + '/' + analytics.short_link;

    targetElement.innerHTML = `
        <div class="space-y-6">
            <!-- Header with URL and actions -->
            <div class="bg-white border rounded-lg p-6">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div class="flex-1">
                        <h3 class="text-xl font-bold text-gray-900 mb-2">Analytics Dashboard</h3>
                        <div class="flex flex-wrap items-center gap-2 text-sm text-gray-600 mb-1">
                            <span>Short URL:</span>
                            <code class="bg-gray-100 px-2 py-1 rounded break-all">${fullUrl}</code>
                            <button
                                onclick="copyToClipboard('${fullUrl}', this)"
                                class="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
                            >
                                Copy
                            </button>
                        </div>
                        <p class="text-sm text-gray-500">Last updated: ${new Date(analytics.updated_at).toLocaleString()}</p>
                    </div>
                    <div class="flex flex-wrap gap-2">
                        <button
                            onclick="refreshAnalytics('${analytics.short_link}')"
                            class="px-3 py-2 sm:px-4 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                        >
                            Refresh
                        </button>
                    </div>
                </div>
            </div>

            <!-- Key Metrics -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                ${Utils.createMetricCard('Total Clicks', data.totalClicks, 'blue', 
                    '<path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>')}
                ${Utils.createMetricCard('Unique Countries', data.uniqueCountries, 'green',
                    '<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clip-rule="evenodd"/>')}
                ${Utils.createMetricCard('Unique Cities', data.uniqueCities, 'purple',
                    '<path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>')}
                ${Utils.createMetricCard('Avg. Clicks/Day', data.avgClicksPerDay, 'orange',
                    '<path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>')}
            </div>

            <!-- Clicks Over Time Chart -->
            <div class="bg-white border rounded-lg p-6">
                <h4 class="font-semibold text-gray-900 mb-4">Clicks Over Time</h4>
                <div style="height: 250px;">
                    <canvas id="clicksOverTimeChart"></canvas>
                </div>
            </div>

            <!-- Top Locations -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-white border rounded-lg p-6">
                    <h4 class="font-semibold text-gray-900 mb-4">Top Countries</h4>
                    <div class="space-y-2">
                        ${data.topCountries.slice(0, 5).length > 0 ? data.topCountries.slice(0, 5).map(([country, count]) => `
                            <div class="flex justify-between items-center py-2 border-b last:border-0">
                                <span class="text-sm font-medium text-gray-900">${country}</span>
                                <span class="text-sm text-gray-600">${count} clicks</span>
                            </div>
                        `).join('') : '<p class="text-center text-gray-500">No data available</p>'}
                    </div>
                </div>
                <div class="bg-white border rounded-lg p-6">
                    <h4 class="font-semibold text-gray-900 mb-4">Top Cities</h4>
                    <div class="space-y-2">
                        ${data.topCities.slice(0, 5).length > 0 ? data.topCities.slice(0, 5).map(([city, count]) => `
                            <div class="flex justify-between items-center py-2 border-b last:border-0">
                                <span class="text-sm font-medium text-gray-900">${city}</span>
                                <span class="text-sm text-gray-600">${count} clicks</span>
                            </div>
                        `).join('') : '<p class="text-center text-gray-500">No data available</p>'}
                    </div>
                </div>
            </div>

            <!-- Recent Clicks Table -->
            <div class="bg-white border rounded-lg p-6">
                <h4 class="font-semibold text-gray-900 mb-4">Recent Clicks</h4>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            ${data.recentClicks.length > 0 ? data.recentClicks.map(click => `
                                <tr>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        ${new Date(click.created_at).toLocaleString()}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        ${click.city}, ${click.country}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        ${click.ip}
                                    </td>
                                </tr>
                            `).join('') : `
                                <tr>
                                    <td colspan="3" class="px-6 py-4 text-center text-sm text-gray-500">
                                        No clicks recorded yet
                                    </td>
                                </tr>
                            `}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    // Initialize charts after DOM is updated
    setTimeout(() => {
        initializeCharts(data.sortedDates);
    }, 100);
}

// Chart configuration helper
function createChartConfig(type, labels, data, options = {}) {
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        }
    };

    return {
        type,
        data: {
            labels,
            datasets: [{
                label: options.label || 'Data',
                data,
                ...options.datasetOptions
            }]
        },
        options: {
            ...defaultOptions,
            ...options.chartOptions
        }
    };
}

// Initialize Chart.js charts
function initializeCharts(sortedDates) {
    Chart.defaults.font.family = 'Inter, ui-sans-serif, system-ui';

    // Clicks Over Time - the only chart we're keeping
    const ctxTime = document.getElementById('clicksOverTimeChart');
    if (ctxTime) {
        if (sortedDates.length === 0) {
            ctxTime.parentElement.innerHTML += '<p class="text-center text-gray-500 mt-4">No data available</p>';
        } else {
            const chartType = sortedDates.length === 1 ? 'bar' : 'line';
            const config = createChartConfig(
                chartType,
                sortedDates.map(([date]) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                sortedDates.map(([, count]) => count),
                {
                    label: 'Clicks',
                    datasetOptions: chartType === 'line' 
                        ? { borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', tension: 0.1 }
                        : { backgroundColor: 'rgba(59, 130, 246, 0.8)', barThickness: 60, maxBarThickness: 80 },
                    chartOptions: {
                        scales: {
                            y: { beginAtZero: true, ticks: { stepSize: 1 } },
                            x: chartType === 'bar' ? { grid: { display: false } } : {}
                        }
                    }
                }
            );
            new Chart(ctxTime, config);
        }
    }
}

// Refresh analytics data
function refreshAnalytics(shortLink) {
    const input = document.getElementById('analytics-input');
    input.value = shortLink;
    document.getElementById('analytics-form').dispatchEvent(new Event('submit'));
}