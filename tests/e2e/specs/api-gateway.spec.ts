import { test, expect } from '@playwright/test';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8080';

test.describe('API Gateway & Distributed Services E2E API Validation', () => {
  test('Gateway routes GET /api/v1/products and injects X-Correlation-Id', async ({ request }) => {
    const res = await request.get(`${GATEWAY_URL}/api/v1/products?size=5`);
    expect(res.status()).toBe(200);

    const correlationId = res.headers()['x-correlation-id'];
    expect(correlationId).toBeDefined();

    const body = await res.json();
    expect(body.content).toBeDefined();
    expect(body.totalElements).toBeGreaterThan(0);
  });

  test('Gateway enforces Idempotency-Key on order creation', async ({ request }) => {
    // 1. Obtain JWT token via auth service
    const loginRes = await request.post(`${GATEWAY_URL}/api/v1/auth/login`, {
      data: {
        email: 'customer@foodplatform.com',
        password: 'Customer123!',
      },
    });
    expect(loginRes.status()).toBe(200);
    const { accessToken, user } = await loginRes.json();
    const authHeaders = {
      Authorization: `Bearer ${accessToken}`,
    };

    // 2. Missing Idempotency-Key returns 400 with RFC 7807 problem detail
    const badRes = await request.post(`${GATEWAY_URL}/api/v1/orders`, {
      headers: authHeaders,
      data: {
        customerId: user.id,
        items: [{ productId: 'a68d0d41-c837-4da4-8c66-e64f5ea6e761', qty: 1 }],
      },
    });
    expect(badRes.status()).toBe(400);

    // 3. Valid Idempotency-Key succeeds
    const key = `e2e-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    const goodRes = await request.post(`${GATEWAY_URL}/api/v1/orders`, {
      headers: {
        ...authHeaders,
        'Idempotency-Key': key,
      },
      data: {
        customerId: user.id,
        items: [{ productId: 'a68d0d41-c837-4da4-8c66-e64f5ea6e761', qty: 1 }],
      },
    });
    expect(goodRes.status()).toBe(201);
    const orderData = await goodRes.json();
    expect(orderData.id).toBeDefined();

    // Idempotent retry with the EXACT same key returns identical order without duplication
    const duplicateRes = await request.post(`${GATEWAY_URL}/api/v1/orders`, {
      headers: {
        ...authHeaders,
        'Idempotency-Key': key,
      },
      data: {
        customerId: user.id,
        items: [{ productId: 'a68d0d41-c837-4da4-8c66-e64f5ea6e761', qty: 1 }],
      },
    });
    expect(duplicateRes.status()).toBe(201);
    const duplicateData = await duplicateRes.json();
    expect(duplicateData.id).toBe(orderData.id);
  });

  test('AI Service tool-calling and SSE streaming via API Gateway', async ({ request }) => {
    const res = await request.post(`${GATEWAY_URL}/api/v1/ai/chat`, {
      data: {
        messages: [{ role: 'user', content: 'Show sales and revenue KPI' }],
      },
    });
    expect(res.status()).toBe(200);
    expect(res.headers()['content-type']).toContain('text/event-stream');

    const bodyText = await res.text();
    expect(bodyText).toContain('event: tool_call');
    expect(bodyText).toContain('get_daily_sales');
    expect(bodyText).toContain('event: token');
    expect(bodyText).toContain('event: done');
  });
});
