// Branch manager: accept nearby requests and move accepted orders through each stage.
import { api } from "../api.js";
import { $, html, render } from "../dom.js";
import { emptyState } from "../feedback.js";
import { icon } from "../icons.js";
import { ACTIVE_STATUSES } from "../lifecycle.js";
import { bindOrderActions, orderCard } from "../components/orders.js";
import { asyncPage, pageHeader } from "./page.js";

const TABS = {
  available: {
    label: "Available",
    empty: { glyph: "inbox", title: "No requests to accept", message: "Marketplace requests inside your service area and direct requests to your branch appear here." },
  },
  active: {
    label: "In progress",
    empty: { glyph: "sparkle", title: "Nothing in progress", message: "Orders you accept move here until they're delivered." },
  },
  done: {
    label: "Finished",
    empty: { glyph: "orders", title: "No finished orders yet", message: "Delivered and cancelled orders are kept here." },
  },
};

export function renderOperations(root) {
  let tab = "available";
  let data = { available: [], active: [], done: [], branch: null };
  const all = () => [...data.available, ...data.active, ...data.done];

  const draw = (body) => {
    const orders = data[tab];
    render(
      $("[data-list]", body),
      orders.length ? html`<div class="grid grid-2">${orders.map((o) => orderCard(o, "manager"))}</div>` : emptyState(TABS[tab].empty),
    );
  };

  const reload = asyncPage(root, {
    header: pageHeader(
      "Branch operations",
      "Orders",
      "Accept requests, then record each stage so customers can follow along.",
      html`<button class="btn btn-ghost" type="button" data-refresh>${icon("refresh")} Refresh</button>`,
    ),
    load: async () => {
      const [available, assigned, me] = await Promise.all([api.orders.available(), api.orders.list(), api.users.me()]);
      const branch = me.laundry_branch_id ? await api.branches.get(me.laundry_branch_id) : null;
      const mine = assigned.filter((o) => o.status !== "pending");
      data = {
        available,
        active: mine.filter((o) => ACTIVE_STATUSES.has(o.status)),
        done: mine.filter((o) => !ACTIVE_STATUSES.has(o.status)),
        branch,
      };
      return data;
    },
    view: ({ branch }) => html`
      ${branch && branch.latitude === null
        ? html`<div class="notice" style="margin-bottom:18px">${icon("alert")}<span>Your branch has no location yet, so it only receives direct requests.
            <a href="#/branch"><strong>Set the branch location</strong></a> to receive marketplace orders within ${branch.service_radius_km} km.</span></div>`
        : ""}
      ${branch ? html`<div class="stats" style="margin-bottom:22px">
        <div class="stat"><span>Waiting to be accepted</span><strong>${data.available.length}</strong></div>
        <div class="stat"><span>In progress</span><strong>${data.active.length}</strong></div>
        <div class="stat"><span>Service area</span><strong>${branch.service_radius_km} km</strong></div>
      </div>` : ""}
      <div class="segmented" role="group" aria-label="Order queue" style="margin-bottom:18px">
        ${Object.entries(TABS).map(([key, { label }]) => html`<button type="button" data-tab="${key}" aria-pressed="${key === tab}">
          ${label}<span class="count">${data[key].length}</span></button>`)}
      </div>
      <div data-list></div>`,
    afterRender: (body) => {
      draw(body);
      bindOrderActions(body, all, () => reload({ quiet: true }));
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
    if (event.target.closest("[data-refresh]")) reload();
  });
}
