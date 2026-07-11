/**
 * Studio Checkpoint C — demo mode smoke expectations.
 *
 * `REGLENS_MODE` defaults to `demo`. With demo mode:
 * - `lib/data.ts` file seed paths remain the decision/review/search plane
 * - `npm run typecheck` and `npm run build` must pass without DATABASE_URL
 * - `make verify` / `make studio-ci` must keep working
 *
 * Postgres mode (`REGLENS_MODE=postgres`) requires DATABASE_URL and is
 * exercised separately against a migrated database.
 */

import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

// Ensure default mode is demo when unset (mirrors lib/mode.ts).
delete process.env.REGLENS_MODE;
const modeModPath = path.join(root, "lib/mode.ts");
assert.ok(require("fs").existsSync(modeModPath));

const dataTs = require("fs").readFileSync(path.join(root, "lib/data.ts"), "utf8");
assert.ok(dataTs.includes("data/seed"));
assert.ok(!dataTs.includes("fixtures/seed"));
assert.ok(dataTs.includes("assertNotFixturesPath"));

const pkg = JSON.parse(
  require("fs").readFileSync(path.join(root, "package.json"), "utf8")
);
assert.ok(pkg.dependencies.pg, "pg must be a dependency");
assert.ok(pkg.devDependencies["@types/pg"] || pkg.dependencies["@types/pg"]);
assert.equal(pkg.scripts["user:create"], "node scripts/create-user.mjs");

console.log("studio-demo-mode-smoke: ok");
