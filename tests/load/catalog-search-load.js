import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    catalog_stress: {
      executor: 'ramping-arrival-rate',
      startRate: 50,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 200,
      stages: [
        { duration: '15s', target: 200 },
        { duration: '30s', target: 500 },
        { duration: '15s', target: 100 },
      ],
    },
  },
  thresholds: {
    // Platform SLO: 95% of catalog requests must respond within 50ms (Redis cached + GIN index)
    http_req_duration: ['p(95)<50', 'p(99)<100'],
    http_req_failed: ['rate<0.01'], // < 1% error rate
  },
};

const BASE_URL = __ENV.GATEWAY_URL || 'http://localhost:8080';

const SEARCH_TERMS = ['milk', 'cheese', 'bread', 'apple', 'coffee', 'pasta', 'beef', 'organic'];

export default function () {
  const query = SEARCH_TERMS[Math.floor(Math.random() * SEARCH_TERMS.length)];
  const page = Math.floor(Math.random() * 5);
  const url = `${BASE_URL}/api/v1/products?q=${query}&page=${page}&size=10`;

  const headers = {
    'Accept': 'application/json',
    'X-Correlation-Id': `k6-${__VU}-${__ITER}`,
  };

  const res = http.get(url, { headers });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has content': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body && Array.isArray(body.content);
      } catch {
        return false;
      }
    },
  });

  sleep(0.05);
}
