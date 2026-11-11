import { api } from "../api.js";
import { $, formValues, html, render } from "../dom.js";
import { toast, withBusy } from "../feedback.js";
import { icon } from "../icons.js";

const STEPS = [
  ["pin", "Request", "Post a pickup or pick a nearby laundry"],
  ["sparkle", "Clean", "Track every stage as it happens"],
  ["truck", "Return", "Delivered back, then rate the service"],
];

function loginForm() {
  return html`<form class="stack" data-form="login" novalidate>
    <header><span class="eyebrow">Welcome back</span><h2>Sign in to Ghasel</h2>
      <p class="muted">Customers, laundry owners, branch managers and admins all sign in here.</p></header>
    <label class="field">Email<input class="input" name="email" type="email" autocomplete="email" required placeholder="you@example.com" /></label>
    <label class="field">Password<input class="input" name="password" type="password" autocomplete="current-password" required /></label>
    <button class="btn btn-primary btn-block" type="submit">Sign in</button>
    <p class="muted" style="text-align:center">New to Ghasel? <a href="#" data-switch="register"><strong>Create an account</strong></a></p>
  </form>`;
}

function registerForm() {
  return html`<form class="stack" data-form="register" novalidate>
    <header><span class="eyebrow">Get started</span><h2>Create your account</h2>
      <p class="muted">Order laundry as a customer, or register your laundry business.</p></header>
    <div class="segmented" role="group" aria-label="Account type">
      <button type="button" data-role="customer" aria-pressed="true">I need laundry done</button>
      <button type="button" data-role="laundry" aria-pressed="false">I run a laundry</button>
    </div>
    <input type="hidden" name="role" value="customer" />
    <label class="field">Full name<input class="input" name="name" autocomplete="name" required /></label>
    <label class="field">Email<input class="input" name="email" type="email" autocomplete="email" required /></label>
    <label class="field">Password <small>At least 8 characters.</small><input class="input" name="password" type="password" autocomplete="new-password" minlength="8" required /></label>
    <button class="btn btn-primary btn-block" type="submit">Create account</button>
    <p class="muted" style="text-align:center">Already registered? <a href="#" data-switch="login"><strong>Sign in</strong></a></p>
  </form>`;
}

export function renderAuth(root, onSignedIn) {
  render(
    root,
    html`<div class="auth">
      <section class="auth-showcase">
        <a class="brand" href="#"><span class="brand-mark">غ</span>Ghasel</a>
        <div class="auth-copy">
          <span class="eyebrow" style="color:var(--gold)">Laundry marketplace</span>
          <h1>Fresh laundry from the laundry nearest you.</h1>
          <p>Post a pickup request and let nearby laundries compete for it, or choose a highly rated branch yourself.</p>
        </div>
        <div class="auth-steps">${STEPS.map(([glyph, title, text]) => html`<div class="auth-step">${icon(glyph)}<strong>${title}</strong><span>${text}</span></div>`)}</div>
      </section>
      <section class="auth-panel"><div class="auth-card">
        <a class="brand" href="#"><span class="brand-mark">غ</span>Ghasel</a>
        <div data-auth-form>${loginForm()}</div>
      </div></section>
    </div>`,
  );

  const slot = $("[data-auth-form]", root);

  root.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-switch]");
    if (toggle) {
      event.preventDefault();
      render(slot, toggle.dataset.switch === "register" ? registerForm() : loginForm());
      $("input:not([type=hidden])", slot)?.focus();
    }
    const role = event.target.closest("[data-role]");
    if (role) {
      slot.querySelectorAll("[data-role]").forEach((b) => b.setAttribute("aria-pressed", String(b === role)));
      $("[name=role]", slot).value = role.dataset.role;
    }
  });

  root.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    const values = formValues(form);
    if (!form.checkValidity()) return toast("Please fill in every field correctly.", "error");
    await withBusy(event.submitter, async () => {
      try {
        const result = form.dataset.form === "login" ? await api.auth.login(values) : await api.auth.register(values);
        await onSignedIn(result.access_token);
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });
}
