const FMT = new Intl.DateTimeFormat('id-ID', {
  dateStyle: 'medium',
  timeStyle: 'short',
  timeZone: 'Asia/Jakarta',
})

/** Backend mengirim UTC (ISO 8601). Semua tampilan dikonversi ke Asia/Jakarta. */
export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return FMT.format(new Date(iso))
}

export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const min = Math.round(diff / 60000)
  if (min < 1) return 'baru saja'
  if (min < 60) return `${min} menit lalu`
  const hours = Math.round(min / 60)
  if (hours < 24) return `${hours} jam lalu`
  const days = Math.round(hours / 24)
  return `${days} hari lalu`
}
