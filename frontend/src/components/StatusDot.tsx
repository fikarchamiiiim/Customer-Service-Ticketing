type Props = {
  ok: boolean
  label: string
  detail?: string | null
}

export function StatusDot({ ok, label, detail }: Props) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={`h-2.5 w-2.5 rounded-full ${ok ? 'bg-emerald-500' : 'bg-rose-500'}`}
        aria-hidden
      />
      <span className="text-sm font-medium text-slate-700">{label}</span>
      {detail && <span className="truncate text-xs text-slate-400">{detail}</span>}
    </div>
  )
}
