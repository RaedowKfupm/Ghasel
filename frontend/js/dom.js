// Safe HTML templating: every interpolated value is escaped unless wrapped in raw().

class SafeHtml {
  constructor(value) {
    this.value = value;
  }
  toString() {
    return this.value;
  }
}

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ESCAPES[c]);
}

/** Trust a string that is already HTML (e.g. an icon or another html`` result). */
export const raw = (value) => new SafeHtml(String(value));

function interpolate(value) {
  if (value === null || value === undefined || value === false) return "";
  if (value instanceof SafeHtml) return value.value;
  if (Array.isArray(value)) return value.map(interpolate).join("");
  return escapeHtml(value);
}

export function html(strings, ...values) {
  return new SafeHtml(strings.reduce((out, s, i) => out + s + (i < values.length ? interpolate(values[i]) : ""), ""));
}

export function render(element, template) {
  element.innerHTML = interpolate(template);
  return element;
}

export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

/** Read a form into a plain object; empty strings become null. */
export function formValues(form) {
  return Object.fromEntries(
    [...new FormData(form).entries()].map(([key, value]) => [key, typeof value === "string" && value.trim() === "" ? null : value]),
  );
}
