import { Download, Loader2, CheckCircle2, Film, Music, Monitor } from 'lucide-react';

const TYPE_CONFIG = {
  'video+audio': { label: '视频 + 音频（推荐）', icon: Film, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  'video only': { label: '仅视频（无声音）', icon: Monitor, color: 'text-blue-600', bg: 'bg-blue-50' },
  'audio only': { label: '仅音频', icon: Music, color: 'text-orange-600', bg: 'bg-orange-50' },
};

export default function DownloadOptions({ formats, onDownload, downloadingId, downloadProgress }) {
  if (!formats || formats.length === 0) return null;

  // Group formats by type
  const grouped = {};
  for (const fmt of formats) {
    const type = fmt.type || 'video+audio';
    if (!grouped[type]) grouped[type] = [];
    grouped[type].push(fmt);
  }

  // Ordered groups
  const groupOrder = ['video+audio', 'video only', 'audio only'];

  return (
    <div className="max-w-3xl mx-auto px-4 animate-fade-in-delay-2">
      <div className="bg-white rounded-2xl shadow-md p-5 md:p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-5 flex items-center gap-2">
          <Download size={20} className="text-indigo-500" />
          下载选项
        </h2>

        {groupOrder.map((type) => {
          const fmts = grouped[type];
          if (!fmts || fmts.length === 0) return null;

          const config = TYPE_CONFIG[type] || TYPE_CONFIG['video+audio'];
          const Icon = config.icon;

          return (
            <div key={type} className="mb-6 last:mb-0">
              <h3 className={`text-sm font-semibold mb-3 flex items-center gap-2 ${config.color}`}>
                <Icon size={16} />
                {config.label}
                <span className="text-xs font-normal text-gray-400">({fmts.length} 个选项)</span>
              </h3>

              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {fmts.map((fmt, idx) => {
                  const isDownloading = downloadingId === fmt.format_id;
                  const progress = downloadProgress[fmt.format_id] || 0;
                  const isBest = idx === 0 && type === 'video+audio';

                  return (
                    <button
                      key={fmt.format_id}
                      onClick={() => !isDownloading && onDownload(fmt.format_id)}
                      disabled={isDownloading}
                      className={`relative flex flex-col items-center gap-1.5 p-4 rounded-xl border-2 transition-all text-center
                        ${isBest
                          ? 'border-amber-300 bg-amber-50 hover:border-amber-400'
                          : 'border-gray-200 bg-white hover:border-indigo-300 hover:shadow-sm'
                        }
                        ${isDownloading ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}
                      `}
                    >
                      {isBest && !isDownloading && (
                        <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-amber-400 text-white text-[11px] font-semibold px-2.5 py-0.5 rounded-full whitespace-nowrap">
                          最佳画质
                        </span>
                      )}

                      {/* Quality label */}
                      <span className="text-sm font-bold text-gray-900">
                        {fmt.quality}
                      </span>
                      <span className="text-xs text-gray-400 uppercase">{fmt.ext}</span>
                      <span className="text-xs text-gray-500">{fmt.filesize_str}</span>

                      {/* Download state */}
                      {isDownloading ? (
                        <div className="mt-1 w-full">
                          {progress > 0 && progress < 100 ? (
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-indigo-500 rounded-full transition-all"
                                  style={{ width: `${progress}%` }}
                                />
                              </div>
                              <span className="text-xs text-indigo-600 font-medium">{progress}%</span>
                            </div>
                          ) : progress >= 100 ? (
                            <span className="inline-flex items-center gap-1 text-xs text-emerald-600 font-medium">
                              <CheckCircle2 size={12} />
                              完成
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-xs text-indigo-500">
                              <Loader2 size={12} className="animate-spin" />
                              准备中
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-indigo-500 font-medium mt-1">
                          <Download size={12} />
                          下载
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
