import { test, expect } from '@playwright/test';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8080';

test.describe('Food Operations Platform — End-to-End User Journey', () => {
  test.beforeEach(async ({ page, request }) => {
    // Authenticate and inject JWT token into browser localStorage
    const loginRes = await request.post(`${GATEWAY_URL}/api/v1/auth/login`, {
      data: {
        email: 'customer@foodplatform.com',
        password: 'Customer123!',
      },
    });

    if (loginRes.ok()) {
      const { accessToken, user } = await loginRes.json();
      await page.addInitScript(
        ({ token, usr }) => {
          localStorage.setItem('accessToken', token);
          localStorage.setItem('user', JSON.stringify(usr));
        },
        { token: accessToken, usr: user }
      );
    }
  });

  test('1. Dashboard renders operational metrics and microservice matrix', async ({ page }) => {
    await page.goto('/');

    // Check title and branding
    await expect(page.locator('text=Operations Control Center')).toBeVisible();
    await expect(page.locator('text=All 7 Services Healthy')).toBeVisible();

    // Check microservice table
    await expect(page.locator('text=API Gateway')).toBeVisible();
    await expect(page.locator('text=Product Service')).toBeVisible();
    await expect(page.locator('text=Order Service')).toBeVisible();
  });

  test('2. Product catalog search and category filtering', async ({ page }) => {
    await page.goto('/products');

    await expect(page.locator('text=Product Catalog')).toBeVisible();

    // Verify search input
    const searchInput = page.locator('input[placeholder*="Search products"]');
    await expect(searchInput).toBeVisible();

    // Type query
    await searchInput.fill('Milk');
    await page.waitForTimeout(500);

    // Verify search results table or items exist
    const rows = page.locator('tbody tr');
    await expect(rows.first()).toBeVisible();
  });

  test('3. Inventory stock inspector across fulfillment hubs', async ({ page }) => {
    await page.goto('/inventory');

    await expect(page.locator('text=Inventory & Stock Levels')).toBeVisible();
    await expect(page.locator('text=Fulfillment Warehouses')).toBeVisible();
    await expect(
      page.locator('text=Select Product to Inspect Real-Time Multi-Warehouse Stock:')
    ).toBeVisible();
  });

  test('4. Order placement with Idempotency-Key and lifecycle tracking', async ({ page }) => {
    await page.goto('/orders');

    await expect(page.locator('text=Order Management')).toBeVisible();

    // Click Create Order
    await page.locator('button:has-text("Create Order")').click();

    // Verify modal and idempotency key banner
    await expect(page.locator('text=Idempotency-Key Header:')).toBeVisible();

    // Submit order
    await page.locator('button:has-text("Place Order")').click();

    // Verify confirmation toast or order in list
    await expect(page.locator('text=Outbox choreography initiated')).toBeVisible({ timeout: 10000 });
  });

  test('5. AI Operations Assistant tool-calling and SSE streaming', async ({ page }) => {
    await page.goto('/assistant');

    await expect(page.locator('text=FoodOps AI Assistant')).toBeVisible();
    await expect(page.locator('text=Tool-Calling Agent')).toBeVisible();

    // Click prompt pill
    const promptButton = page.locator('button:has-text("Show today\'s sales and revenue KPI")');
    if (await promptButton.isVisible()) {
      await promptButton.click();

      // Verify tool call badge and streaming response
      await expect(page.locator('text=Tool Dispatched:')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=get_daily_sales')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=Data Returned from Service:')).toBeVisible({ timeout: 10000 });
    }
  });
});
