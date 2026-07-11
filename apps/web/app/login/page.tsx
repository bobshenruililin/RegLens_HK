import { Suspense } from "react";
import LoginPage from "./LoginClient";

export default function Page() {
  return (
    <Suspense fallback={<section className="panel">Loading…</section>}>
      <LoginPage />
    </Suspense>
  );
}
