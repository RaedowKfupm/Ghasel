/*
  GHASEL FRONTEND
  ----------------
  The only required connection setting is API_BASE below.
  If FastAPI runs on http://127.0.0.1:8000, leave it as-is.
*/
const API_BASE = window.GHASEL_API_BASE || "http://127.0.0.1:8000";

const state = {
  token: localStorage.getItem("ghasel_token"),
  user: JSON.parse(localStorage.getItem("ghasel_user") || "null"),
  currentPage: "dashboard",
};

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

const roleConfig = {
  customer: {
    nav: [["dashboard","⌂","Home"],["orders","▤","Orders"],["laundries","⌕","Laundries"],["profile","⚙","Profile"]],
  },
  laundry: {
    nav: [["dashboard","⌂","Home"],["business","▦","Business"],["profile","⚙","Profile"]],
  },
  manager: {
    nav: [["dashboard","⌂","Home"],["orders","▤","Orders"],["profile","⚙","Profile"]],
  },
  admin: {
    nav: [["dashboard","⌂","Home"],["admin","✓","Admin"],["profile","⚙","Profile"]],
  },
};

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (state.token) headers.Authorization = `Bearer ${state.token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 204) return null;

  let data = null;
  try { data = await response.json(); } catch { /* no JSON body */ }

  if (!response.ok) {
    if (response.status === 401 && state.token) {
      logout(false);
    }
    throw new Error(data?.detail || `Request failed (${response.status})`);
  }
  return data;
}

function toast(message, type = "success") {
  const el = $("#toast");
  el.textContent = message;
  el.className = `toast ${type === "error" ? "error" : ""} show`;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove("show"), 3000);
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
}

function initials(name = "G") {
  return name.trim().split(/\s+/).slice(0,2).map(x => x[0]?.toUpperCase()).join("") || "G";
}

function fmtDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, { dateStyle:"medium", timeStyle:"short" }).format(new Date(value));
}

function badge(status) {
  return `<span class="badge ${escapeHtml(status)}">${escapeHtml(status)}</span>`;
}

function persistSession(data) {
  state.token = data.access_token;
  state.user = { name:data.name, email:data.email, role:data.role };
  localStorage.setItem("ghasel_token", state.token);
  localStorage.setItem("ghasel_user", JSON.stringify(state.user));
}

function logout(showMessage = true) {
  state.token = null; state.user = null;
  localStorage.removeItem("ghasel_token");
  localStorage.removeItem("ghasel_user");
  $("#appView").classList.add("hidden");
  $("#authView").classList.remove("hidden");
  if (showMessage) toast("Signed out");
}

async function hydrateUser() {
  if (!state.token) return false;
  try {
    const user = await api("/users/me");
    state.user = user;
    localStorage.setItem("ghasel_user", JSON.stringify(user));
    return true;
  } catch {
    return false;
  }
}

function buildNavigation() {
  const role = state.user?.role || "customer";
  const nav = roleConfig[role]?.nav || roleConfig.customer.nav;
  const html = nav.map(([id, icon, label]) =>
    `<button class="nav-item ${state.currentPage===id?"active":""}" data-page="${id}">
       <span class="nav-symbol">${icon}</span><span>${label}</span>
     </button>`).join("");
  $("#desktopNav").innerHTML = html;
  $("#mobileNav").innerHTML = html;
  $$("[data-page]").forEach(btn => btn.addEventListener("click", () => showPage(btn.dataset.page)));
}

function updateIdentityUI() {
  const user = state.user || {};
  $("#sidebarName").textContent = user.name || "User";
  $("#sidebarRole").textContent = user.role || "";
  $("#sidebarAvatar").textContent = initials(user.name);
  $("#mobileProfileBtn").textContent = initials(user.name);
  $("#profileAvatar").textContent = initials(user.name);
}

function showPage(page) {
  state.currentPage = page;
  $$(".page").forEach(p => p.classList.add("hidden"));
  $(`#${page}Page`)?.classList.remove("hidden");
  $$("[data-page]").forEach(b => b.classList.toggle("active", b.dataset.page === page));
  if (page === "orders") loadOrders();
  if (page === "profile") loadProfile();
  if (page === "business") renderBusiness();
  if (page === "admin") renderAdmin();
}

async function enterApp() {
  $("#authView").classList.add("hidden");
  $("#appView").classList.remove("hidden");
  updateIdentityUI();
  buildNavigation();
  renderDashboard();
  showPage("dashboard");
}

