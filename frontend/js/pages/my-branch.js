// Branch manager: keep the branch's details, location and service area up to date.
import { api } from "../api.js";
import { $, html, render } from "../dom.js";
import { emptyState, toast } from "../feedback.js";
import { branchTitle, ratingSummary, timeAgo } from "../format.js";
import { session } from "../session.js";
import { branchForm } from "../components/branch-form.js";
import { asyncPage, pageHeader } from "./page.js";

export function renderMyBranch(root) {
  const branchId = session.user.laundry_branch_id;
  if (!branchId) {
    render(
      root,
      html`${pageHeader("Branch", "My branch")}${emptyState({
        glyph: "store",
        title: "No branch assigned",
        message: "Ask your laundry owner to assign you to a branch.",
      })}`,
    );
    return;
  }

  const reload = asyncPage(root, {
    header: pageHeader("Branch", "My branch", "Customers see these details, and marketplace orders are matched against this location."),
    load: () => Promise.all([api.branches.get(branchId), api.branches.reviews(branchId)]),
    view: ([branch, reviews]) => html`<div class="grid grid-sidebar">
      <aside class="stack">
        <div class="card stack">
          <div><span class="eyebrow">${branch.laundry_name}</span><h2>${branchTitle(branch)}</h2></div>
          ${ratingSummary(branch.rating_average, branch.rating_count)}
        </div>
        <div class="card">
          <h3>Latest reviews</h3>
          ${reviews.length
            ? reviews.slice(0, 5).map(
                (r) => html`<div class="review"><div class="spread"><span class="rating"><span class="stars" style="--percent:${r.rating * 20}%"></span>${r.reviewer_name}</span>
                  <small class="muted">${timeAgo(r.created_at)}</small></div>${r.comment ? html`<p>${r.comment}</p>` : ""}</div>`,
              )
            : html`<p class="muted" style="margin-top:8px">Reviews appear after customers rate delivered orders.</p>`}
        </div>
      </aside>
      <section class="card"><h3 style="margin-bottom:16px">Branch details</h3><div data-form></div></section>
    </div>`,
    afterRender: (body, [branch]) => {
      branchForm($("[data-form]", body), {
        branch,
        submitLabel: "Save changes",
        onSubmit: async (changes) => {
          await api.branches.update(branch.id, changes);
          toast("Branch details saved");
          reload({ quiet: true });
        },
      });
    },
  });
}
