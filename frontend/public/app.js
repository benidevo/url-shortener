// Alpine.js app data
function app() {
    return {
        currentPage: 'shortener',
        showResult: false,
        
        submitAnalytics(event) {
            const input = document.getElementById('analytics-input');
            let shortLink = input.value.trim();
            
            // Extract short code from full URL if needed
            if (shortLink.includes('/')) {
                shortLink = shortLink.split('/').pop();
            }
            
            // Update the HTMX request URL
            event.target.setAttribute('hx-get', `/api/analytics/api/v1/${shortLink}`);
            
            // Trigger HTMX request
            htmx.trigger(event.target, 'submit');
        }
    }
}

// HTMX event handlers
document.body.addEventListener('htmx:responseError', function(evt) {
    const target = evt.detail.target;
    if (evt.detail.xhr.status === 404) {
        target.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex">
                    <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-800">URL Not Found</h3>
                        <p class="mt-1 text-sm text-red-700">The shortened URL you entered was not found. Please check the URL and try again.</p>
                    </div>
                </div>
            </div>
        `;
    } else {
        target.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex">
                    <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-800">Error</h3>
                        <p class="mt-1 text-sm text-red-700">An error occurred. Please try again.</p>
                    </div>
                </div>
            </div>
        `;
    }
});

// Handle successful shortener response
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.xhr.status === 201 && evt.detail.target.id === 'shortener-result') {
        try {
            const response = JSON.parse(evt.detail.xhr.responseText);
            if (response.success && response.data && response.data.short_link) {
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
                                    <span class="font-mono text-blue-600 break-all">${response.data.short_link}</span>
                                    <button 
                                        onclick="copyToClipboard('${response.data.short_link}')"
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
                const totalClicks = analytics.clicks.length;
                
                // Aggregate data by country and city
                const countryStats = {};
                const cityStats = {};
                const recentClicks = analytics.clicks.slice(-10).reverse(); // Last 10 clicks
                
                analytics.clicks.forEach(click => {
                    countryStats[click.country] = (countryStats[click.country] || 0) + 1;
                    cityStats[click.city] = (cityStats[click.city] || 0) + 1;
                });
                
                const topCountries = Object.entries(countryStats)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5);
                
                const topCities = Object.entries(cityStats)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5);
                
                evt.detail.target.innerHTML = `
                    <div class="bg-white border rounded-lg p-6 space-y-6">
                        <div class="text-center">
                            <h3 class="text-xl font-bold text-gray-900 mb-2">Analytics for ${analytics.short_link}</h3>
                            <div class="text-3xl font-bold text-blue-600">${totalClicks}</div>
                            <p class="text-gray-600">Total Clicks</p>
                        </div>
                        
                        <div class="grid md:grid-cols-2 gap-6">
                            <!-- Top Countries -->
                            <div>
                                <h4 class="font-semibold text-gray-900 mb-3">Top Countries</h4>
                                <div class="space-y-2">
                                    ${topCountries.length > 0 ? topCountries.map(([country, count]) => `
                                        <div class="flex justify-between items-center p-2 bg-gray-50 rounded">
                                            <span class="text-gray-700">${country}</span>
                                            <span class="font-medium text-blue-600">${count}</span>
                                        </div>
                                    `).join('') : '<p class="text-gray-500 text-sm">No data available</p>'}
                                </div>
                            </div>
                            
                            <!-- Top Cities -->
                            <div>
                                <h4 class="font-semibold text-gray-900 mb-3">Top Cities</h4>
                                <div class="space-y-2">
                                    ${topCities.length > 0 ? topCities.map(([city, count]) => `
                                        <div class="flex justify-between items-center p-2 bg-gray-50 rounded">
                                            <span class="text-gray-700">${city}</span>
                                            <span class="font-medium text-green-600">${count}</span>
                                        </div>
                                    `).join('') : '<p class="text-gray-500 text-sm">No data available</p>'}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Recent Clicks -->
                        <div>
                            <h4 class="font-semibold text-gray-900 mb-3">Recent Clicks</h4>
                            <div class="space-y-2">
                                ${recentClicks.length > 0 ? recentClicks.map(click => `
                                    <div class="flex justify-between items-center p-3 bg-gray-50 rounded text-sm">
                                        <div>
                                            <span class="text-gray-700">${click.city}, ${click.country}</span>
                                        </div>
                                        <div class="text-gray-500">
                                            ${new Date(click.created_at).toLocaleString()}
                                        </div>
                                    </div>
                                `).join('') : '<p class="text-gray-500 text-sm">No clicks yet</p>'}
                            </div>
                        </div>
                        
                        <div class="text-center text-sm text-gray-500">
                            Last updated: ${new Date(analytics.updated_at).toLocaleString()}
                        </div>
                    </div>
                `;
            }
        } catch (e) {
            console.error('Error parsing analytics response:', e);
            evt.detail.target.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div class="flex">
                        <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                        </svg>
                        <div class="ml-3">
                            <h3 class="text-sm font-medium text-red-800">Error</h3>
                            <p class="mt-1 text-sm text-red-700">Unable to parse analytics data.</p>
                        </div>
                    </div>
                </div>
            `;
        }
    }
});

// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show success feedback
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('bg-green-600');
        button.classList.remove('bg-blue-600');
        
        setTimeout(function() {
            button.textContent = originalText;
            button.classList.remove('bg-green-600');
            button.classList.add('bg-blue-600');
        }, 2000);
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
    });
}