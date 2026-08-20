/** IndexedDB persistence for the offline queue (design §09).
 *  LocalStorage is NOT used for data (Agent Rule 10). */
import type { OutboxItem } from "./engine";

const DB_NAME = "sms-offline";
const DB_VERSION = 1;
const OUTBOX = "outbox";
const DRAFTS = "drafts";
const META = "meta";

let dbPromise: Promise<IDBDatabase> | null = null;

function open(): Promise<IDBDatabase> {
  if (typeof indexedDB === "undefined") {
    return Promise.reject(new Error("IndexedDB unavailable"));
  }
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(OUTBOX)) {
          db.createObjectStore(OUTBOX, { keyPath: "client_mutation_id" });
        }
        if (!db.objectStoreNames.contains(DRAFTS)) {
          db.createObjectStore(DRAFTS); // key: sheet/roster cache id → value any
        }
        if (!db.objectStoreNames.contains(META)) {
          db.createObjectStore(META);
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  return dbPromise;
}

function tx<T>(store: string, mode: IDBTransactionMode,
                fn: (s: IDBObjectStore) => IDBRequest | void): Promise<T> {
  return open().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const t = db.transaction(store, mode);
        const s = t.objectStore(store);
        const req = fn(s);
        t.oncomplete = () => resolve((req as IDBRequest)?.result as T);
        t.onerror = () => reject(t.error);
      })
  );
}

export const outboxDb = {
  all: () => tx<OutboxItem[]>(OUTBOX, "readonly", (s) => s.getAll()),
  put: (item: OutboxItem) => tx(OUTBOX, "readwrite", (s) => void s.put(item)),
  putMany: (items: OutboxItem[]) =>
    tx(OUTBOX, "readwrite", (s) => void items.forEach((i) => s.put(i))),
  remove: (id: string) => tx(OUTBOX, "readwrite", (s) => void s.delete(id)),
  clear: () => tx(OUTBOX, "readwrite", (s) => void s.clear()),
};

export const draftsDb = {
  get: <T,>(key: string) => tx<T | undefined>(DRAFTS, "readonly", (s) => s.get(key)),
  put: (key: string, value: unknown) => tx(DRAFTS, "readwrite", (s) => void s.put(value, key)),
};

export const metaDb = {
  get: <T,>(key: string) => tx<T | undefined>(META, "readonly", (s) => s.get(key)),
  put: (key: string, value: unknown) => tx(META, "readwrite", (s) => void s.put(value, key)),
};
