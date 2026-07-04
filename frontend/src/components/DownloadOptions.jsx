import { Download, Loader2, Film, Music, Monitor, Star, ArrowDown, Check } from 'lucide-react';
import { useState } from 'react';

const TYPE_CONFIG = {
  'video+audio': { label: '视频 + 音频', icon: Film, desc: '含声音的完整视频' },
  'video only': { label: '仅视频', icon: Monitor, desc: '无声音的纯画面' },
  'audio only': { label: '仅音频', icon: Music, desc: '提取音频为 MP3' },
};

function useDownloadState() {
  const [completed, setCompleted] = useState({});
  const markComplete = (id) => setCompleted(prev => ({ ...prev, [id]: true }));
  return { completed, markComplete };
}

export default function DownloadOptions({ formats, onDownload, downloadingId, downloadProgress }) {
  if (!formats || formats.length === 0) return null;

  const grouped = {};
  for (const fmt of formats) {
    const type = fmt.type || 'video+audio';
    if (!grouped[type]) grouped[type] = [];
    grouped[type].push(fmt);
  }

  const typeOrder = ['video+audio', 'video only', 'audio only'];

  return (
    <div className="glass-card rounded-2xl p-5 sm:p-6 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-lg bg-accent-100 flex items-center justify-center">
          <Download size={16} className="text-accent-600" />
        </div>
        <h2 className="text-base font-bold text-surface-800">下载选项</h2>
      </div>

      <div className="space-y-5">
        {typeOrder.map(type => {
          const fmts = grouped[type];
          if (!fmts || fmts.length === 0) return null;
          const config = TYPE_CONFIG[type];
          const Icon = config.icon;

          return (
            <div key={type}>
              {/* Type label */}
              <div className="flex items-center gap-2 mb-3">
                <Icon size={14} className="text-accent-500" />
                <span className="text-xs font-semibold text-surface-500 uppercase tracking-wide">
                  {config.label}
                </span>
                <span className="text-[10px] text-surface-400">{config.desc}</span>
              </div>

              {/* Format cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
                {fmts.map((fmt, idx) => {
                  const isDownloading = downloadingId === fmt.format_id;
                  const progress = downloadProgress[fmt.format_id] || 0;
                  const isBest = idx === 0 && type === 'video+audio';
                  const isDone = progress >= 100;

                  let borderClass = 'border-surface-200 bg-white hover:border-accent-300 hover:shadow-md';
                  if (isBest) borderClass = 'border-accent-300 bg-accent-50/50 hover:border-accent-400 ring-1 ring-accent-200';
                  if (isDownloading) borderClass = 'border-accent-300 bg-accent-50/30';
                  if (isDone) borderClass = 'border-emerald-300 bg-emerald-50/50';

                  return (
                    <DownloadButton
                      key={fmt.format_id}
                      fmt={fmt}
                      isDownloading={isDownloading}
                      isBest={isBest}
                      isDone={isDone}
                      progress={progress}
                      borderClass={borderClass}
                      onDownload={() => onDownload(fmt.format_id, fmt.type)}
                    />
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

function DownloadButton({ fmt, isDownloading, isBest, isDone, progress, borderClass, onDownload }) {
  return (
    <button
      onClick={() => !isDownloading && !isDone && onDownload()}
      disabled={isDownloading}
      className={`relative flex flex-col items-center gap-1 p-3.5 rounded-xl border-2 text-center transition-all duration-200 cursor-pointer
        ${borderClass}
        ${isDownloading ? 'cursor-wait' : 'cursor-pointer'}
        ${!isDownloading && !isDone ? 'active:scale-[0.97]' : ''}`}
    >
      {/* Best badge */}
      {isBest && !isDownloading && !isDone && (
        <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-accent-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full shadow-md flex items-center gap-1">
          <Star size={10} /> 推荐
        </span>
      )}

      {/* Done badge */}
      {isDone && (
        <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full shadow-md flex items-center gap-1">
          <Check size={10} /> 完成
        </span>
      )}

      {/* Content */}
      <span className="text-sm font-bold text-surface-800">{fmt.quality}</span>
      <span className="text-[11px] text-surface-400 font-mono uppercase">{fmt.ext}</span>
      <span className="text-[10px] text-surface-400">{fmt.filesize_str}</span>

      {/* Action */}
      {isDownloading ? (
        progress > 0 && progress < 100 ? (
          <div className="w-full flex items-center gap-2 mt-1.5">
            <div className="flex-1 h-1.5 bg-surface-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent-500 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-[10px] font-bold text-accent-600 tabular-nums">{progress}%</span>
          </div>
        ) : (
          <span className="text-[10px] text-surface-500 mt-1 flex items-center gap-1">
            <Loader2 size={10} className="animate-spin" />准备中
          </span>
        )
      ) : isDone ? (
        <span className="text-[10px] text-emerald-600 font-medium mt-1 flex items-center gap-1">
          <Check size={10} />已下载
        </span>
      ) : (
        <span className="text-[10px] text-accent-600 font-medium mt-1 flex items-center gap-1 group-hover:underline">
          <ArrowDown size={10} />下载
        </span>
      )}
    </button>
  );
}
