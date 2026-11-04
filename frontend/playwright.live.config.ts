import { defineConfig } from '@playwright/test';

// Explicit developer-only check. Requires the existing catalog and local runtime
// configuration; never runs in normal CI or against a deployed frontend.
export default defineConfig({
  testDir: './tests', testMatch: '**/live-m3.spec.ts', workers: 1, timeout: 180_000,
  reporter: 'list', outputDir: './test-results-live',
  use: { baseURL: 'http://127.0.0.1:4173', browserName: 'chromium' },
});
