import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration
 *
 * Target: < 2 minutes total execution time
 * Browsers: Chromium + WebKit
 * Reports: HTML
 */
export default defineConfig({
  testDir: './specs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  reporter: [
    ['html', { open: 'never' }],
    ['list']
  ],

  use: {
    // Docker frontend port (feature-day-closing branch)
    baseURL: 'http://localhost:8304',

    // Collect trace on first retry
    trace: 'on-first-retry',

    // Screenshots only on failure
    screenshot: 'only-on-failure',

    // Video only on failure
    video: 'retain-on-failure',

    // Default timeout for actions
    actionTimeout: 10000,
  },

  // Global timeout per test
  timeout: 30000,

  // Expect timeout
  expect: {
    timeout: 5000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  // Global setup for health check
  globalSetup: require.resolve('./global-setup.ts'),
});
