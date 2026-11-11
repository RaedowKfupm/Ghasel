// Administrator: approve laundry applications and look up accounts.
import { api } from "../api.js";
import { html } from "../dom.js";
import { emptyState, toast, withBusy } from "../feedback.js";
import { formatDateTime, initials } from "../format.js";
import { asyncPage, pageHeader } from "./page.js";

const ROLE_LABEL = { customer: "Customer", laundry: "Laundry owner", manager: "Branch manager", admin: "Admin" };
const REQUEST_TONE = { pending: "gold", approved: "green", rejected: "red" };

export function renderAdmin(root) {
  const reload = asyncPage(root, {
    header: pageHeader("Administration", "Marketplace review", "Approve laundry companies before they can add branches."),
    load: () => Promise.all([api.laundries.requests(), api.users.list()]),
    view: ([requests, users]) => {
      const pending = requests.filter((r) => r.status === "pending");
      return html`
        <div class="stats">
          <div class="stat"><span>Applications waiting</span><strong>${pending.length}</strong></div>
          <div class="stat"><span>Approved companies</span><strong>${requests.filter((r) => r.status === "approved").length}</strong></div>
          <div class="stat"><span>Accounts</span><strong>${users.length}</strong></div>
        </div>
        <section class="section">
          <div class="section-head"><h2>Laundry applications</h2></div>
          ${requests.length
            ? html`<div class="stack">${requests.map(
                (r) => html`<article class="card card-tight spread wrap-mobile">
                  <div><div class="cluster"><h3>${r.company_name}</h3><span class="badge badge-${REQUEST_TONE[r.status]}">${r.status}</span></div>
                    <div class="meta" style="margin-top:4px"><span>Owner #${r.owner_id}</span><span>${formatDateTime(r.created_at)}</span></div></div>
                  ${r.status === "pending" ? html`<button class="btn btn-primary btn-sm" type="button" data-approve="${r.id}">Approve</button>` : ""}
                </article>`,
              )}</div>`
            : emptyState({ glyph: "store", title: "No applications yet", message: "Laundry owners' applications appear here for review." })}
        </section>
        <section class="section">
          <div class="section-head"><h2>Accounts</h2></div>
          <div class="grid grid-2">${users.map(
            (u) => html`<article class="card card-tight cluster" style="flex-wrap:nowrap">
              <span class="avatar">${initials(u.name)}</span>
              <div style="min-width:0"><strong>${u.name}</strong><div class="meta"><span>${u.email}</span><span>${ROLE_LABEL[u.role]}</span></div></div>
            </article>`,
          )}</div>
        </section>`;
    },
  });

  root.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-approve]");
    if (!button) return;
    await withBusy(button, async () => {
      try {
        const laundry = await api.laundries.approve(Number(button.dataset.approve));
        toast(`${laundry.name} approved`);
        reload({ quiet: true });
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });
}
