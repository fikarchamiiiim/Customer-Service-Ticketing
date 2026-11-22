import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '../api/health'
import { StatusDot } from '../components/StatusDot'

export function HealthPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 10_000,
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Status Sistem</h1>
          <p className="text-sm text-slate-500">
            Memanggil <code className="rounded bg-slate-100 px-1">GET /api/v1/health</code> lewat
            Vite proxy setiap 10 detik.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-100"
        >
          {isFetching ? 'Memeriksa…' : 'Refresh'}
        </button>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        {isLoading && <p className="text-sm text-slate-500">Memeriksa…</p>}

        {isError && (
          <div className="space-y-2">
            <StatusDot ok={false} label="API: tidak terjangkau" />
            <p className="text-sm text-rose-600">
              {error instanceof Error ? error.message : 'Backend belum jalan?'}
            </p>
            <p className="text-xs text-slate-500">
              Jalankan <code className="rounded bg-slate-100 px-1">make be</code> di terminal lain.
            </p>
          </div>
        )}

        {data && (
          <div className="space-y-3">
            <StatusDot ok={data.status === 'ok'} label={`API: ${data.status}`} detail={`v${data.version}`} />
            <StatusDot ok={data.db === 'ok'} label={`DB: ${data.db}`} detail={data.db_error} />
            <pre className="mt-3 overflow-x-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
