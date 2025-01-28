# SimpleGuardHome 404 Checker Userscript

A Tampermonkey userscript that detects 404 responses while browsing and automatically checks if the domains are blocked by your AdGuard Home instance. This helps identify when DNS blocking might be causing page load failures.

## Features

- Automatically detects 404 responses from both fetch and XMLHttpRequest calls
- Checks failed domains against your AdGuard Home instance
- Shows notifications for blocked domains with unblock option
- Configurable AdGuard Home instance settings
- Caches results to minimize API calls
- Error handling with configuration shortcuts

## Installation

1. Install the [Tampermonkey](https://www.tampermonkey.net/) browser extension
2. Click on the Tampermonkey icon and select "Create a new script"
3. Copy the contents of `simpleguardhome-404-checker.user.js` into the editor
4. Save the script (Ctrl+S or File -> Save)

## Configuration

1. Click on the Tampermonkey icon in your browser
2. Select "Configure SimpleGuardHome Instance" under the script's menu
3. Enter your AdGuard Home host (e.g., `http://localhost`)
4. Enter your AdGuard Home port (default: 3000)

### Default Settings
- Host: `http://localhost`
- Port: `3000`

## How It Works

1. The script monitors all web requests on any website
2. When a 404 response is detected:
   - Extracts the domain from the failed URL
   - Checks if the domain is blocked by AdGuard Home
   - Shows a notification if the domain is blocked
   - Provides a quick "Unblock" button to open SimpleGuardHome

3. Error handling:
   - Connection issues show a notification with configuration options
   - Results are cached for 1 hour to reduce API load
   - Failed requests provide clear error messages

## Technical Details

### Required Permissions
- `GM_xmlhttpRequest`: For making cross-origin requests to AdGuard Home
- `GM_getValue`/`GM_setValue`: For storing configuration
- `GM_registerMenuCommand`: For adding configuration menu
- `@connect *`: For connecting to custom AdGuard Home instances

### Cache System
- Domain check results are cached for 1 hour
- Cache includes:
  - Block status
  - Blocking reason
  - Applied rules
  - Timestamp

### Error Handling
- Connection failures
- Request timeouts
- API errors
- JSON parsing errors

## Development

The userscript is part of the SimpleGuardHome project and is designed to complement the main application by providing real-time feedback during web browsing.

To modify or extend the script:
1. Make changes to `simpleguardhome-404-checker.user.js`
2. Update version number in the metadata block
3. Reinstall in Tampermonkey to test changes

## License

Same as the main SimpleGuardHome project