// Create or edit a branch, including its location and service radius.
import { $, formValues, html, render } from "../dom.js";
import { toast, withBusy } from "../feedback.js";
import { icon } from "../icons.js";
import { locationPicker } from "./location-picker.js";

const RADII = [3, 5, 10, 15, 25, 50];

export function branchForm(container, { branch = null, submitLabel = "Save branch", onSubmit }) {
  const currentRadius = branch?.service_radius_km ?? 10;
  // Always offer the saved radius, even if it isn't one of the presets.
  const radii = [...new Set([...RADII, currentRadius])].sort((a, b) => a - b);
  const initial = branch?.latitude != null ? { label: "Saved branch location", latitude: branch.latitude, longitude: branch.longitude } : null;
  render(
    container,
    html`<form class="stack" novalidate>
      <div class="form-grid">
        <label class="field">Branch name<input class="input" name="branch_name" required maxlength="200" value="${branch?.branch_name ?? ""}" placeholder="e.g. Al Khobar North" /></label>
        <label class="field">Phone<input class="input" name="phone" required value="${branch?.phone ?? ""}" placeholder="+966 13 000 0000" /></label>
        <label class="field full">Street address<input class="input" name="branch_address" required maxlength="200" value="${branch?.branch_address ?? ""}" placeholder="Street, district, city" /></label>
        <label class="field">Service radius <small>Marketplace orders within this distance are offered to the branch.</small>
          <select class="input" name="service_radius_km">
            ${radii.map((km) => html`<option value="${km}" ${km === currentRadius ? "selected" : ""}>${km} km</option>`)}
          </select>
        </label>
      </div>
      <div class="field">Branch location <small>Customers find branches by distance from this point.</small></div>
      <div data-picker></div>
      <div class="form-actions"><button class="btn btn-primary" type="submit">${icon("check")} ${submitLabel}</button></div>
    </form>`,
  );

  const picker = locationPicker($("[data-picker]", container), { initial, emptyLabel: "Location not set — hidden from nearby search" });
  $("form", container).addEventListener("submit", async (event) => {
    event.preventDefault();
    const values = formValues(event.target);
    if (!values.branch_name || !values.branch_address || !values.phone) return toast("Name, address and phone are required.", "error");
    await withBusy(event.submitter, () =>
      onSubmit({
        branch_name: values.branch_name,
        branch_address: values.branch_address,
        phone: values.phone,
        service_radius_km: Number(values.service_radius_km),
        latitude: picker.value?.latitude ?? null,
        longitude: picker.value?.longitude ?? null,
      }).catch((error) => toast(error.message, "error")),
    );
  });
}
