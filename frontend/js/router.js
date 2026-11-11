// Hash-based navigation with a per-role set of pages.
import { $, html, render } from "./dom.js";
import { icon } from "./icons.js";

let routes = [];
let mount = null;

export function configureRoutes(roleRoutes, root) {
  routes = roleRoutes;
  mount = root;
  renderNavigation();
}

export const currentPath = () => window.location.hash.replace(/^#\/?/, "").split("?")[0] || routes[0]?.path;

export function navigate(path) {
  if (currentPath() === path) showCurrentRoute();
  else window.location.hash = `#/${path}`;
}

function renderNavigation() {
  const links = routes.map(
    (route) => html`<a class="nav-link" href="#/${route.path}" data-path="${route.path}">${icon(route.icon)}<span>${route.label}</span></a>`,
  );
  render($("#sidebar-nav"), links);
  render($("#bottom-nav"), links);
}

export async function showCurrentRoute() {
  if (!mount || !routes.length) return;
  const route = routes.find((r) => r.path === currentPath()) ?? routes[0];
  document.title = `${route.label} · Ghasel`;
  document.querySelectorAll(".nav-link[data-path]").forEach((link) => {
    if (link.dataset.path === route.path) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });

  const page = document.createElement("div");
  page.className = "content";
  mount.replaceChildren(page);
  window.scrollTo({ top: 0 });
  await route.render(page);
}

window.addEventListener("hashchange", showCurrentRoute);
