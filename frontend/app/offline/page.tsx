export default function OfflinePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 px-4">
      <div className="max-w-md text-center">
        <h1 className="text-lg font-semibold text-slate-800">You are offline</h1>
        <p className="mt-2 text-sm text-slate-500">
          Marks and attendance you enter are stored securely on this device (IndexedDB) and
          will sync automatically when the connection returns. Conflicts — if a sheet changed
          elsewhere — are surfaced for your decision; nothing is silently lost.
        </p>
        <p className="mt-4 text-xs text-slate-400">
          Tip: keep this tab open; syncing resumes as soon as you are back online.
        </p>
      </div>
    </div>
  );
}