function renderDashboard() {
  const user = state.user;
  const role = user.role;
  let content = "";

  if (role === "customer") {
    content = `
      <div class="hero">
        <span class="eyebrow">Customer dashboard</span>
        <h1>Fresh laundry, without the friction.</h1>
        <p>Create an order with a branch, then follow its lifecycle from pending to completed.</p>
        <div class="hero-actions">
          <button class="btn btn-primary" onclick="showPage('laundries')">Find a laundry</button>
          <button class="btn btn-secondary" onclick="showPage('orders')">My orders</button>
        </div>
      </div>
      <div class="section-head"><h2>Quick actions</h2></div>
      <div class="stats-grid">
        ${quickCard("⌕","Find laundry","Browse a company and its branches","laundries")}
        ${quickCard("+","Create order","Select a branch first","laundries")}
        ${quickCard("▤","Track orders","See current order states","orders")}
        ${quickCard("⚙","Account","Update your information","profile")}
      </div>`;
  } else if (role === "laundry") {
    content = `
      <div class="hero">
        <span class="eyebrow">Laundry owner</span>
        <h1>Run your laundry network from one place.</h1>
        <p>Submit your company for approval, create branches, and provision branch managers.</p>
        <div class="hero-actions"><button class="btn btn-primary" onclick="showPage('business')">Manage business</button></div>
      </div>
      <div class="code-note">Ghasel V1 intentionally keeps business operations focused: company approval, branches, managers, and orders. Ratings, ETA and geospatial discovery belong to V2.</div>`;
  } else if (role === "manager") {
    content = `
      <div class="hero">
        <span class="eyebrow">Branch operations</span>
        <h1>Keep every order moving.</h1>
        <p>Browse open orders and move your branch’s orders through the lifecycle.</p>
        <div class="hero-actions"><button class="btn btn-primary" onclick="showPage('orders')">Manage orders</button></div>
      </div>`;
  } else {
    content = `
      <div class="hero">
        <span class="eyebrow">Platform administration</span>
        <h1>Review the marketplace.</h1>
        <p>Approve laundry applications and inspect registered users.</p>
        <div class="hero-actions"><button class="btn btn-primary" onclick="showPage('admin')">Open admin</button></div>
      </div>`;
  }
  $("#dashboardPage").innerHTML = content;
}

function quickCard(icon, title, text, page) {
  return `<button class="stat-card" style="text-align:left;border:1px solid var(--border);cursor:pointer" onclick="showPage('${page}')">
    <strong style="font-size:1.25rem">${icon} ${title}</strong><span>${text}</span>
  </button>`;
}

async function loadOrders() {
  const role = state.user.role;
  const root = $("#ordersContent");
  root.innerHTML = `<div class="list"><div class="skeleton"></div><div class="skeleton"></div></div>`;

  if (role === "customer") {
    try {
      const orders = await api("/orders/?page=1&limit=50");
      root.innerHTML = `
        <div class="section-head"><h2>My orders</h2><button class="btn btn-primary" onclick="showPage('laundries')">+ New order</button></div>
        ${orders.length ? `<div class="list">${orders.map(orderCard).join("")}</div>` : empty("No orders yet","Choose a laundry branch and create your first order.")}`;
    } catch (e) { root.innerHTML = errorBox(e.message); }
  } else if (role === "manager") {
    try {
      const orders = await api("/orders/?page=1&limit=50");
      root.innerHTML = `
        <div class="section-head"><h2>Open and branch orders</h2><button class="btn btn-secondary" id="refreshManagerOrders">Refresh</button></div>
        <label>Filter orders<input id="managerOrderFilter" type="search" placeholder="Order ID or details" /></label>
        <div id="managerOrderList" class="list" style="margin-top:14px"></div>`;
      const renderManagerOrders = () => {
        const query = $("#managerOrderFilter").value.trim().toLowerCase();
        const visibleOrders = orders.filter(order =>
          String(order.id).includes(query) || order.details.toLowerCase().includes(query)
        );
        $("#managerOrderList").innerHTML = visibleOrders.length
          ? visibleOrders.map(managerOrderCard).join("")
          : empty("No matching orders", "Try another search or refresh the list.");
      };
      $("#managerOrderFilter").addEventListener("input", renderManagerOrders);
      $("#refreshManagerOrders").addEventListener("click", loadOrders);
      $("#managerOrderList").addEventListener("click", event => {
        const button = event.target.closest("[data-order-id]");
        if (button) updateManagerOrder(Number(button.dataset.orderId), button.dataset.nextStatus);
      });
      renderManagerOrders();
    } catch (error) {
      root.innerHTML = errorBox(error.message);
    }
  } else {
    root.innerHTML = empty("No order view for this role","Use the navigation for your role-specific workflow.");
  }
}

