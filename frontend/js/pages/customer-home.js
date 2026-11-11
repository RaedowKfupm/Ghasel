import { api } from "../api.js";
import { html } from "../dom.js";
import { emptyState } from "../feedback.js";
import { icon } from "../icons.js";
import { ACTIVE_STATUSES } from "../lifecycle.js";
import { navigate } from "../router.js";
import { session } from "../session.js";
import { bindOrderActions, openCreateOrder, orderCard } from "../components/orders.js";
import { asyncPage } from "./page.js";

export function renderCustomerHome(root) {
  const firstName = session.user.name.split(" ")[0];
  let orders = [];

  const reload = asyncPage(root, {
    header: html`<section class="hero">
      <span class="eyebrow">Hi ${firstName}</span>
      <h1>Laundry, picked up from your door.</h1>
      <p>Post a request and the nearest laundries compete to accept it, or choose a rated branch yourself.</p>
      <div class="hero-actions">
        <button class="btn btn-primary" type="button" data-new-order>${icon("plus")} Request a pickup</button>
        <a class="btn btn-ghost" href="#/discover">${icon("search")} Find laundries nearby</a>
      </div>
    </section>`,
    load: async () => (orders = await api.orders.list()),
    view: (all) => {
      const active = all.filter((o) => ACTIVE_STATUSES.has(o.status));
      const delivered = all.filter((o) => o.status === "completed");
      const toReview = delivered.filter((o) => !o.review);
      return html`
        <div class="stats section">
          <div class="stat"><span>Active orders</span><strong>${active.length}</strong></div>
          <div class="stat"><span>Delivered</span><strong>${delivered.length}</strong></div>
          <div class="stat"><span>Waiting for your review</span><strong>${toReview.length}</strong></div>
        </div>
        <section class="section">
          <div class="section-head"><h2>In progress</h2>${all.length ? html`<a class="btn btn-ghost btn-sm" href="#/orders">All orders</a>` : ""}</div>
          ${active.length
            ? html`<div class="grid grid-2" data-orders>${active.slice(0, 4).map((o) => orderCard(o))}</div>`
            : emptyState({
                glyph: "sparkle",
                title: "Nothing in the wash right now",
                message: "Request a pickup and follow it here from acceptance to delivery.",
                action: html`<button class="btn btn-primary" type="button" data-new-order>${icon("plus")} Request a pickup</button>`,
              })}
        </section>`;
    },
    afterRender: (body) => {
      const list = body.querySelector("[data-orders]");
      if (list) bindOrderActions(list, () => orders, () => reload({ quiet: true }));
    },
  });

  root.addEventListener("click", (event) => {
    if (event.target.closest("[data-new-order]")) openCreateOrder({ onCreated: () => navigate("orders") });
  });
}
