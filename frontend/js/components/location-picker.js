// Choose a point: browser geolocation, a city preset, or typed coordinates.
import { $, $$, html, render } from "../dom.js";
import { toast } from "../feedback.js";
import { formatCoordinates } from "../format.js";
import { icon } from "../icons.js";
import { CITY_PRESETS, currentPosition, isValidCoordinate } from "../location.js";

/**
 * Render a location picker into `container`.
 * Returns { get value(), set(location) }; `onChange(location)` fires on every change.
 */
export function locationPicker(container, { initial = null, emptyLabel = "No location selected", onChange = () => {} } = {}) {
  let value = initial;

  function draw() {
    render(
      container,
      html`<div class="location-picker">
        <div class="location-current">
          <span class="pin">${icon("pin")}</span>
          <div>
            <strong>${value ? value.label : emptyLabel}</strong>
            <small>${value ? formatCoordinates(value.latitude, value.longitude) : "Use your location, pick a city or enter coordinates"}</small>
          </div>
        </div>
        <div class="cluster">
          <button class="btn btn-dark btn-sm" type="button" data-locate>${icon("crosshair")} Use my location</button>
          ${CITY_PRESETS.map(
            (city) => html`<button class="chip" type="button" data-city="${city.label}"
              aria-pressed="${value?.label === city.label}">${city.label}</button>`,
          )}
        </div>
        <details>
          <summary class="muted" style="cursor:pointer;font-size:.85rem;font-weight:650">Enter exact coordinates</summary>
          <div class="coordinate-row" style="margin-top:10px">
            <label class="field">Latitude<input class="input" data-lat type="number" step="any" min="-90" max="90" value="${value?.latitude ?? ""}" /></label>
            <label class="field">Longitude<input class="input" data-lng type="number" step="any" min="-180" max="180" value="${value?.longitude ?? ""}" /></label>
            <button class="btn btn-ghost" type="button" data-apply>Use</button>
          </div>
        </details>
      </div>`,
    );
  }

  function set(location) {
    value = location;
    draw();
    onChange(value);
  }

  container.addEventListener("click", async (event) => {
    const locate = event.target.closest("[data-locate]");
    const city = event.target.closest("[data-city]");
    if (locate) {
      locate.disabled = true;
      locate.classList.add("is-busy");
      try {
        set(await currentPosition());
      } catch (error) {
        toast(error.message, "error");
        draw();
      }
    } else if (city) {
      set(CITY_PRESETS.find((preset) => preset.label === city.dataset.city));
    } else if (event.target.closest("[data-apply]")) {
      const latitude = Number($("[data-lat]", container).value);
      const longitude = Number($("[data-lng]", container).value);
      if (!isValidCoordinate(latitude, longitude) || $$("[data-lat], [data-lng]", container).some((i) => i.value === "")) {
        toast("Latitude must be between -90 and 90 and longitude between -180 and 180.", "error");
        return;
      }
      set({ label: "Custom location", latitude, longitude });
    }
  });

  draw();
  return {
    get value() {
      return value;
    },
    set,
  };
}
