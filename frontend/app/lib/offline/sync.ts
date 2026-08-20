/** Browser sync controller: queue → flush when online → status broadcast.
 *  Mutations go through POST /api/v1/sync/mutations — idempotent server side,
 *  so retries and duplicate flushes are safe (design §09). */
import { API } from "../api";
import { outboxDb } from "./db";
import {
  ApiMutationResult, OutboxItem, QueueSummary, classifyResult, latestByRef,
  markTransportFailed, pruneSynced, summarize,
} from "./engine";

type Listener = (items: OutboxItem[], summary: QueueSummary, online: boolean) => void;

let listeners: Listener[] = [];
let cache: OutboxItem[] = [];
let flushing = false;
let started = false;

function isOnline(): boolean {
  return typeof navigator === "undefined" ? true : navigator.onLine;
}

async function notify() {
  const summary = summarize(cache);
  for (const l of listeners) l(cache, summary, isOnline());
}

export function subscribeSync(fn: Listener): () => void {
  listeners.push(fn);
  fn(cache, summarize(cache), isOnline());
  return () => { listeners = listeners.filter((x) => x !== fn); };
}

export async function loadQueue(): Promise<void> {
  try { cache = await outboxDb.all(); } catch { cache = []; }
  await notify();
}

export async function enqueue(item: OutboxItem): Promise<void> {
  cache = pruneSynced([...cache.filter((i) => i.client_mutation_id !== item.client_mutation_id), item]);
  try { await outboxDb.put(item); } catch { /* in-memory only fallback */ }
  await notify();
  void flush();
}

export async function removeFromQueue(id: string): Promise<void> {
  cache = cache.filter((i) => i.client_mutation_id !== id);
  try { await outboxDb.remove(id); } catch { /* ignore */ }
  await notify();
}

export async function retryFailed(): Promise<void> {
  const updated = cache.map((i) => (i.status === "FAILED" ? { ...i, status: "PENDING" as const } : i));
  cache = updated;
  await outboxDb.putMany(updated.filter((i) => i.status === "PENDING"));
  await notify();
  void flush();
}

export async function flush(): Promise<void> {
  if (flushing || !isOnline()) return;
  const batch = cache.filter((i) => i.status === "PENDING").slice(0, 20);
  if (batch.length === 0) return;
  flushing = true;
  try {
    const res = await fetch(`${API}/sync/mutations`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mutations: batch.map((i) => ({
          client_mutation_id: i.client_mutation_id, entity_type: i.entity_type,
          entity_ref: i.entity_ref, base_version: i.base_version, payload: i.payload,
        })),
      }),
    });
    if (res.status === 401) { flushing = false; return; } // needs login; keep queue
    if (!res.ok) throw new Error(`sync ${res.status}`);
    const data = await res.json();
    const byId = new Map<string, ApiMutationResult>(
      (data.results as ApiMutationResult[]).map((r) => [r.client_mutation_id, r]));
    const next: OutboxItem[] = [];
    for (const item of cache) {
      const verdict = byId.get(item.client_mutation_id);
      next.push(verdict ? classifyResult(item, verdict) : item);
    }
    cache = pruneSynced(next);
    await outboxDb.clear();
    await outboxDb.putMany(cache);
  } catch (e) {
    // transport failure: pending items become FAILED (retryable), nothing lost
    cache = cache.map((i) =>
      i.status === "PENDING"
        ? markTransportFailed(i, e instanceof Error ? e.message : "network error")
        : i);
    try { await outboxDb.putMany(cache); } catch { /* ignore */ }
  } finally {
    flushing = false;
    await notify();
  }
}

export function startSyncEngine(): void {
  if (started || typeof window === "undefined") return;
  started = true;
  void loadQueue().then(() => flush());
  window.addEventListener("online", () => void flush());
  window.setInterval(() => {
    if (cache.some((i) => i.status === "PENDING")) void flush();
  }, 15000);
}

export function latestStatus(): Map<string, OutboxItem> {
  return latestByRef(cache);
}
