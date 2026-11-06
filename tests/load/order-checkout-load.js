import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    checkout_concurrency: {
      executor: 'constant-arrival-rate',
      rate: 50,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 30,
      maxVUs: 100,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<300'], // 95% of orders processed within 300ms
    http_req_failed: ['rate<0.05'], // < 5% error rate under peak concurrency
  },
};

const BASE_URL = __ENV.GATEWAY_URL || 'http://localhost:8080';

// Setup: login once to obtain access token
export function setup() {
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({
      email: 'customer@foodplatform.com',
      password: 'Customer123!',
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  if (loginRes.status === 200) {
    const data = JSON.parse(loginRes.body);
    return { token: data.accessToken, customerId: data.user.id };
  }
  return { token: null, customerId: 'b44d2402-65ab-48fd-8a71-f1f3fdddc0bc' };
}

export default function (data) {
  const idempotencyKey = `k6-${__VU}-${__ITER}-${Date.now()}`;

  const payload = JSON.stringify({
    customerId: data.customerId,
    items: [
      {
        productId: 'a68d0d41-c837-4da4-8c66-e64f5ea6e761',
        qty: 1,
      },
    ],
  });

  const headers = {
    'Content-Type': 'application/json',
    'Idempotency-Key': idempotencyKey,
    'X-Correlation-Id': `k6-order-${__VU}-${__ITER}`,
  };

  if (data.token) {
    headers['Authorization'] = `Bearer ${data.token}`;
  }

  const res = http.post(`${BASE_URL}/api/v1/orders`, payload, { headers });

  check(res, {
    'order created status is 201': (r) => r.status === 201,
    'order has ID': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body && body.id !== undefined;
      } catch {
        return false;
      }
    },
  });

  sleep(0.1);
}
