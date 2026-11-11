// Branch cards and the branch details dialog with its reviews.
import { api } from "../api.js";
import { $, html } from "../dom.js";
import { closeModal, modalHeader, openModal, toast } from "../feedback.js";
import { branchTitle, formatCoordinates, formatDistance, ratingSummary, timeAgo } from "../format.js";
import { icon } from "../icons.js";
import { openCreateOrder } from "./orders.js";

/** `showCompany` is false where every card belongs to the same company (the owner's view). */
export function branchCard(branch, { actions = "", showCompany = true } = {}) {
  return html`<article class="card card-tight card-interactive branch-card" data-branch-id="${branch.id}">
    <div class="spread">
      <div class="title">${showCompany
        ? html`<h3>${branch.laundry_name}</h3><span>${branchTitle(branch)}</span>`
        : html`<h3>${branchTitle(branch)}</h3><span>Branch #${branch.id}</span>`}</div>
      ${branch.distance_km !== undefined ? html`<span class="distance">${icon("pin")} ${formatDistance(branch.distance_km)}</span>` : ""}
    </div>
    ${ratingSummary(branch.rating_average, branch.rating_count)}
    <div class="meta">
      <span>${icon("pin")} ${branch.branch_address}</span>
      <span>${icon("phone")} ${branch.phone}</span>
    </div>
    ${actions ? html`<div class="cluster">${actions}</div>` : ""}
  </article>`;
}

function reviewItem(review) {
  return html`<div class="review">
    <div class="spread">
      <span class="rating"><span class="stars" style="--percent:${review.rating * 20}%" aria-label="${review.rating} out of 5"></span>
        ${review.reviewer_name}</span>
      <small class="muted">${timeAgo(review.created_at)}</small>
    </div>
    ${review.comment ? html`<p>${review.comment}</p>` : ""}
  </div>`;
}

export async function openBranchDetails(branchId, { allowOrder = false, onOrdered = () => {} } = {}) {
  const [branch, reviews] = await Promise.all([api.branches.get(branchId), api.branches.reviews(branchId)]);
  const modal = openModal(
    html`${modalHeader(branch.laundry_name, branchTitle(branch))}
      <div class="stack" style="gap:20px">
        <div class="spread wrap-mobile">
          ${ratingSummary(branch.rating_average, branch.rating_count)}
          ${allowOrder ? html`<button class="btn btn-primary" type="button" data-order>${icon("plus")} Request pickup here</button>` : ""}
        </div>
        <dl class="detail-list">
          <div><dt>Address</dt><dd>${branch.branch_address}</dd></div>
          <div><dt>Phone</dt><dd>${branch.phone}</dd></div>
          <div><dt>Service area</dt><dd>Within ${branch.service_radius_km} km</dd></div>
          <div><dt>Coordinates</dt><dd>${branch.latitude !== null ? formatCoordinates(branch.latitude, branch.longitude) : "Not set"}</dd></div>
        </dl>
        <section>
          <h3>Customer reviews</h3>
          ${reviews.length
            ? reviews.map(reviewItem)
            : html`<p class="muted" style="margin-top:8px">No reviews yet. Reviews come from customers whose orders were delivered.</p>`}
        </section>
      </div>`,
    { wide: true },
  );
  $("[data-order]", modal)?.addEventListener("click", () => {
    closeModal();
    openCreateOrder({ branch, onCreated: onOrdered });
  });
}

/** Open branch details when a card (not one of its buttons) is clicked. */
export function bindBranchCards(container, options) {
  container.addEventListener("click", (event) => {
    const card = event.target.closest("[data-branch-id]");
    if (!card || event.target.closest("button:not([data-view])")) return;
    openBranchDetails(Number(card.dataset.branchId), options).catch((error) => toast(error.message, "error"));
  });
}
