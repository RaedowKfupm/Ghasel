// Shared page scaffolding: header, async body with loading/error/retry handling.
import { $, html, render } from "../dom.js";
import { errorState, loading } from "../feedback.js";

export function pageHeader(eyebrow, title, description = "", actions = "") {
  return html`<div class="page-head">
    <div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1>${description ? html`<p>${description}</p>` : ""}</div>
    ${actions ? html`<div class="cluster">${actions}</div>` : ""}
  </div>`;
}

/**
 * Render `header` and an async body into `root`. `load()` fetches data and `view(data)`
 * returns the body template; `afterRender(body, data)` wires up events after each draw.
 * Returns a `reload()` function.
 */
export function asyncPage(root, { header, load, view, afterRender = () => {}, skeletonRows = 3 }) {
  render(root, html`${header}<div data-page-body></div>`);
  const body = $("[data-page-body]", root);

  async function reload({ quiet = false } = {}) {
    if (!quiet) render(body, loading(skeletonRows));
    try {
      const data = await load();
      // A fresh element per draw, so listeners added in afterRender never accumulate.
      const content = document.createElement("div");
      render(content, view(data));
      body.replaceChildren(content);
      afterRender(content, data);
    } catch (error) {
      render(body, errorState(error));
    }
  }

  body.addEventListener("click", (event) => {
    if (event.target.closest("[data-retry]")) reload();
  });
  reload();
  return reload;
}
