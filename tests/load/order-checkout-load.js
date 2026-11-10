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

  let productId = __ENV.PRODUCT_ID;
  if (!productId) {
    const prodRes = http.get(`${BASE_URL}/api/v1/products?size=1`);
    if (prodRes.status === 200) {
      try {
        const pData = JSON.parse(prodRes.body);
        if (pData.content && pData.content.length > 0) {
          productId = pData.content[0].id;
        }
      } catch (e) {}
    }
  }

  if (loginRes.status === 200) {
    const data = JSON.parse(loginRes.body);
    return { token: data.accessToken, customerId: data.user.id, productId };
  }
  return { token: null, customerId: 'b44d2402-65ab-48fd-8a71-f1f3fdddc0bc', productId };
}

export default function (data) {
  const idempotencyKey = `k6-${__VU}-${__ITER}-${Date.now()}`;

  const payload = JSON.stringify({
    customerId: data.customerId,
    items: [
      {
        productId: data.productId || '0015fe4b-68ea-425f-a86f-61aef58e0d5e',
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
