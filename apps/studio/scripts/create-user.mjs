#!/usr/bin/env node
/**
 * Bootstrap an admin user against DATABASE_URL.
 *
 * Usage:
 *   DATABASE_URL=... npm run user:create -- --username admin
 *   REG_LENS_BOOTSTRAP_PASSWORD=... DATABASE_URL=... npm run user:create
 *
 * Password format matches Python: scrypt$N$r$p$salt_b64$hash_b64
 */

import { createInterface } from "node:readline";
import { randomBytes, scryptSync } from "node:crypto";
import pg from "pg";

const SCRYPT_N = 2 ** 14;
const SCRYPT_R = 8;
const SCRYPT_P = 1;
const SCRYPT_DKLEN = 64;

function hashPassword(password) {
  const salt = randomBytes(16);
  const digest = scryptSync(password, salt, SCRYPT_DKLEN, {
    N: SCRYPT_N,
    r: SCRYPT_R,
    p: SCRYPT_P,
  });
  return `scrypt$${SCRYPT_N}$${SCRYPT_R}$${SCRYPT_P}$${salt.toString("base64")}$${digest.toString("base64")}`;
}

function parseArgs(argv) {
  const out = { username: "admin", role: "admin", displayName: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--username" && argv[i + 1]) out.username = argv[++i];
    else if (a === "--role" && argv[i + 1]) out.role = argv[++i];
    else if (a === "--display-name" && argv[i + 1]) out.displayName = argv[++i];
  }
  return out;
}

function promptPassword(prompt) {
  return new Promise((resolve, reject) => {
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    rl.question(prompt, (answer) => {
      rl.close();
      resolve(answer);
    });
    rl.on("SIGINT", () => {
      rl.close();
      reject(new Error("interrupted"));
    });
  });
}

async function main() {
  const dsn = (process.env.DATABASE_URL || "").trim();
  if (!dsn) {
    console.error("DATABASE_URL is required");
    process.exit(1);
  }
  const args = parseArgs(process.argv.slice(2));
  if (!["reviewer", "publisher", "admin"].includes(args.role)) {
    console.error(`Invalid role=${args.role}`);
    process.exit(1);
  }

  let password = process.env.REG_LENS_BOOTSTRAP_PASSWORD || "";
  if (!password) {
    password = await promptPassword(`Password for ${args.username}: `);
  }
  if (!password) {
    console.error("Password is required (prompt or REG_LENS_BOOTSTRAP_PASSWORD)");
    process.exit(1);
  }

  const passwordHash = hashPassword(password);
  const client = new pg.Client({ connectionString: dsn });
  await client.connect();
  try {
    const res = await client.query(
      `
      INSERT INTO users (username, password_hash, role, active, display_name)
      VALUES ($1, $2, $3, TRUE, $4)
      ON CONFLICT (username) DO UPDATE SET
        password_hash = EXCLUDED.password_hash,
        role = EXCLUDED.role,
        display_name = COALESCE(EXCLUDED.display_name, users.display_name),
        updated_at = now(),
        active = TRUE
      RETURNING id, username, role, active, display_name
      `,
      [args.username.trim(), passwordHash, args.role, args.displayName]
    );
    const user = res.rows[0];
    console.log(
      JSON.stringify(
        {
          ok: true,
          id: user.id,
          username: user.username,
          role: user.role,
          active: user.active,
          display_name: user.display_name,
        },
        null,
        2
      )
    );
  } finally {
    await client.end();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
