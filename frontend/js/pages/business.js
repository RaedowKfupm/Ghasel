// Laundry owner: apply for approval, then manage branches and branch managers.
import { api } from "../api.js";
import { $, formValues, html } from "../dom.js";
import { closeModal, emptyState, modalHeader, openModal, toast, withBusy } from "../feedback.js";
import { branchTitle } from "../format.js";
import { icon } from "../icons.js";
import { session } from "../session.js";
import { branchCard } from "../components/branches.js";
import { branchForm } from "../components/branch-form.js";
import { asyncPage, pageHeader } from "./page.js";

function pendingView(request) {
  return html`<div class="card empty">
    <div class="glyph">${icon("clock")}</div>
    <h3>${request.company_name} is awaiting approval</h3>
    <p>An administrator will review your application. Branch tools unlock as soon as it's approved.</p>
  </div>`;
}

function applicationView(rejected) {
  return html`<div class="grid grid-2">
    <form class="card stack" data-apply novalidate>
      ${rejected ? html`<div class="notice notice-danger">${icon("alert")}<span>Your application for ${rejected.company_name} was not approved. You can apply again.</span></div>` : ""}
      <div><h3>Register your laundry company</h3><p class="muted">An administrator reviews each application before the company goes live.</p></div>
      <label class="field">Company name<input class="input" name="company_name" required minlength="2" maxlength="120" placeholder="e.g. Crisp & Clean Laundry" /></label>
      <button class="btn btn-primary" type="submit">Submit application</button>
    </form>
    <div class="card stack">
      <h3>What happens next</h3>
      <ol class="timeline">
        <li class="current"><span class="dot"></span><div><strong>Apply</strong><small>Submit your company name</small></div></li>
        <li class="upcoming"><span class="dot"></span><div><strong>Approval</strong><small>An admin approves the company</small></div></li>
        <li class="upcoming"><span class="dot"></span><div><strong>Set up branches</strong><small>Add locations and branch managers</small></div></li>
      </ol>
    </div>
  </div>`;
}

function companyView({ laundry, branches, managers }) {
  const located = branches.filter((b) => b.latitude !== null).length;
  const managerNames = (branchId) =>
    managers.filter((m) => m.laundry_branch_id === branchId).map((m) => m.name).join(", ");

  return html`
    <section class="hero" style="margin-bottom:22px">
      <span class="eyebrow">Your company</span>
      <h1>${laundry.name}</h1>
      <div class="hero-actions">
        <button class="btn btn-primary" type="button" data-add-branch>${icon("plus")} Add branch</button>
        <button class="btn btn-ghost" type="button" data-add-manager ${branches.length ? "" : "disabled"}>${icon("users")} Add manager</button>
      </div>
    </section>
    <div class="stats">
      <div class="stat"><span>Branches</span><strong>${branches.length}</strong></div>
      <div class="stat"><span>Visible in nearby search</span><strong>${located}</strong></div>
      <div class="stat"><span>Branch managers</span><strong>${managers.length}</strong></div>
    </div>
    <section class="section">
      <div class="section-head"><h2>Branches</h2></div>
      ${branches.length
        ? html`<div class="grid grid-2">${branches.map((branch) =>
            branchCard(branch, {
              showCompany: false,
              actions: html`
                ${branch.latitude === null ? html`<span class="badge badge-gold">No location set</span>` : ""}
                <span class="badge badge-plain">${icon("users")} ${managerNames(branch.id) || "No manager yet"}</span>
                <button class="btn btn-ghost btn-sm" type="button" data-edit-branch="${branch.id}">Edit</button>`,
            }),
          )}</div>`
        : emptyState({
            glyph: "store",
            title: "Add your first branch",
            message: "Branches with a location appear in customers' nearby search and receive marketplace requests.",
            action: html`<button class="btn btn-primary" type="button" data-add-branch>${icon("plus")} Add branch</button>`,
          })}
    </section>`;
}

export function renderBusiness(root) {
  let state = null;

  const reload = asyncPage(root, {
    header: pageHeader("Business", "Laundry management", "Your company, its branches and the managers who run them."),
    load: async () => {
      const me = await api.users.me();
      session.setUser(me);
      if (!me.laundry_id) return (state = { laundry: null, request: await api.laundries.myRequest() });
      const [laundry, branches, managers] = await Promise.all([
        api.laundries.get(me.laundry_id),
        api.laundries.branches(me.laundry_id),
        api.laundries.managers(me.laundry_id),
      ]);
      return (state = { laundry, branches, managers });
    },
    view: (data) => {
      if (data.laundry) return companyView(data);
      if (data.request?.status === "pending") return pendingView(data.request);
      return applicationView(data.request?.status === "rejected" ? data.request : null);
    },
  });

  function openBranchModal(branch = null) {
    const modal = openModal(html`${modalHeader(branch ? "Edit branch" : "New branch", branch ? branchTitle(branch) : "Add a branch")}<div data-form></div>`, { wide: true });
    branchForm($("[data-form]", modal), {
      branch,
      submitLabel: branch ? "Save changes" : "Create branch",
      onSubmit: async (values) => {
        if (branch) await api.branches.update(branch.id, values);
        else await api.laundries.createBranch(state.laundry.id, values);
        closeModal();
        toast(branch ? "Branch updated" : "Branch created");
        reload({ quiet: true });
      },
    });
  }

  function openManagerModal() {
    const modal = openModal(html`${modalHeader("Team", "Add a branch manager")}
      <form class="stack" novalidate>
        <div class="form-grid">
          <label class="field">Full name<input class="input" name="name" required /></label>
          <label class="field">Branch<select class="input" name="branch_id">${state.branches.map((b) => html`<option value="${b.id}">${branchTitle(b)}</option>`)}</select></label>
          <label class="field">Email<input class="input" name="email" type="email" required /></label>
          <label class="field">Temporary password <small>At least 8 characters.</small><input class="input" name="password" type="password" minlength="8" required /></label>
        </div>
        <div class="form-actions"><button class="btn btn-primary" type="submit">Create manager</button></div>
      </form>`);
    $("form", modal).addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!event.target.checkValidity()) return toast("Fill in every field; the password needs 8+ characters.", "error");
      const values = formValues(event.target);
      await withBusy(event.submitter, async () => {
        try {
          await api.laundries.createManager(state.laundry.id, { ...values, branch_id: Number(values.branch_id) });
          closeModal();
          toast(`${values.name} can now sign in and manage the branch`);
          reload({ quiet: true });
        } catch (error) {
          toast(error.message, "error");
        }
      });
    });
  }

  root.addEventListener("click", (event) => {
    if (event.target.closest("[data-add-branch]")) openBranchModal();
    if (event.target.closest("[data-add-manager]")) openManagerModal();
    const edit = event.target.closest("[data-edit-branch]");
    if (edit) openBranchModal(state.branches.find((b) => b.id === Number(edit.dataset.editBranch)));
  });

  root.addEventListener("submit", async (event) => {
    if (!event.target.matches("[data-apply]")) return;
    event.preventDefault();
    const { company_name: name } = formValues(event.target);
    if (!name || name.length < 2) return toast("Enter your company name.", "error");
    await withBusy(event.submitter, async () => {
      try {
        await api.laundries.apply(name);
        toast("Application submitted — you'll get access once an admin approves it");
        reload({ quiet: true });
      } catch (error) {
        toast(error.message, "error");
      }
    });
  });
}
