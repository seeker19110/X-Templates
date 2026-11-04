// Migration có thứ tự cố định (danh sách tĩnh, không quét thư mục). CLI: `node src/migrate.ts up|down|reset`.
import type { Kysely } from "kysely";
import { type Migration, Migrator, NO_MIGRATIONS } from "kysely/migration";
import { createDb } from "./db.ts";
import * as m0001 from "./migrations/0001_tenancy.ts";
import * as m0002 from "./migrations/0002_notes.ts";
import * as m0003 from "./migrations/0003_jobs.ts";

export const MIGRATIONS: Record<string, Migration> = {
  "0001_tenancy": m0001,
  "0002_notes": m0002,
  "0003_jobs": m0003,
};

function migrator(db: Kysely<unknown>): Migrator {
  return new Migrator({ db, provider: { getMigrations: async () => MIGRATIONS } });
}

export type Direction = "up" | "down" | "reset";

export async function migrate(db: Kysely<unknown>, direction: Direction): Promise<string[]> {
  const m = migrator(db);
  const run = {
    up: () => m.migrateToLatest(),
    down: () => m.migrateDown(),
    reset: () => m.migrateTo(NO_MIGRATIONS),
  };
  const { error, results } = await run[direction]();
  if (error) {
    throw error instanceof Error ? error : new Error(String(error));
  }
  return (results ?? []).map((r) => `${r.direction} ${r.migrationName} ${r.status}`);
}

async function main(argv: string[]): Promise<number> {
  const direction = argv[0] ?? "up";
  const url = process.env.DATABASE_URL;
  if (!url || !["up", "down", "reset"].includes(direction)) {
    console.error("dùng: DATABASE_URL=… node src/migrate.ts up|down|reset");
    return 2;
  }
  const db = createDb(url, 1);
  try {
    for (const line of await migrate(db as unknown as Kysely<unknown>, direction as Direction)) {
      console.log(line);
    }
    return 0;
  } finally {
    await db.destroy();
  }
}

if (import.meta.main) {
  process.exitCode = await main(process.argv.slice(2));
}
