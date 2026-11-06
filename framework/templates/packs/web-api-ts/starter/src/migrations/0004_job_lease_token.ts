// 0004 — mã lease mỗi lần claim (AUD-DATA-006): `complete`/`fail` khớp `lease_token` thay vì `locked_by`. Khớp theo
// `locked_by` thì cùng workerId claim lại job hết lease → handler của lần chạy cũ reset/hoàn tất lần chạy mới.
// Cột cho phép NULL, không DEFAULT: ADD COLUMN chỉ đổi metadata (khoá ngắn). Job đang `running` do bản cũ claim có
// token NULL — không ai hoàn tất được bằng token, lease hết hạn thì được claim lại (at-least-once như worker chết).
import { type Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    SET LOCAL lock_timeout = '5s';
    SET LOCAL statement_timeout = '60s';
    ALTER TABLE jobs ADD COLUMN lease_token uuid;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    SET LOCAL lock_timeout = '5s';
    SET LOCAL statement_timeout = '60s';
    ALTER TABLE jobs DROP COLUMN lease_token;
  `.execute(db);
}
