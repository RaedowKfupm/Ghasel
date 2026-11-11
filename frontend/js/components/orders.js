// Order cards, progress tracking and the dialogs that act on orders.
import { api } from "../api.js";
import { $, formValues, html } from "../dom.js";
import { closeModal, confirmDialog, modalHeader, openModal, toast, withBusy } from "../feedback.js";
import { branchTitle, formatDateTime, formatDistance, statusBadge, timeAgo } from "../format.js";
import { icon } from "../icons.js";
import {
  ADVANCE_LABEL,
  ORDER_STEPS,
  STATUS,
  branchCanCancel,
  customerCanCancel,
} from "../lifecycle.js";
import { saveLocation, savedLocation } from "../location.js";
import { session } from "../session.js";
import { locationPicker } from "./location-picker.js";

// --- Presentation -------------------------------------------------------------------

export function progressTrack(order) {
  const index = ORDER_STEPS.indexOf(order.status);
  const cancelled = order.status === "cancelled";
  const segments = ORDER_STEPS.slice(1).map((_, i) => {
    const step = i + 1;
    if (cancelled) return html`<span></span>`;
    const state = step <= index ? (step === index && order.status !== "completed" ? "current" : "done") : "";
    return html`<span class="${state}"></span>`;
  });
  const meta = STATUS[order.status];
  return html`<div class="stack" style="gap:8px">
    <div class="track${cancelled ? " cancelled" : ""}" aria-hidden="true" style="grid-template-columns:repeat(6,1fr)">${segments}</div>
    <div class="track-label"><strong>${meta.label}</strong><span>${meta.description}</span></div>
  </div>`;
}

function branchLine(order) {
  if (!order.branch) return html`<span>${icon("clock")} Waiting for a nearby laundry to accept</span>`;
  return html`<span>${icon("store")} ${order.branch.laundry_name} · ${branchTitle(order.branch)}</span>`;
}

function customerActions(order) {
  return html`
    <button class="btn btn-ghost btn-sm" type="button" data-action="details">Track order</button>
    ${customerCanCancel(order) ? html`<button class="btn btn-ghost btn-sm" type="button" data-action="cancel">Cancel</button>` : ""}
    ${order.status === "completed" && !order.review
      ? html`<button class="btn btn-primary btn-sm" type="button" data-action="review">${icon("star")} Rate this order</button>`
      : ""}
    ${order.review ? html`<span class="badge badge-gold badge-plain">${icon("star")} You rated ${order.review.rating}/5</span>` : ""}`;
}

function managerActions(order) {
  if (order.status === "pending") {
    return html`<button class="btn btn-primary btn-sm" type="button" data-action="accept">${icon("check")} Accept order</button>
      <button class="btn btn-ghost btn-sm" type="button" data-action="details">Details</button>`;
  }
  return html`
    ${order.next_status
      ? html`<button class="btn btn-primary btn-sm" type="button" data-action="advance" data-next="${order.next_status}">
          ${ADVANCE_LABEL[order.next_status]}</button>`
      : ""}
    <button class="btn btn-ghost btn-sm" type="button" data-action="details">Details</button>
    ${branchCanCancel(order) ? html`<button class="btn btn-ghost btn-sm" type="button" data-action="cancel">Cancel</button>` : ""}`;
}

function managerMeta(order) {
  const hasDistance = order.distance_km !== undefined && order.distance_km !== null;
  return html`<span>${icon("pin")} ${order.pickup_address ?? "No pickup address"}</span>
    ${order.status === "pending" ? html`<span>${order.branch_id ? "Direct request to your branch" : "Marketplace request"}</span>` : ""}
    ${hasDistance ? html`<span>${icon("clock")} ${timeAgo(order.created_at)}</span>` : ""}`;
}

