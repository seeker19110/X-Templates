export async function render(main, { h }) {
  main.replaceChildren(
    h("h1", null, "Vòng tự động"),
    h("p", null, "Việc cần người, trạng thái vòng tự động, danh sách quyết định D-NNN có tìm kiếm và ADR theo trạng thái."),
    h("p", { class: "muted" }, "Màn này đang được xây dựng."),
  );
}
