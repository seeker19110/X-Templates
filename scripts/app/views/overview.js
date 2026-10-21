export async function render(main, { api, h, loading, error }) {
  const info = h("div", null);
  main.replaceChildren(
    h("h1", null, "Tổng quan"),
    h("p", null, "Thẻ số về blueprint, task mở, việc chờ người và trạng thái vòng; mỗi thẻ dẫn sang màn chi tiết."),
    h("p", { class: "muted" }, "Màn này đang được xây dựng."),
    info,
  );
  async function load() {
    loading(info);
    try {
      const data = await api("/api/health");
      info.replaceChildren(
        h("div", { class: "card" }, h("div", { class: "num" }, String(data.version)), h("div", { class: "label" }, "Phiên bản khung")),
      );
    } catch (e) {
      error(info, e, load);
    }
  }
  await load();
}
