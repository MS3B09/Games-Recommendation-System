import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests', testMatch: '**/live-m4.spec.ts', workers: 1, timeout: 300_000,
  reporter: 'list', use: { baseURL: 'http://127.0.0.1:4173', browserName: 'chromium' },
});
