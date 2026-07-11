import { redirect } from "next/navigation";
import { getCurrentUser, listUsers } from "../../../lib/auth-server";
import { isAdmin } from "../../../lib/auth";
import { isDemoMode } from "../../../lib/mode";

export const dynamic = "force-dynamic";

export default async function AdminUsersPage() {
  const user = await getCurrentUser();
  if (!user || !isAdmin(user.role)) {
    redirect("/dashboard");
  }

  const users = await listUsers();

  return (
    <section className="panel">
      <h1>Users</h1>
      <p>
        Admin-only.{" "}
        {isDemoMode()
          ? "Demo mode shows the local HMAC operator as admin."
          : "Manage via DATABASE_URL / npm run user:create."}
      </p>
      <div className="prop-list">
        {users.map((u) => (
          <div className="prop" key={u.id}>
            <div className="prop-type">
              {u.role} · {u.active ? "active" : "inactive"}
            </div>
            <p className="claim">
              {u.display_name || u.username} (<code>{u.username}</code>)
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
