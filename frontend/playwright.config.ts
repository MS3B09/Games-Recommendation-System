import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests', fullyParallel: false, workers: 1, timeout: 30_000,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:4173', browserName: 'chromium' },
  webServer: {
    command: 'npm run preview', url: 'http://127.0.0.1:4173', reuseExistingServer: false,
    timeout: 30_000,
  },
});
