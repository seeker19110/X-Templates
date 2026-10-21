export async function render(main, { h }) {
  main.replaceChildren(
    h("h1", null, "Ghép blueprint"),
    h("p", null, "Chọn hồ sơ, quy mô, ngành để xem trước số mục và nội dung markdown, tải file .md hoặc ghi BLUEPRINT.md sau bước xác nhận."),
    h("p", { class: "muted" }, "Màn này đang được xây dựng."),
  );
}
