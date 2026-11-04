import { defineConfig } from "vitest/config";

// Mỗi file test tự tạo cơ sở dữ liệu riêng (test/helpers.ts) nên chạy song song an toàn; cần DATABASE_URL tới Postgres
// thật (vai trò được CREATE DATABASE). Thiếu biến → test đỏ, không bỏ qua (cổng rỗng là đỏ).
export default defineConfig({
  test: {
    include: ["test/**/*.test.ts"],
    testTimeout: 30_000,
    hookTimeout: 60_000,
  },
});
