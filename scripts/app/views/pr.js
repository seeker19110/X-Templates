export async function render(main, { h }) {
  main.replaceChildren(
    h("h1", null, "PR"),
    h("p", null, "Bảng PR đang mở (làn, hành động kế, lý do), số đo lead time và CI; chỉ đọc, không có nút merge."),
    h("p", { class: "muted" }, "Màn này đang được xây dựng."),
  );
}
