// Toasts, modals and the loading / empty / error states every page uses.
import { $, html, render } from "./dom.js";
import { icon } from "./icons.js";

export function toast(message, type = "success") {
  const region = $("#toasts");
  const item = document.createElement("div");
  item.className = `toast${type === "error" ? " toast-error" : ""}`;
  item.setAttribute("role", type === "error" ? "alert" : "status");
  render(item, html`${icon(type === "error" ? "alert" : "check")}<span>${message}</span>`);
  region.append(item);
  setTimeout(() => item.remove(), 4200);
}

let lastFocus = null;

/** Open a modal; returns the modal element so callers can wire up its contents. */
export function openModal(template, { wide = false } = {}) {
  lastFocus = document.activeElement;
  const backdrop = $("#modal-root");
  render(backdrop, html`<div class="modal-backdrop" data-close-modal>
    <div class="modal${wide ? " modal-wide" : ""}" role="dialog" aria-modal="true">${template}</div>
  </div>`);
  const modal = $(".modal", backdrop);
  modal.querySelector("input, textarea, select, button:not([data-close-modal])")?.focus();
  return modal;
}

export function closeModal() {
  render($("#modal-root"), "");
  lastFocus?.focus?.();
}

export function modalHeader(eyebrow, title) {
  return html`<div class="modal-head">
    <div><span class="eyebrow">${eyebrow}</span><h2>${title}</h2></div>
    <button class="icon-btn" type="button" data-close-modal aria-label="Close">${icon("x")}</button>
  </div>`;
}

document.addEventListener("click", (event) => {
  const target = event.target.closest("[data-close-modal]");
  if (target && (target === event.target || target.tagName === "BUTTON")) closeModal();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && $("#modal-root").firstElementChild) closeModal();
});

export function confirmDialog({ title, message, confirmLabel = "Confirm", danger = false }) {
  return new Promise((resolve) => {
    const modal = openModal(html`${modalHeader("Please confirm", title)}
      <p class="muted">${message}</p>
      <div class="form-actions">
        <button class="btn btn-ghost" type="button" data-answer="no">Keep it</button>
        <button class="btn ${danger ? "btn-danger" : "btn-primary"}" type="button" data-answer="yes">${confirmLabel}</button>
      </div>`);
    modal.addEventListener("click", (event) => {
      const answer = event.target.closest("[data-answer]")?.dataset.answer;
      if (!answer) return;
      closeModal();
      resolve(answer === "yes");
    });
  });
}

export const loading = (rows = 3) =>
  html`<div class="stack" aria-busy="true" aria-label="Loading">${Array.from({ length: rows }, () => html`<div class="skeleton"></div>`)}</div>`;

export function emptyState({ glyph = "inbox", title, message, action = "" }) {
  return html`<div class="card empty">
    <div class="glyph">${icon(glyph)}</div>
    <h3>${title}</h3>
    <p>${message}</p>
    ${action}
  </div>`;
}

export function errorState(error, retryLabel = "Try again") {
  return html`<div class="card empty">
    <div class="glyph">${icon("alert")}</div>
    <h3>Something went wrong</h3>
    <p>${error.message}</p>
    <button class="btn btn-ghost" type="button" data-retry>${icon("refresh")} ${retryLabel}</button>
  </div>`;
}

/** Run an async action while showing a spinner on the button that triggered it. */
export async function withBusy(button, action) {
  if (!button) return action();
  button.disabled = true;
  button.classList.add("is-busy");
  try {
    return await action();
  } finally {
    button.disabled = false;
    button.classList.remove("is-busy");
  }
}
