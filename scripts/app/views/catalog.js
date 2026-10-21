export async function render(main, { h }) {
  main.replaceChildren(
    h("h1", null, "Thư viện yêu cầu"),
    h("p", null, "Cây mảng và module với số mục MUST/SHOULD/MAY; chọn module để xem từng mục (ID, mức, quy mô, nội dung, Kiểm, Nguồn) và tìm theo ID hoặc chữ."),
    h("p", { class: "muted" }, "Màn này đang được xây dựng."),
  );
}
