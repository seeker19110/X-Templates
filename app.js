const routes = {
  "": ["Tổng quan", { render: overview }],
  catalog: ["Thư viện yêu cầu", () => import("./views/catalog.js")],
  blueprint: ["Tiến độ blueprint", () => import("./views/blueprint.js")],
  plan: ["Kế hoạch", () => import("./views/plan.js")],
};
const files = new Map();

function h(tag, attrs, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === false || value == null) continue;
    element.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat()) {
    if (child == null || child === false) continue;
    element.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return element;
}

function readData(name) {
  if (!files.has(name)) {
    const operation = fetch(`./data/${name}.json`).then((res) => {
      if (!res.ok) throw new Error(`Không tải được dữ liệu (${res.status}).`);
      return res.json();
    }).catch((error) => {
      files.delete(name);
      throw error;
    });
    files.set(name, operation);
  }
  return files.get(name);
}

function findRequirements(modules, term) {
  const query = term.trim().toLocaleLowerCase("vi");
  const hits = [];
  for (const { items } of Object.values(modules)) {
    for (const item of items) {
      const words = [item.id, item.text, item.check, item.source];
      if (!words.some((text) => text.toLocaleLowerCase("vi").includes(query))) continue;
      if (hits.length === 200) return { hits, truncated: true };
      hits.push(item);
    }
  }
  return { hits, truncated: false };
}

async function api(request) {
  const { pathname, searchParams } = new URL(request, location.origin);
  switch (pathname) {
    case "/api/catalog": {
      const term = searchParams.get("q");
      return term ? findRequirements(await readData("modules"), term) : readData("catalog");
    }
    case "/api/catalog/module": {
      const modules = await readData("modules");
      const name = searchParams.get("rel");
      if (Object.hasOwn(modules, name)) return modules[name];
      break;
    }
    case "/api/blueprint": return readData("blueprint");
    case "/api/plans": return readData("plans");
    case "/api/plan": return readData("plan");
  }
  throw Object.assign(new Error("Không tìm thấy dữ liệu."), { status: 404 });
}

function loading(element, message = "Đang tải…") {
  element.replaceChildren(h("p", { class: "state loading", role: "status" }, message));
}

function empty(element, message) {
  element.replaceChildren(h("p", { class: "state empty" }, message));
}

function error(element, failure, retry) {
  const box = h("div", { class: "state error", role: "alert" },
    h("p", null, failure.message || "Không tải được trang."));
  if (typeof retry === "function") {
    const button = h("button", { type: "button" }, "Thử lại");
    button.addEventListener("click", retry);
    box.append(button);
  }
  element.replaceChildren(box);
}

function metric(href, value, name, description) {
  return h("a", { class: "card", href },
    h("h2", null, name),
    h("p", { class: "num" }, value),
    h("p", { class: "label" }, description));
}

async function overview(page) {
  const current = await readData("overview");
  const root = `${current.repo}/tree/${current.commit}`;
  const locale = new Intl.NumberFormat("vi-VN");
  page.replaceChildren(
    h("section", { class: "intro", "aria-labelledby": "project-name" },
      h("p", { class: "version" }, `Khung ${current.version}`),
      h("h1", { id: "project-name" }, "X-Templates"),
      h("p", { class: "summary" }, "Khung tham chiếu để lập yêu cầu, ghép blueprint và kiểm tra tiến độ dự án phần mềm."),
      h("div", { class: "project-links" },
        h("a", { class: "primary-link", href: `${root}/README.md` }, "Đọc hướng dẫn"),
        h("a", { href: root }, "Xem mã nguồn"))),
    h("section", { class: "cards", "aria-label": "Dữ liệu của khung" },
      metric("#/catalog", locale.format(current.requirements), "Thư viện yêu cầu", `${current.modules} module`),
      metric("#/blueprint", `${current.must_done}/${current.must_total}`, "Tiến độ blueprint", "Yêu cầu MUST đã đạt"),
      metric("#/plan", locale.format(current.tasks_open), "Kế hoạch phát triển", "Việc còn mở trong kế hoạch factory")),
    h("footer", { class: "snapshot" }, "Dữ liệu từ ",
      h("a", { href: `${current.repo}/commit/${current.commit}` }, "main · " + current.commit.slice(0, 8)),
      h("a", { href: `${current.repo}/commits/main/` }, "Lịch sử thay đổi")),
  );
}

async function render(moveFocus = false) {
  const main = document.getElementById("main");
  const status = document.getElementById("status");
  const path = location.hash.slice(2);
  const route = location.hash.startsWith("#/") && Object.hasOwn(routes, path) ? routes[path] : null;
  for (const link of document.querySelectorAll('nav a[href^="#/"]')) {
    if (route && link.hash === location.hash) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }

  const page = h("div", null);
  main.replaceChildren(page);
  if (moveFocus) main.focus();
  if (!route) {
    document.title = "Không tìm thấy — X-Templates";
    empty(page, "Không tìm thấy trang này.");
    return;
  }

  const [title, getView] = route;
  document.title = `${title} — X-Templates`;
  loading(page);
  try {
    const view = typeof getView === "function" ? await getView() : getView;
    await view.render(page, { api, h, loading, empty, error });
    if (page.isConnected) status.textContent = `Đã mở ${title}`;
  } catch (failure) {
    error(page, failure, () => render(true));
  }
}

window.addEventListener("hashchange", () => {
  if (location.hash.startsWith("#/")) render(true);
});
if (!location.hash || location.hash === "#main") history.replaceState(null, "", "#/");
render();
