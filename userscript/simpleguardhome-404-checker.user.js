// ==UserScript==
// @name         SimpleGuardHome 404 Checker
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Detects 404 responses and checks if they are blocked by AdGuard Home
// @author       SimpleGuardHome
// @match        *://*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_registerMenuCommand
// @connect      *
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    // Default configuration
    const DEFAULT_CONFIG = {
        host: 'http://localhost',
        port: 8000
    };

    // Get current configuration
    function getConfig() {
        return {
            host: GM_getValue('host', DEFAULT_CONFIG.host),
            port: GM_getValue('port', DEFAULT_CONFIG.port)
        };
    }

    // Show configuration dialog
    function showConfigDialog() {
        const config = getConfig();
        const host = prompt('Enter SimpleGuardHome host (e.g. http://localhost):', config.host);
        if (host === null) return;

        const port = prompt('Enter SimpleGuardHome port:', config.port);
        if (port === null) return;

        GM_setValue('host', host);
        GM_setValue('port', parseInt(port, 10) || DEFAULT_CONFIG.port);

        alert('Configuration saved! The new settings will be used for future checks.');
    }

    // Register configuration menu command
    GM_registerMenuCommand('Configure SimpleGuardHome Instance', showConfigDialog);

    // Store check results to avoid repeated API calls
    const checkedDomains = new Map();

    // Check if domain is blocked by AdGuard Home
    async function checkDomain(domain) {
        // Skip if already checked recently
        if (checkedDomains.has(domain)) {
            const cachedResult = checkedDomains.get(domain);
            if (Date.now() - cachedResult.timestamp < 3600000) { // Cache for 1 hour
                return;
            }
        }

        try {
            const config = getConfig();
            const apiUrl = `${config.host}:${config.port}/control/filtering/check_host?name=${encodeURIComponent(domain)}`;

            GM_xmlhttpRequest({
                method: 'GET',
                url: apiUrl,
                headers: {'Accept': 'application/json'},
                onload: function(response) {
                    try {
                        const data = JSON.parse(response.responseText);
                        const isBlocked = data.reason.startsWith('Filtered');
                        
                        // Cache the result
                        checkedDomains.set(domain, {
                            isBlocked,
                            timestamp: Date.now()
                        });

                        // If blocked, redirect to SimpleGuardHome interface
                        if (isBlocked) {
                            window.location.href = apiUrl;
                        }
                    } catch (error) {
                        console.error('SimpleGuardHome parsing error:', error);
                    }
                },
                onerror: function(error) {
                    console.error('SimpleGuardHome API error:', error);
                }
            });
        } catch (error) {
            console.error('SimpleGuardHome check error:', error);
        }
    }

    // Intercept 404 responses using a fetch handler
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        try {
            const response = await originalFetch.apply(this, args);
            if (response.status === 404) {
                const url = new URL(args[0].toString());
                checkDomain(url.hostname);
            }
            return response;
        } catch (error) {
            console.error('SimpleGuardHome 404 Checker Error:', error);
            return originalFetch.apply(this, args);
        }
    };

    // Also intercept XHR for broader compatibility
    const originalXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
        const originalOnReadyStateChange = this.onreadystatechange;
        this.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 404) {
                const urlObj = new URL(url, window.location.href);
                checkDomain(urlObj.hostname);
            }
            if (originalOnReadyStateChange) {
                originalOnReadyStateChange.apply(this, arguments);
            }
        };
        originalXHROpen.apply(this, [method, url, ...rest]);
    };
})();