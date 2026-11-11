import { api } from "../api.js";
import { $, html, render } from "../dom.js";
import { emptyState, errorState, loading } from "../feedback.js";
import { icon } from "../icons.js";
import { saveLocation, savedLocation } from "../location.js";
import { navigate } from "../router.js";
import { bindBranchCards, branchCard } from "../components/branches.js";
import { locationPicker } from "../components/location-picker.js";
import { openCreateOrder } from "../components/orders.js";
import { pageHeader } from "./page.js";

const RADII = [2, 5, 10, 25, 50];

export function renderDiscover(root) {
  let radius = 10;
  let branches = [];

  render(
    root,
    html`${pageHeader(
      "Discover",
      "Laundries near you",
      "Distances come from each branch's saved location; ratings come only from customers whose orders were delivered.",
      html`<button class="btn btn-primary" type="button" data-new-order>${icon("plus")} Post to marketplace</button>`,
    )}
    <div class="grid grid-sidebar">
      <aside class="card stack">
        <h3>Search area</h3>
        <div data-picker></div>
        <div class="field">Radius
          <div class="cluster">${RADII.map(
            (km) => html`<button class="chip" type="button" data-km="${km}" aria-pressed="${km === radius}">${km} km</button>`,
          )}</div>
        </div>
      </aside>
      <section data-results></section>
    </div>`,
  );

  const results = $("[data-results]", root);

  async function search() {
    const point = picker.value;
    if (!point) {
      render(
        results,
        emptyState({
          glyph: "pin",
          title: "Where should we look?",
          message: "Share your location, pick a city or enter coordinates to see laundries around you.",
        }),
      );
      return;
    }
    render(results, loading(4));
    try {
      branches = await api.branches.nearby({ latitude: point.latitude, longitude: point.longitude, radius_km: radius });
      render(results, branches.length ? resultsView() : noResultsView());
    } catch (error) {
      render(results, errorState(error));
    }
  }

  const resultsView = () => html`
    <div class="spread" style="margin-bottom:12px">
      <strong>${branches.length} branch${branches.length === 1 ? "" : "es"} within ${radius} km</strong>
      <small class="muted">Nearest first</small>
    </div>
    <div class="grid grid-2">${branches.map((branch) =>
      branchCard(branch, {
        actions: html`<button class="btn btn-primary btn-sm" type="button" data-order="${branch.id}">Request pickup</button>
          <button class="btn btn-ghost btn-sm" type="button" data-view>Reviews & details</button>`,
      }),
    )}</div>`;

  const noResultsView = () =>
    emptyState({
      glyph: "search",
      title: `No laundries within ${radius} km`,
      message: "Try a larger radius, or post your request to the marketplace so laundries serving your area can accept it.",
      action: html`<button class="btn btn-primary" type="button" data-new-order>Post to marketplace</button>`,
    });

  const picker = locationPicker($("[data-picker]", root), {
    initial: savedLocation(),
    onChange: (point) => {
      saveLocation(point);
      search();
    },
  });

  const afterOrder = () => navigate("orders");
  bindBranchCards(results, { allowOrder: true, onOrdered: afterOrder });

  root.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-km]");
    if (chip) {
      radius = Number(chip.dataset.km);
      root.querySelectorAll("[data-km]").forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      search();
    }
    const order = event.target.closest("[data-order]");
    if (order) openCreateOrder({ branch: branches.find((b) => b.id === Number(order.dataset.order)), onCreated: afterOrder });
    if (event.target.closest("[data-new-order]")) openCreateOrder({ onCreated: afterOrder });
    if (event.target.closest("[data-retry]")) search();
  });

  search();
}
