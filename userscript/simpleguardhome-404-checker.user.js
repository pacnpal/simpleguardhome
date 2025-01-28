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
        port: 3000
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
                headers: {
                    'Accept': 'application/json'
                },
                onload: function(response) {
                    try {
                        const data = JSON.parse(response.responseText);
                        const isBlocked = data.reason.startsWith('Filtered');
                        
                        // Cache the result
                        checkedDomains.set(domain, {
                            isBlocked,
                            reason: data.reason,
                            rules: data.rules,
                            timestamp: Date.now()
                        });

                        // Show notification if blocked
                        if (isBlocked) {
                            showNotification(domain, data);
                        }
                    } catch (error) {
                        console.error('SimpleGuardHome parsing error:', error);
                    }
                },
                onerror: function(error) {
                    console.error('SimpleGuardHome API error:', error);
                    showNotification(domain, null, 'Unable to connect to SimpleGuardHome instance. Please check your configuration.');
                },
                onabort: function() {
                    console.error('SimpleGuardHome API request aborted');
                    showNotification(domain, null, 'Request to SimpleGuardHome instance was aborted. Please check your configuration.');
                },
                ontimeout: function() {
                    console.error('SimpleGuardHome API request timed out');
                    showNotification(domain, null, 'Request to SimpleGuardHome instance timed out. Please check your configuration.');
                }
            });
        } catch (error) {
            console.error('SimpleGuardHome check error:', error);
        }
    }

    // Show a notification when a blocked domain is detected
    function showNotification(domain, data, error = null) {
        const notification = document.createElement('div');
        const config = getConfig();
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px;
            background: ${error ? '#fff3cd' : '#f8d7d9'};
            border-left: 4px solid ${error ? '#ffc107' : '#dc3545'};
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 9999;
            max-width: 400px;
            font-family: system-ui, -apple-system, sans-serif;
        `;

        if (error) {
            notification.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 5px;">SimpleGuardHome Error</div>
                <div style="font-size: 14px;">${error}</div>
                <button style="margin-top: 10px; background: #ffc107; color: black; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Configure Instance</button>
            `;

            const configButton = notification.querySelector('button');
            configButton.addEventListener('click', () => {
                showConfigDialog();
                notification.remove();
            });
        } else {
            notification.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 5px;">404 Domain is Blocked</div>
                <div style="font-size: 14px;"><strong>${domain}</strong></div>
                <div style="font-size: 12px; margin-top: 5px;">Reason: ${data.reason}</div>
                ${data.rules?.length ? `<div style="font-size: 12px; margin-top: 5px; background: rgba(0,0,0,0.05); padding: 5px; border-radius: 3px;">Rule: ${data.rules[0].text}</div>` : ''}
                <button style="margin-top: 10px; background: #0d6efd; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Unblock Domain</button>
            `;

            const unblockButton = notification.querySelector('button');
            unblockButton.addEventListener('click', () => {
                window.open(`${config.host}:${config.port}/?domain=${encodeURIComponent(domain)}`, '_blank');
                notification.remove();
            });
        }

        // Auto-remove after 10 seconds
        setTimeout(() => notification.remove(), 10000);

        document.body.appendChild(notification);
    }
})();