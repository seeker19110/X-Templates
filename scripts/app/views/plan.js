export async function render(main, { h }) {
  main.replaceChildren(
    h("h1", null, "Kế hoạch"),
    h("p", null, "Chọn PLAN, xem bảng task theo lát với cột Đợt, tầng executor, Gate chép được và mục Bị chặn kèm lý do."),
    h("p", { class: "muted" }, "Màn này đang được xây dựng."),
  );
}