export function orderCard(order, viewer = "customer") {
  const isManager = viewer === "manager";
  const hasDistance = isManager && order.distance_km !== undefined && order.distance_km !== null;
  return html`<article class="card card-tight order-card" data-order-id="${order.id}">
    <div class="spread">
      <div class="cluster"><h3>Order #${order.id}</h3>${statusBadge(order.status)}</div>
      ${hasDistance
        ? html`<span class="distance">${icon("route")} ${formatDistance(order.distance_km)} away</span>`
        : html`<small class="muted">${timeAgo(order.created_at)}</small>`}
    </div>
    <div class="meta">${isManager ? managerMeta(order) : branchLine(order)}</div>
    <p class="details">${order.details}</p>
    ${order.status !== "pending" ? progressTrack(order) : ""}
    <div class="actions">${isManager ? managerActions(order) : customerActions(order)}</div>
  </article>`;
}

function timeline(order) {
  const reached = new Map(order.history.map((event) => [event.status, event]));
  const currentIndex = ORDER_STEPS.indexOf(order.status);
  const steps = order.status === "cancelled" ? ORDER_STEPS.filter((s) => reached.has(s)) : ORDER_STEPS;

  const actorLabel = (event) => {
    if (!event?.actor_role) return "";
    if (event.actor_role === "customer") return session.user.role === "customer" ? " · by you" : " · by customer";
    return " · by the laundry";
  };

  const items = steps.map((status) => {
    const event = reached.get(status);
    const index = ORDER_STEPS.indexOf(status);
    const state = order.status === "cancelled" || index < currentIndex || order.status === "completed"
      ? "done"
      : index === currentIndex
        ? "current"
        : "upcoming";
    return html`<li class="${state}">
      <span class="dot">${state === "done" ? icon("check") : ""}</span>
      <div><strong>${STATUS[status].label}</strong>
        <small>${event ? `${formatDateTime(event.created_at)}${actorLabel(event)}` : STATUS[status].description}</small></div>
    </li>`;
  });

  if (order.status === "cancelled") {
    const event = reached.get("cancelled");
    items.push(html`<li class="cancelled"><span class="dot">${icon("x")}</span>
      <div><strong>Cancelled</strong><small>${formatDateTime(event?.created_at)}${actorLabel(event)}</small></div></li>`);
  }
  return html`<ol class="timeline">${items}</ol>`;
}

// --- Dialogs ----------------------------------------------------------------------

export async function openOrderDetails(orderId) {
  const order = await api.orders.get(orderId);
  const branch = order.branch;
  openModal(
    html`${modalHeader(`Order #${order.id}`, STATUS[order.status].label)}
      <div class="stack" style="gap:20px">
        <p>${order.details}</p>
        <dl class="detail-list">
          <div><dt>Laundry</dt><dd>${branch ? `${branch.laundry_name} · ${branchTitle(branch)}` : "Not assigned yet"}</dd></div>
          <div><dt>Branch contact</dt><dd>${branch ? branch.phone : "—"}</dd></div>
          <div><dt>Pickup address</dt><dd>${order.pickup_address ?? "—"}</dd></div>
          <div><dt>Requested</dt><dd>${formatDateTime(order.created_at)}</dd></div>
        </dl>
        <section><h3 style="margin-bottom:14px">Progress</h3>${timeline(order)}</section>
        ${order.review
          ? html`<div class="notice">${icon("star")}<div><strong>Rated ${order.review.rating}/5</strong>${order.review.comment ? html`<div>${order.review.comment}</div>` : ""}</div></div>`
          : ""}
      </div>`,
    { wide: true },
  );
}

export function openCreateOrder({ branch = null, onCreated = () => {} } = {}) {
  const direct = Boolean(branch);
  const modal = openModal(html`${modalHeader(direct ? "Direct request" : "Marketplace request", direct ? branchTitle(branch) : "Request a pickup")}
    <form class="stack" novalidate>
      <div class="notice notice-info">${icon("info")}<span>${direct
        ? `${branch.laundry_name} will be asked to accept this order.`
        : "Laundries whose service area covers your pickup point can accept this request. The first to accept gets it."}</span></div>
      <label class="field">What needs cleaning?
        <textarea class="input" name="details" required minlength="3" maxlength="1000" placeholder="e.g. 4 shirts and 2 trousers — wash, iron and fold"></textarea>
      </label>
      <label class="field">Pickup address
        <input class="input" name="pickup_address" required minlength="3" maxlength="300" placeholder="Building, street, district" value="${session.user.address ?? ""}" />
      </label>
      <div class="field">Pickup point <small>Used to match your request with nearby laundries.</small></div>
      <div data-picker></div>
      <div class="form-actions"><button class="btn btn-primary" type="submit">${icon("check")} Submit request</button></div>
    </form>`);

  const picker = locationPicker($("[data-picker]", modal), { initial: savedLocation() });
  $("form", modal).addEventListener("submit", async (event) => {
    event.preventDefault();
    const values = formValues(event.target);
    if (!values.details || values.details.length < 3) return toast("Describe the items to clean (at least 3 characters).", "error");
    if (!values.pickup_address) return toast("Add a pickup address.", "error");
    if (!picker.value) return toast("Choose a pickup point so laundries can find you.", "error");

    await withBusy(event.submitter, async () => {
      try {
        const order = await api.orders.create({
          details: values.details,
          pickup_address: values.pickup_address,
          pickup_latitude: picker.value.latitude,
          pickup_longitude: picker.value.longitude,
          branch_id: branch?.id ?? null,
        });
        saveLocation(picker.value);
        closeModal();
        toast(`Order #${order.id} submitted`);
        onCreated(order);
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });
}