function orderCard(o) {
  const statuses = ["pending","accepted","delivering","completed"];
  const idx = statuses.indexOf(o.status);
  return `<article class="order-card">
    <div class="row">
      <div>
        <div class="row-start"><strong>Order #${o.id}</strong>${badge(o.status)}</div>
        <div class="meta"><span>${o.branch_id ? `Branch #${o.branch_id}` : "Waiting for a branch"}</span><span>${fmtDate(o.created_at)}</span></div>
      </div>
      <button class="btn btn-secondary" onclick="openOrder(${o.id})">Details</button>
    </div>
    <p style="margin:16px 0 0">${escapeHtml(o.details)}</p>
    ${o.status === "open" ? `<p class="muted" style="margin:12px 0 0">Branch operators can see and claim this request.</p>` : `<div class="timeline">${statuses.map((s,i)=>`<div class="timeline-step ${i<=idx?"done":""}">${s}</div>`).join("")}</div>`}
  </article>`;
}

function managerOrderCard(order) {
  const nextStatus = {
    open: "accepted",
    pending: "accepted",
    accepted: "delivering",
    delivering: "completed",
  }[order.status];
  const actionLabel = {
    accepted: "Accept order",
    delivering: "Start delivery",
    completed: "Complete order",
  }[nextStatus];
  return `<article class="order-card">
    <div class="row"><div><div class="row-start"><strong>Order #${order.id}</strong>${badge(order.status)}</div>
      <div class="meta"><span>${order.branch_id ? `Branch #${order.branch_id}` : "Open to branches"}</span><span>${fmtDate(order.created_at)}</span></div></div>
      ${nextStatus ? `<button class="btn btn-primary" data-order-id="${order.id}" data-next-status="${nextStatus}">${actionLabel}</button>` : ""}
    </div>
    <p style="margin:16px 0 0">${escapeHtml(order.details)}</p>
  </article>`;
}

async function openOrder(id) {
  try {
    const o = await api(`/orders/${id}`);
    openModal(`
      <div class="modal-head"><div><span class="eyebrow">Order</span><h2>#${o.id}</h2></div><button class="icon-btn" onclick="closeModal()">×</button></div>
      <div class="row">${badge(o.status)}<span class="muted">${fmtDate(o.created_at)}</span></div>
      <p style="margin-top:20px">${escapeHtml(o.details)}</p>
      <div class="detail-grid">
        <div class="detail"><span>Branch</span><strong>#${o.branch_id}</strong></div>
        <div class="detail"><span>Accepted</span><strong>${fmtDate(o.accepted_at)}</strong></div>
        <div class="detail"><span>Completed</span><strong>${fmtDate(o.completed_at)}</strong></div>
      </div>`);
  } catch(e) { toast(e.message,"error"); }
}

async function updateManagerOrder(id, status) {
  try {
    await api(`/orders/${id}/status`, { method:"PATCH", body:JSON.stringify({status}) });
    toast(`Order #${id} moved to ${status}`);
    await loadOrders();
  } catch(e) { toast(e.message,"error"); }
}

async function loadLaundry(id) {
  const root = $("#laundryResult");
  root.innerHTML = `<div class="skeleton"></div>`;
  try {
    const [laundry, branches] = await Promise.all([
      api(`/laundries/${id}`),
      api(`/laundries/${id}/branches?page=1&limit=50`)
    ]);
    root.classList.remove("empty-card");
    root.innerHTML = `
      <div class="row">
        <div><span class="eyebrow">Laundry #${laundry.id}</span><h2>${escapeHtml(laundry.company_name || "Laundry")}</h2></div>
        <span class="badge approved">${branches.length} branch${branches.length===1?"":"es"}</span>
      </div>
      ${state.user.role === "customer" ? `<div class="section-head"><p class="muted">Prefer an open request?</p><button class="btn btn-secondary" onclick="openCreateOrder(null, 'Open request')">Offer to branches</button></div>` : ""}
      <div class="section-head"><h2>Branches</h2></div>
      ${branches.length ? `<div class="list">${branches.map(branchCard).join("")}</div>` : empty("No branches","This laundry has no branches yet.")}`;
  } catch(e) {
    root.innerHTML = errorBox(e.message);
  }
}

