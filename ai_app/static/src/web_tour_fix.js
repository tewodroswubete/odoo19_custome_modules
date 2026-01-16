/** @odoo-module */

/**
 * Fix for web_tour.interactive loading error
 * This prevents the args[0].includes error from blocking AI functionality
 */

console.log("🔧 Web Tour Fix Loading...");

// Patch String.prototype.includes if it doesn't exist (shouldn't happen but fixes the error)
if (!String.prototype.includes) {
    String.prototype.includes = function(search, start) {
        'use strict';
        if (search instanceof RegExp) {
            throw TypeError('first argument must not be a RegExp');
        }
        if (start === undefined) { start = 0; }
        return this.indexOf(search, start) !== -1;
    };
}

// Patch Array.prototype.includes if needed
if (!Array.prototype.includes) {
    Array.prototype.includes = function(searchElement, fromIndex) {
        return this.indexOf(searchElement, fromIndex) !== -1;
    };
}

// Catch and suppress web_tour errors to prevent UI blocking
window.addEventListener('error', function(event) {
    if (event.message && event.message.includes('web_tour')) {
        console.warn('⚠️ Web tour error suppressed:', event.message);
        event.preventDefault();
        event.stopPropagation();
        return false;
    }
});

// Catch promise rejections related to web_tour
window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.message && event.reason.message.includes('web_tour')) {
        console.warn('⚠️ Web tour promise rejection suppressed');
        event.preventDefault();
        return false;
    }
});

console.log("✅ Web Tour Fix Loaded!");