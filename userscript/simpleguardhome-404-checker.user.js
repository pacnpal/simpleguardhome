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
        port: 8000  // SimpleGuardHome runs on port 8000 by default
    };

    // Get current configuration
    function getConfig() {
        return {
            host: GM_getValue('host', DEFAULT_CONFIG.host),
            port: GM_getValue('port', DEFAULT_CONFIG.port)
        };
    }

    // Test SimpleGuardHome connection
    async function testConnection(host, port) {
        try {
            const response = await new Promise((resolve, reject) => {
                GM_xmlhttpRequest({
                    method: 'GET',
                    url: `${host}:${port}/health`,
                    headers: {'Accept': 'application/json'},
                    onload: resolve,
                    onerror: reject
                });
            });
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }

    // Show configuration dialog
    async function showConfigDialog() {
        const config = getConfig();
        const currentSettings = `Current Settings:
- Host: ${config.host}
- Port: ${config.port}

Enter new settings or cancel to keep current.`;

        const host = prompt(currentSettings + '\n\nEnter SimpleGuardHome host (e.g. http://localhost):', config.host);
        if (host === null) return;

        const port = prompt('Enter SimpleGuardHome port (default: 8000):', config.port);
        if (port === null) return;

        const newPort = parseInt(port, 10) || DEFAULT_CONFIG.port;

        // Test connection with new settings
        const success = await testConnection(host, newPort);
        if (success) {
            GM_setValue('host', host);
            GM_setValue('port', newPort);
            createNotification('SimpleGuardHome configuration saved and connection tested successfully!');
        } else {
            const save = confirm('Could not connect to SimpleGuardHome with these settings. Save anyway?');
            if (save) {
                GM_setValue('host', host);
                GM_setValue('port', newPort);
                createNotification('Configuration saved, but connection test failed. Please verify your settings.');
            }
        }
    }

    // Register configuration menu commands
    GM_registerMenuCommand('⚙️ Configure SimpleGuardHome', showConfigDialog);
    GM_registerMenuCommand('🔄 Test Connection', async () => {
        const config = getConfig();
        const success = await testConnection(config.host, config.port);
        createNotification(success ?
            'Successfully connected to SimpleGuardHome!' :
            'Could not connect to SimpleGuardHome. Please check your settings.');
    });

    // Store check results to avoid repeated API calls
    const checkedDomains = new Map();

    // Create notification container
    function createNotification(message, showUnblockButton = false, domain = '') {
        const notif = document.createElement('div');
        notif.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 9999;
            font-family: sans-serif;
            max-width: 300px;
        `;
        
        const messageDiv = document.createElement('div');
        messageDiv.textContent = message;
        notif.appendChild(messageDiv);

        if (showUnblockButton) {
            const button = document.createElement('button');
            button.textContent = 'Unblock Domain';
            button.style.cssText = `
                margin-top: 10px;
                padding: 5px 10px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            `;
            button.onclick = () => unblockDomain(domain);
            notif.appendChild(button);
        }

        document.body.appendChild(notif);
        setTimeout(() => notif.remove(), 10000); // Remove after 10 seconds
    }

    // Unblock a domain
    async function unblockDomain(domain) {
        const config = getConfig();
        const apiUrl = `${config.host}:${config.port}/control/filtering/unblock_host?name=${encodeURIComponent(domain)}`;

        GM_xmlhttpRequest({
            method: 'GET',
            url: apiUrl,
            headers: {'Accept': 'application/json'},
            onload: function(response) {
                try {
                    const data = JSON.parse(response.responseText);
                    createNotification(data.message);
                    
                    // Update cache if successful
                    if (data.message.includes('unblocked')) {
                        checkedDomains.set(domain, {
                            isBlocked: false,
                            timestamp: Date.now()
                        });
                    }
                } catch (error) {
                    console.error('SimpleGuardHome unblock error:', error);
                    createNotification('Failed to unblock domain. Please try again.');
                }
            },
            onerror: function(error) {
                console.error('SimpleGuardHome API error:', error);
                createNotification('Error connecting to SimpleGuardHome. Please check your settings.');
            }
        });
    }

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

                        // If blocked, show notification with unblock option
                        if (isBlocked) {
                            createNotification(
                                `Domain ${domain} is blocked by AdGuard Home.`,
                                true,
                                domain
                            );
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