function openReview(order, onDone) {
  const modal = openModal(html`${modalHeader(`Order #${order.id}`, "How was your laundry?")}
    <form class="stack">
      <div class="star-input" role="radiogroup" aria-label="Rating">
        ${[5, 4, 3, 2, 1].map(
          (n) => html`<input type="radio" id="star-${n}" name="rating" value="${n}" /><label for="star-${n}" title="${n} star${n > 1 ? "s" : ""}">★</label>`,
        )}
      </div>
      <label class="field">Comment <small>Optional · shown on the branch page with your first name.</small>
        <textarea class="input" name="comment" maxlength="1000" placeholder="What went well? What could be better?"></textarea>
      </label>
      <div class="form-actions"><button class="btn btn-primary" type="submit">Submit review</button></div>
    </form>`);

  $("form", modal).addEventListener("submit", async (event) => {
    event.preventDefault();
    const { rating, comment } = formValues(event.target);
    if (!rating) return toast("Choose a rating from 1 to 5 stars.", "error");
    await withBusy(event.submitter, async () => {
      try {
        await api.orders.review(order.id, { rating: Number(rating), comment });
        closeModal();
        toast("Thanks — your review is published");
        onDone();
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });
}

// --- Actions -----------------------------------------------------------------------

/** Handle clicks on order card buttons inside `container`; `refresh` reloads the page data. */
export function bindOrderActions(container, orders, refresh) {
  container.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    const card = event.target.closest("[data-order-id]");
    if (!button || !card) return;
    const order = orders().find((o) => o.id === Number(card.dataset.orderId));
    if (!order) return;

    const run = (action, message) =>
      withBusy(button, async () => {
        try {
          const updated = await action();
          toast(message(updated));
        } catch (error) {
          toast(error.message, "error");
        }
        await refresh();
      });

    switch (button.dataset.action) {
      case "details":
        return openOrderDetails(order.id).catch((error) => toast(error.message, "error"));
      case "review":
        return openReview(order, refresh);
      case "accept":
        return run(() => api.orders.accept(order.id), () => `Order #${order.id} is yours — schedule the pickup`);
      case "advance":
        return run(() => api.orders.advance(order.id, button.dataset.next), (o) => `Order #${o.id}: ${STATUS[o.status].label}`);
      case "cancel": {
        const confirmed = await confirmDialog({
          title: `Cancel order #${order.id}?`,
          message: "This can't be undone.",
          confirmLabel: "Cancel order",
          danger: true,
        });
        if (confirmed) await run(() => api.orders.cancel(order.id), () => `Order #${order.id} cancelled`);
      }
    }
  });
}
