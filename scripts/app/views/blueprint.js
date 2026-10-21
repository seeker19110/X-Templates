export async function render(main, { h }) {
  main.replaceChildren(
    h("h1", null, "Tiến độ blueprint"),
    h("p", null, "Thanh tiến độ tổng và theo module, danh sách MUST chưa đạt có lọc, lệnh blueprint-status --strict để chép."),
    h("p", { class: "muted" }, "Màn này đang được xây dựng."),
  );
}
