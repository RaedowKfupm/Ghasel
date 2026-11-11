// Thin client for the Ghasel API. Every screen gets its data through here.
import { API_BASE } from "./config.js";
import { session } from "./session.js";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function describe(detail, status) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    // FastAPI validation errors: report the first field problem readably.
    const { loc = [], msg } = detail[0];
    const field = loc.filter((part) => !["body", "query"].includes(part)).join(".");
    return field ? `${field.replaceAll("_", " ")}: ${msg}` : msg;
  }
  return `Request failed (${status})`;
}

async function request(path, { method = "GET", body, query } = {}) {
  const url = new URL(path, API_BASE);
  Object.entries(query ?? {}).forEach(([key, value]) => value !== undefined && value !== null && url.searchParams.set(key, value));

  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (session.token) headers.Authorization = `Bearer ${session.token}`;

  let response;
  try {
    response = await fetch(url, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError(0, "Can't reach the Ghasel API. Check that the server is running.");
  }

  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && session.token) session.end();
    throw new ApiError(response.status, describe(data?.detail, response.status));
  }
  return data;
}

const page = (limit = 50, pageNumber = 1) => ({ limit, page: pageNumber });

export const api = {
  auth: {
    login: (credentials) => request("/auth/login", { method: "POST", body: credentials }),
    register: (account) => request("/auth/register", { method: "POST", body: account }),
  },
  users: {
    me: () => request("/users/me"),
    updateMe: (changes) => request("/users/me", { method: "PATCH", body: changes }),
    list: () => request("/users/", { query: page(100) }),
  },
  laundries: {
    apply: (companyName) => request("/laundries/", { method: "POST", body: { company_name: companyName } }),
    requests: () => request("/laundries/requests", { query: page(100) }),
    myRequest: () => request("/laundries/requests/me"),
    approve: (requestId) => request(`/laundries/requests/${requestId}/approve`, { method: "POST" }),
    get: (laundryId) => request(`/laundries/${laundryId}`),
    branches: (laundryId) => request(`/laundries/${laundryId}/branches`, { query: page(100) }),
    createBranch: (laundryId, branch) => request(`/laundries/${laundryId}/branches`, { method: "POST", body: branch }),
    managers: (laundryId) => request(`/laundries/${laundryId}/managers`),
    createManager: (laundryId, manager) => request(`/laundries/${laundryId}/managers`, { method: "POST", body: manager }),
  },
  branches: {
    nearby: (search) => request("/branches/nearby", { query: { limit: 20, ...search } }),
    get: (branchId) => request(`/branches/${branchId}`),
    update: (branchId, changes) => request(`/branches/${branchId}`, { method: "PATCH", body: changes }),
    reviews: (branchId) => request(`/branches/${branchId}/reviews`, { query: page(20) }),
  },
  orders: {
    list: () => request("/orders/", { query: page(100) }),
    available: () => request("/orders/available", { query: page(100) }),
    get: (orderId) => request(`/orders/${orderId}`),
    create: (order) => request("/orders/", { method: "POST", body: order }),
    accept: (orderId) => request(`/orders/${orderId}/accept`, { method: "POST" }),
    cancel: (orderId) => request(`/orders/${orderId}/cancel`, { method: "POST" }),
    advance: (orderId, status) => request(`/orders/${orderId}/status`, { method: "PATCH", body: { status } }),
    review: (orderId, review) => request(`/orders/${orderId}/review`, { method: "POST", body: review }),
  },
};
