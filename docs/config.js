/**
 * A11y Agent — Environment Configuration
 * Differentiates local development from GitHub Pages production.
 */
window.A11Y_CONFIG = {
    // API endpoint for Headless Playwright backend (Level 1 Precision).
    // In local development, points to the local FastAPI server.
    // In production, configure your deployed cloud instance (Render, Hugging Face Spaces, etc.).
    // If empty or unreachable, the frontend falls back automatically to Level 2 (Multi-Proxy Anti-Bot).
    apiEndpoint: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? 'http://localhost:8000'
        : 'https://samuelcamacho2008-a11y-agent-api.hf.space',

    // Connection timeout for cloud backend before falling back to Level 2 (in milliseconds)
    backendTimeoutMs: 8000,

    // Resilient client-side proxy fallback enabled
    enableClientFallback: true,

    // Production environment flag
    isProduction: window.location.hostname.endsWith('github.io'),

    // Version
    version: '1.2.0'
};
