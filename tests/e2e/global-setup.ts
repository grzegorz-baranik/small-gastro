import { FullConfig } from '@playwright/test';

/**
 * Global setup runs before all tests.
 * Verifies that the Docker stack is running and healthy.
 */
async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL = config.projects[0].use?.baseURL || 'http://localhost:8304';
  const backendURL = baseURL.replace(':8304', ':8303');

  console.log('Checking backend health...');

  try {
    // Check backend health endpoint (at root, not under /api/v1)
    const response = await fetch(`${backendURL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Backend returned status ${response.status}`);
    }

    console.log('Backend health check passed');
  } catch (error) {
    console.error('Backend health check failed:', error);
    console.error('\nMake sure Docker stack is running:');
    console.error('  docker compose up -d');
    console.error('  docker compose exec backend alembic upgrade head');
    throw new Error('Backend not available. Start Docker stack first.');
  }

  console.log('Global setup complete');
}

export default globalSetup;
