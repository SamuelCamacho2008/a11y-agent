/**
 * A11y Agent — Environment Configuration
 * Differentiates local development from GitHub Pages production.
 */
window.A11Y_CONFIG = {
    // API endpoint for Headless Playwright backend (Level 1 Precision).
    // In local development, points to the local FastAPI server.
    // The Render service is defined in render.yaml. Update this URL if Render assigns a different hostname.
    // If empty or unreachable, the frontend falls back automatically to Level 2 (Multi-Proxy Anti-Bot).
    apiEndpoint: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? 'http://localhost:8000'
        : 'https://a11y-agent-api-samuelcamacho2008.onrender.com',

    // Allow time for Render's free instance to wake before falling back to Level 2.
    backendTimeoutMs: 120000,

    // Resilient client-side proxy fallback enabled
    enableClientFallback: true,

    // Production environment flag
    isProduction: window.location.hostname.endsWith('github.io'),

    // Version
    version: '1.2.2'
};
