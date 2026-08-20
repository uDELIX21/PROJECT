"use client";

import React, { useEffect, useState } from "react";
import { Badge, EmptyState, ErrorBanner, Field, Loading, PageHeader, Panel } from "../components/ui";
import { api } from "../lib/api";
import { useSession } from "../lib/session";

interface UserRow {
  id: string; username: string; display_name?: string; status: string; roles: string[];
  last_login_at?: string;
}

export default function UsersPage() {
  const { me } = useSession();
  const [rows, setRows] = useState<UserRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("TEACHER");

  const load = () =>
    api<{ items: UserRow[] }>("/users?limit=100")
      .then((r) => setRows(r.items))
      .catch((e) => setError(e.message));

  useEffect(() => { if (me) load(); /* eslint-disable-line */ }, [me]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api("/users", {
        method: "POST",
        body: { username, password, display_name: displayName || undefined, role_codes: [role] },
      });
      setShowCreate(false); setUsername(""); setPassword(""); setDisplayName("");
      load();
    } catch (err: any) { setError(err.message); }
  };

  const toggleStatus = async (u: UserRow) => {
    const status = u.status === "ACTIVE" ? "DEACTIVATED" : "ACTIVE";
    try {
      await api(`/users/${u.id}`, { method: "PATCH", body: { status } });
      load();
    } catch (err: any) { setError(err.message); }
  };

  return (
    <>
      <PageHeader
        title="Users"
        subtitle="Accounts, roles and access. Role grants/revokes are audited."
        actions={<button className="btn-primary" onClick={() => setShowCreate(!showCreate)}>New user</button>}
      />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}

      {showCreate && (
        <Panel title="Create user">
          <form onSubmit={create} className="grid gap-4 px-4 py-4 sm:grid-cols-2 lg:grid-cols-4">
            <Field label="Username"><input className="input" value={username} onChange={(e) => setUsername(e.target.value)} required /></Field>
            <Field label="Display name"><input className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} /></Field>
            <Field label="Password" hint="Min 10 characters"><input type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={10} /></Field>
            <Field label="Role">
              <select className="input" value={role} onChange={(e) => setRole(e.target.value)}>
                {["TEACHER", "BURSAR", "HEAD_TEACHER", "PARENT", "SUPER_ADMIN"].map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </Field>
            <div className="sm:col-span-2 lg:col-span-4">
              <button className="btn-primary">Create account</button>
            </div>
          </form>
        </Panel>
      )}

      <div className="mt-4">
        <Panel>
          {rows === null ? (
            <Loading />
          ) : rows.length === 0 ? (
            <EmptyState title="No users" />
          ) : (
            <div className="overflow-x-auto">
              <table className="tbl">
                <thead>
                  <tr><th>Username</th><th>Display name</th><th>Roles</th><th>Status</th><th>Last login</th><th></th></tr>
                </thead>
                <tbody>
                  {rows.map((u) => (
                    <tr key={u.id}>
                      <td className="font-mono text-xs">{u.username}</td>
                      <td>{u.display_name ?? "—"}</td>
                      <td className="text-xs text-slate-600">{u.roles.join(", ")}</td>
                      <td><Badge value={u.status} /></td>
                      <td className="text-xs text-slate-500">
                        {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "never"}
                      </td>
                      <td className="text-right">
                        {u.id !== me?.user.id && (
                          <button className="btn-secondary !py-1" onClick={() => toggleStatus(u)}>
                            {u.status === "ACTIVE" ? "Deactivate" : "Activate"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
