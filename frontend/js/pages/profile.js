import { api } from "../api.js";
import { $, formValues, html } from "../dom.js";
import { toast, withBusy } from "../feedback.js";
import { initials } from "../format.js";
import { session } from "../session.js";
import { asyncPage, pageHeader } from "./page.js";

const ROLE_LABEL = { customer: "Customer", laundry: "Laundry owner", manager: "Branch manager", admin: "Administrator" };

export function renderProfile(root, { onUpdated }) {
  const reload = asyncPage(root, {
    header: pageHeader("Account", "Your profile", "Keep your contact details current so laundries can reach you."),
    skeletonRows: 1,
    load: () => api.users.me(),
    view: (user) => {
      const isCustomer = user.role === "customer";
      return html`<form class="card stack" style="max-width:760px" novalidate>
        <div class="cluster" style="gap:16px">
          <span class="avatar avatar-lg">${initials(user.name)}</span>
          <div><h2>${user.name}</h2><span class="badge badge-plain">${ROLE_LABEL[user.role]}</span></div>
        </div>
        <hr class="divider" />
        <div class="form-grid">
          <label class="field">Full name<input class="input" name="name" required value="${user.name}" /></label>
          <label class="field">Email<input class="input" name="email" type="email" required value="${user.email}" /></label>
          ${isCustomer
            ? html`<label class="field">Phone<input class="input" name="phone" type="tel" value="${user.phone ?? ""}" placeholder="+966 5x xxx xxxx" /></label>
                <label class="field">Default pickup address<input class="input" name="address" value="${user.address ?? ""}" placeholder="Building, street, district" /></label>`
            : ""}
        </div>
        <div class="form-actions"><button class="btn btn-primary" type="submit">Save changes</button></div>
      </form>`;
    },
    afterRender: (body, user) => {
      $("form", body).addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!event.target.checkValidity()) return toast("Name and a valid email are required.", "error");
        const values = formValues(event.target);
        const changes = { name: values.name, email: values.email };
        if (user.role === "customer") {
          if (values.phone) changes.phone = values.phone;
          if (values.address !== (user.address ?? null)) {
            if (!values.phone && !user.phone) return toast("Add a phone number to save an address.", "error");
            changes.address = values.address;
          }
        }
        await withBusy(event.submitter, async () => {
          try {
            session.setUser(await api.users.updateMe(changes));
            onUpdated();
            toast("Profile saved");
            reload({ quiet: true });
          } catch (error) {
            toast(error.message, "error");
          }
        });
      });
    },
  });
}
