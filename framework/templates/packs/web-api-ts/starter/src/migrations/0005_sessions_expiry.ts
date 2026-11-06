// 0005 — chỉ mục cho dọn phiên hết hạn (AUD-SEC-532): `login` xoá phiên hết hạn theo user, `purgeExpiredSessions`
// xoá theo hạn. Không có chỉ mục thì mỗi lần đăng nhập quét cả bảng `sessions`. CREATE INDEX (không CONCURRENTLY — migration
// chạy trong transaction) chặn ghi `sessions` trong lúc dựng: bảng lớn ở môi trường thật → tách migration dựng CONCURRENTLY.
import { type Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    SET LOCAL lock_timeout = '5s';
    SET LOCAL statement_timeout = '60s';
    CREATE INDEX sessions_user_expires ON sessions (user_id, expires_at);
    CREATE INDEX sessions_expires ON sessions (expires_at);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    SET LOCAL lock_timeout = '5s';
    SET LOCAL statement_timeout = '60s';
    DROP INDEX sessions_expires;
    DROP INDEX sessions_user_expires;
  `.execute(db);
}
