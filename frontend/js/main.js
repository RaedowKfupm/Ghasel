// Entry point: restore the session, then show the sign-in screen or the role's app.
import { api } from "./api.js";
import { $, html, render } from "./dom.js";
import { toast } from "./feedback.js";
import { initials } from "./format.js";
import { icon } from "./icons.js";
import { configureRoutes, navigate, showCurrentRoute } from "./router.js";
import { session } from "./session.js";
import { renderAdmin } from "./pages/admin.js";
import { renderAuth } from "./pages/auth.js";
import { renderBusiness } from "./pages/business.js";
import { renderCustomerHome } from "./pages/customer-home.js";
import { renderCustomerOrders } from "./pages/customer-orders.js";
import { renderDiscover } from "./pages/discover.js";
import { renderMyBranch } from "./pages/my-branch.js";
import { renderOperations } from "./pages/operations.js";
import { renderProfile } from "./pages/profile.js";

const ROLE_LABEL = { customer: "Customer", laundry: "Laundry owner", manager: "Branch manager", admin: "Administrator" };

const profileRoute = { path: "profile", label: "Profile", icon: "user", render: (root) => renderProfile(root, { onUpdated: showIdentity }) };

const ROUTES = {
  customer: [
    { path: "home", label: "Home", icon: "home", render: renderCustomerHome },
    { path: "discover", label: "Discover", icon: "search", render: renderDiscover },
    { path: "orders", label: "Orders", icon: "orders", render: renderCustomerOrders },
    profileRoute,
  ],
  manager: [
    { path: "operations", label: "Orders", icon: "inbox", render: renderOperations },
    { path: "branch", label: "My branch", icon: "store", render: renderMyBranch },
    profileRoute,
  ],
  laundry: [{ path: "business", label: "Business", icon: "store", render: renderBusiness }, profileRoute],
  admin: [{ path: "admin", label: "Review", icon: "shield", render: renderAdmin }, profileRoute],
};

function showIdentity() {
  const { name, role } = session.user;
  $("#identity-avatar").textContent = initials(name);
  $("#topbar-profile").textContent = initials(name);
  $("#identity-name").textContent = name;
  $("#identity-role").textContent = ROLE_LABEL[role];
}

async function enterApp() {
  session.setUser(await api.users.me());
  render($("#auth-root"), "");
  $("#app-root").hidden = false;
  showIdentity();
  const routes = ROUTES[session.user.role];
  configureRoutes(routes, $("#page-root"));
  if (!routes.some((r) => window.location.hash === `#/${r.path}`)) navigate(routes[0].path);
  else showCurrentRoute();
}

function showSignIn() {
  $("#app-root").hidden = true;
  history.replaceState(null, "", window.location.pathname);
  renderAuth($("#auth-root"), async (token) => {
    session.start(token);
    try {
      await enterApp();
      toast(`Welcome, ${session.user.name.split(" ")[0]}`);
    } catch (error) {
      session.end();
      toast(error.message, "error");
    }
  });
}

render($("#sign-out"), html`${icon("logout")}<span>Sign out</span>`);
$("#sign-out").addEventListener("click", () => session.end());
session.onEnd(showSignIn);

(async function boot() {
  if (!session.token) return showSignIn();
  try {
    await enterApp();
  } catch (error) {
    // Keep the token if the API is merely unreachable; drop it if it was rejected.
    if (error.status === 0) {
      showSignIn();
      toast(error.message, "error");
    } else {
      session.end();
    }
  }
})();
