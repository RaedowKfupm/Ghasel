import { api } from "../api.js";
import { $, html, render } from "../dom.js";
import { emptyState } from "../feedback.js";
import { icon } from "../icons.js";
import { ACTIVE_STATUSES } from "../lifecycle.js";
import { bindOrderActions, openCreateOrder, orderCard } from "../components/orders.js";
import { asyncPage, pageHeader } from "./page.js";

const TABS = [
  ["active", "In progress", (o) => ACTIVE_STATUSES.has(o.status)],
  ["past", "History", (o) => !ACTIVE_STATUSES.has(o.status)],
];

export function renderCustomerOrders(root) {
  let orders = [];
  let tab = "active";

  const draw = (body) => {
    const [, , matches] = TABS.find(([key]) => key === tab);
    const visible = orders.filter(matches);
    render(
      $("[data-list]", body),
      visible.length
        ? html`<div class="grid grid-2">${visible.map((o) => orderCard(o))}</div>`
        : emptyState(
            tab === "active"
              ? { glyph: "sparkle", title: "No orders in progress", message: "Requests you post appear here until they're delivered." }
              : { glyph: "orders", title: "No past orders yet", message: "Delivered and cancelled orders are kept here." },
          ),
    );
  };

  const reload = asyncPage(root, {
    header: pageHeader(
      "Orders",
      "Your laundry",
      "Every stage below is recorded by the laundry as it happens.",
      html`<button class="btn btn-primary" type="button" data-new-order>${icon("plus")} New request</button>`,
    ),
    load: async () => (orders = await api.orders.list()),
    view: () => html`
      <div class="segmented" role="group" aria-label="Filter orders" style="margin-bottom:18px">
        ${TABS.map(([key, label, matches]) => html`<button type="button" data-tab="${key}" aria-pressed="${key === tab}">
          ${label}<span class="count">${orders.filter(matches).length}</span></button>`)}
      </div>
      <div data-list></div>`,
    afterRender: (body) => {
      draw(body);
      bindOrderActions(body, () => orders, () => reload({ quiet: true }));
      body.addEventListener("click", (event) => {
        const button = event.target.closest("[data-tab]");
        if (!button) return;
        tab = button.dataset.tab;
        body.querySelectorAll("[data-tab]").forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
        draw(body);
      });
    },
  });

  root.addEventListener("click", (event) => {
    if (event.target.closest("[data-new-order]")) openCreateOrder({ onCreated: () => reload() });
  });
}
