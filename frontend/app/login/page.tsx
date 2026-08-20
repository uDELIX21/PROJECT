"use client";

import { useRouter } from "next/navigation";
import React, { useState } from "react";
import { api, ApiClientError, setCsrf } from "../lib/api";

const DEMO_ACCOUNTS = [
  { u: "admin", label: "Super Admin" },
  { u: "head", label: "Headteacher" },
  { u: "bursar", label: "Bursar" },
  { u: "teacher1", label: "Teacher" },
  { u: "parent1", label: "Parent" },
];
const DEMO_PASSWORD = "Demo#2026accra";

function DemoCredentials({ onUse }: { onUse: (u: string, p: string) => void }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5">
      <p className="text-[11px] font-medium text-slate-500 mb-1.5">
        Demo accounts (password <code className="font-mono">Demo#2026accra</code>) — tap to fill:
      </p>
      <div className="flex flex-wrap gap-1.5">
        {DEMO_ACCOUNTS.map((a) => (
          <button
            key={a.u}
            type="button"
            onClick={() => onUse(a.u, DEMO_PASSWORD)}
            className="rounded border border-slate-300 bg-white px-2 py-1 text-[11px] text-slate-600 hover:bg-slate-100"
          >
            {a.label} <span className="font-mono text-slate-400">{a.u}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api("/auth/login", {
        method: "POST",
        body: { username, password },
      });
      setCsrf(res.csrf_token);
      router.replace("/");
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError("Unable to reach the server.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="text-xl font-bold text-brand-800">School Management System</h1>
          <p className="text-sm text-slate-500 mt-1">Sign in to continue</p>
        </div>
        <form
          onSubmit={submit}
          className="bg-white border border-slate-200 rounded-lg shadow-sm p-6 space-y-4"
        >
          {error && (
            <div role="alert" className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}
          <div>
            <label className="label" htmlFor="username">Username</label>
            <input
              id="username"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <DemoCredentials onUse={(u, p) => { setUsername(u); setPassword(p); setError(null); }} />
        </form>
      </div>
    </div>
  );
}