function branchCard(b) {
  return `<article class="branch-card">
    <div class="row">
      <div><strong>${escapeHtml(b.branch_name || `Branch #${b.id}`)}</strong>
        <div class="meta"><span>${escapeHtml(b.branch_address)}</span><span>${escapeHtml(b.phone)}</span></div>
      </div>
      ${state.user.role === "customer" ? `<button class="btn btn-primary" onclick='openCreateOrder(${JSON.stringify(b.id)}, ${JSON.stringify(b.branch_name || "Branch")})'>Order</button>` : ""}
    </div>
  </article>`;
}

function openCreateOrder(branchId, branchName) {
  openModal(`
    <div class="modal-head"><div><span class="eyebrow">New order</span><h2>${escapeHtml(branchName)}</h2></div><button class="icon-btn" onclick="closeModal()">×</button></div>
    <form id="createOrderForm" class="stack">
      <input type="hidden" id="createOrderBranch" value="${branchId ?? ""}" />
      <label>Laundry details<textarea id="createOrderDetails" required placeholder="Example: 3 shirts, 2 trousers. Wash and iron."></textarea></label>
      <div class="code-note">${branchId ? "This order will go directly to the selected branch." : "All branch operators can see and claim this open request in V1; nearby matching comes later."}</div>
      <button class="btn btn-primary" type="submit">Create order</button>
    </form>`);
  $("#createOrderForm").addEventListener("submit", createOrder);
}

async function createOrder(e) {
  e.preventDefault();
  try {
    await api("/orders/", { method:"POST", body:JSON.stringify({
      branch_id:$("#createOrderBranch").value ? Number($("#createOrderBranch").value) : null,
      details:$("#createOrderDetails").value.trim()
    })});
    closeModal(); toast("Order created");
    showPage("orders");
  } catch(e) { toast(e.message,"error"); }
}

async function renderBusiness() {
  const root = $("#businessPage");
  root.innerHTML = `<div class="skeleton"></div>`;
  try {
    const user = await api("/users/me");
    state.user = { ...state.user, ...user };
    localStorage.setItem("ghasel_user", JSON.stringify(state.user));
    updateIdentityUI();
    root.innerHTML = `
      <div class="page-head"><div><span class="eyebrow">Business</span><h1>Laundry management</h1><p class="muted">Company approval, branches, and branch operators.</p></div></div>
      ${user.laundry_id ? businessApproved(user.laundry_id) : businessPending()}`;
    if (user.laundry_id) {
      loadOwnerBranches(user.laundry_id);
      return;
    }

    $("#laundryRequestForm").addEventListener("submit", async event => {
      event.preventDefault();
      try {
        const request = await api("/laundries/", {
          method: "POST",
          body: JSON.stringify({ company_name: $("#companyName").value.trim() }),
        });
        root.innerHTML = `
          <div class="page-head"><div><span class="eyebrow">Business</span><h1>Application submitted</h1><p class="muted">Your request for ${escapeHtml(request.company_name)} is ${escapeHtml(request.status)}. This page will refresh your access after approval.</p></div></div>`;
        toast("Laundry application submitted");
      } catch (error) {
        toast(error.message, "error");
      }
    });
  } catch (error) {
    root.innerHTML = errorBox(error.message);
  }
}

function businessPending() {
  return `<div class="two-col">
    <form id="laundryRequestForm" class="card stack">
      <div><h3>Register your laundry company</h3><p class="muted">Submit a company application for admin approval.</p></div>
      <label>Company name<input id="companyName" required placeholder="Ghasel Clean Co." /></label>
      <button class="btn btn-primary" type="submit">Submit application</button>
    </form>
    <div class="card"><h3>What happens next?</h3><p class="muted">An administrator approves the request. Your user is then linked to the new laundry company, after which you can create branches and managers.</p></div>
  </div>`;
}

function businessApproved(id) {
  return `<div class="stats-grid">
    <div class="stat-card"><span>Company ID</span><strong>#${id}</strong></div>
    <button class="stat-card" onclick="openBranchForm(${id})" style="text-align:left;cursor:pointer"><span>Business action</span><strong style="font-size:1.05rem">+ Add branch</strong></button>
    <button class="stat-card" onclick="openManagerForm(${id})" style="text-align:left;cursor:pointer"><span>Team action</span><strong style="font-size:1.05rem">+ Add manager</strong></button>
  </div>
  <div class="section-head"><h2>Your branches</h2><button class="btn btn-secondary" onclick="loadOwnerBranches(${id})">Refresh</button></div>
  <div id="ownerBranches" class="list"><div class="skeleton"></div></div>`;
}

async function loadOwnerBranches(id) {
  try {
    const branches = await api(`/laundries/${id}/branches?page=1&limit=50`);
    $("#ownerBranches").innerHTML = branches.length ? branches.map(branchCard).join("") : empty("No branches yet","Create the first physical branch for your laundry.");
  } catch(e) { $("#ownerBranches").innerHTML = errorBox(e.message); }
}

function openBranchForm(laundryId) {
  openModal(`
    <div class="modal-head"><h2>Create branch</h2><button class="icon-btn" onclick="closeModal()">×</button></div>
    <form id="branchForm" class="stack">
      <label>Branch name<input id="branchName" required /></label>
      <label>Address<input id="branchAddress" required /></label>
      <label>Phone<input id="branchPhone" required /></label>
      <button class="btn btn-primary" type="submit">Create branch</button>
    </form>`);
  $("#branchForm").addEventListener("submit", async e => {
    e.preventDefault();
    try {
      await api(`/laundries/${laundryId}/branches`, {method:"POST",body:JSON.stringify({
        branch_name:$("#branchName").value, branch_address:$("#branchAddress").value, phone:$("#branchPhone").value
      })});
      closeModal(); toast("Branch created"); loadOwnerBranches(laundryId);
    } catch(e) { toast(e.message,"error"); }
  });
}

function openManagerForm(laundryId) {
  openModal(`
    <div class="modal-head"><h2>Create branch manager</h2><button class="icon-btn" onclick="closeModal()">×</button></div>
    <form id="managerForm" class="stack">
      <label>Name<input id="managerName" required /></label>
      <label>Email<input id="managerEmail" type="email" required /></label>
      <label>Password<input id="managerPassword" type="password" required /></label>
      <label>Branch ID<input id="managerBranch" type="number" min="1" required /></label>
      <button class="btn btn-primary" type="submit">Create manager</button>
    </form>`);
  $("#managerForm").addEventListener("submit", async e => {
    e.preventDefault();
    try {
      await api(`/laundries/${laundryId}/managers`, {method:"POST",body:JSON.stringify({
        name:$("#managerName").value,email:$("#managerEmail").value,password:$("#managerPassword").value,branch_id:Number($("#managerBranch").value)
      })});
      closeModal(); toast("Manager created"); loadOwnerBranches(laundryId);
    } catch(e) { toast(e.message,"error"); }
  });
}

async function renderAdmin() {
  const root = $("#adminPage");
  root.innerHTML = `<div class="page-head"><div><span class="eyebrow">Administration</span><h1>Marketplace review</h1><p class="muted">Approve laundry applications and inspect users.</p></div></div>
  <div class="section-head"><h2>Laundry applications</h2><button class="btn btn-secondary" onclick="renderAdmin()">Refresh</button></div>
  <div id="adminRequests" class="list"><div class="skeleton"></div></div>
  <div class="section-head"><h2>Users</h2></div>
  <div id="adminUsers" class="list"><div class="skeleton"></div></div>`;
  try {
    const [requests, users] = await Promise.all([
      api("/laundries/requests?page=1&limit=50"),
      api("/users/?page=1&limit=50")
    ]);
    $("#adminRequests").innerHTML = requests.length ? requests.map(r => `
      <article class="request-card"><div class="row">
        <div><div class="row-start"><strong>${escapeHtml(r.company_name)}</strong>${badge(r.status)}</div><div class="meta"><span>Owner #${r.owner_id}</span><span>${fmtDate(r.created_at)}</span></div></div>
        ${r.status==="pending"?`<button class="btn btn-primary" onclick="approveRequest(${r.id})">Approve</button>`:""}
      </div></article>`).join("") : empty("No applications","No laundry applications are waiting.");
    $("#adminUsers").innerHTML = users.length ? users.map(u => `
      <article class="request-card"><div class="row"><div><strong>${escapeHtml(u.name)}</strong><div class="meta"><span>${escapeHtml(u.email)}</span><span>${escapeHtml(u.role)}</span></div></div><span class="badge">${u.role}</span></div></article>`).join("") : empty("No users","No users found.");
  } catch(e) { root.insertAdjacentHTML("beforeend", errorBox(e.message)); }
}

async function approveRequest(id) {
  try { await api(`/laundries/requests/${id}/approve`, {method:"POST"}); toast("Laundry approved"); renderAdmin(); }
  catch(e) { toast(e.message,"error"); }
}

async function loadProfile() {
  try {
    const u = await api("/users/me");
    state.user = {...state.user,...u};
    localStorage.setItem("ghasel_user",JSON.stringify(state.user));
    updateIdentityUI();
    $("#profileName").value = u.name || "";
    $("#profileEmail").value = u.email || "";
    $("#profilePhone").value = u.phone || "";
    $("#profileAddress").value = u.address || "";
    const isCustomer = u.role === "customer";
    $("#profilePhone").closest("label").classList.toggle("hidden", !isCustomer);
    $("#profileAddress").closest("label").classList.toggle("hidden", !isCustomer);
    $("#profilePhone").required = isCustomer && !u.phone;
  } catch(e) { toast(e.message,"error"); }
}

function openModal(html) {
  $("#modal").innerHTML = html;
  $("#modalBackdrop").classList.remove("hidden");
}
function closeModal() { $("#modalBackdrop").classList.add("hidden"); $("#modal").innerHTML=""; }
window.closeModal = closeModal;
window.showPage = showPage;
window.openOrder = openOrder;
window.openCreateOrder = openCreateOrder;
window.openBranchForm = openBranchForm;
window.openManagerForm = openManagerForm;
window.loadOwnerBranches = loadOwnerBranches;
window.approveRequest = approveRequest;
window.renderAdmin = renderAdmin;

function empty(title,text) {
  return `<div class="card empty-card"><div class="empty-icon">○</div><h3>${escapeHtml(title)}</h3><p class="muted">${escapeHtml(text)}</p></div>`;
}
function errorBox(text) { return `<div class="card"><strong>Could not load this section</strong><p class="muted" style="margin:8px 0 0">${escapeHtml(text)}</p></div>`; }

$("#modalBackdrop").addEventListener("click", e => { if (e.target === $("#modalBackdrop")) closeModal(); });
$("#logoutBtn").addEventListener("click", () => logout());
$("#mobileProfileBtn").addEventListener("click", () => showPage("profile"));
$("#refreshOrdersBtn").addEventListener("click", loadOrders);

$$(".auth-tab").forEach(tab => tab.addEventListener("click", () => {
  $$(".auth-tab").forEach(x=>x.classList.toggle("active",x===tab));
  $("#loginForm").classList.toggle("hidden",tab.dataset.authTab!=="login");
  $("#registerForm").classList.toggle("hidden",tab.dataset.authTab!=="register");
}));

$("#loginForm").addEventListener("submit", async e => {
  e.preventDefault();
  try {
    const data = await api("/auth/login", {method:"POST",body:JSON.stringify({email:$("#loginEmail").value,password:$("#loginPassword").value})});
    persistSession(data);
    await hydrateUser();
    await enterApp();
    toast("Welcome back");
  } catch(e) { toast(e.message,"error"); }
});

$("#registerForm").addEventListener("submit", async e => {
  e.preventDefault();
  try {
    const data = await api("/auth/register", {method:"POST",body:JSON.stringify({
      name:$("#registerName").value,email:$("#registerEmail").value,password:$("#registerPassword").value,role:$("#registerRole").value
    })});
    persistSession(data);
    await hydrateUser();
    await enterApp();
    toast("Account created");
  } catch(e) { toast(e.message,"error"); }
});

$("#profileForm").addEventListener("submit", async e => {
  e.preventDefault();
  const payload = {
    name:$("#profileName").value.trim(),
    email:$("#profileEmail").value.trim(),
  };
  if (state.user.role === "customer") {
    const phone = $("#profilePhone").value.trim();
    if (phone) payload.phone = phone;
    payload.address = $("#profileAddress").value.trim() || null;
  }
  try {
    await api("/users/me",{method:"PATCH",body:JSON.stringify(payload)});
    await loadProfile(); buildNavigation(); renderDashboard(); toast("Profile updated");
  } catch(e) { toast(e.message,"error"); }
});

$("#laundryLookupForm").addEventListener("submit", e => {
  e.preventDefault(); loadLaundry(Number($("#laundryLookupId").value));
});

(async function boot() {
  if (state.token && await hydrateUser()) await enterApp();
  else logout(false);
})();
