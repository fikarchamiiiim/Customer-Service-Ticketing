export function LoginPage() {
  return (
    <div className="mx-auto max-w-md space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-xl font-semibold">Login</h1>
      <p className="text-sm text-slate-500">
        Halaman ini masih placeholder. Google SSO dipasang di <strong>Step 2</strong>.
      </p>
      <button
        disabled
        className="w-full cursor-not-allowed rounded-md border border-slate-200 bg-slate-100 px-4 py-2 text-sm text-slate-400"
      >
        Sign in with Google (Step 2)
      </button>
    </div>
  )
}
