import { html } from "./dom.js";
import { STATUS } from "./lifecycle.js";

const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });
const relative = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

export function formatDateTime(value) {
  return value ? dateTime.format(new Date(value)) : "—";
}

export function timeAgo(value) {
  if (!value) return "";
  const seconds = (new Date(value) - Date.now()) / 1000;
  const units = [
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return relative.format(Math.round(seconds / size), unit);
  }
  return "just now";
}

export function formatDistance(km) {
  if (km === null || km === undefined) return "";
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(km < 10 ? 1 : 0)} km`;
}

export function formatCoordinates(latitude, longitude) {
  return `${Number(latitude).toFixed(4)}, ${Number(longitude).toFixed(4)}`;
}

export function initials(name = "") {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "G";
}

export function statusBadge(status) {
  const meta = STATUS[status] ?? { label: status, tone: "" };
  return html`<span class="badge badge-${meta.tone}">${meta.label}</span>`;
}

/** Star rating with its count, or an honest "No reviews yet". */
export function ratingSummary(average, count) {
  if (!count) return html`<span class="rating"><small>No reviews yet</small></span>`;
  return html`<span class="rating" title="${average} out of 5">
    <span class="stars" style="--percent:${(average / 5) * 100}%" aria-hidden="true"></span>
    ${average.toFixed(1)} <small>(${count})</small>
  </span>`;
}

export function branchTitle(branch) {
  return branch.branch_name || branch.laundry_name || `Branch #${branch.id}`;
}
