import { AlertTriangle, RefreshCw, RotateCcw, ArrowLeft } from 'lucide-react';

export default function ErrorMessage({ error, onRetry, onReset }) {
  return (
    <div className="animate-fade-in-up">
      <div className="glass-card rounded-2xl p-8 text-center border-l-2 border-l-red-400">
        <div className="inline-flex flex-col items-center gap-3 max-w-sm">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
            <AlertTriangle size={24} className="text-red-500" />
          </div>
          <div>
            <h3 className="text-base font-bold text-surface-800 mb-1">
              {error?.title || '解析失败'}
            </h3>
            {error?.detail && (
              <p className="text-xs text-surface-500 leading-relaxed max-w-xs">
                {error.detail}
              </p>
            )}
          </div>
          <div className="flex gap-2 mt-2">
            {error?.retryable !== false && (
              <button
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-accent-600 text-white rounded-xl text-sm font-semibold hover:bg-accent-700 transition-all shadow-md shadow-accent-500/20"
              >
                <RefreshCw size={14} />重试
              </button>
            )}
            {onReset && (
              <button
                onClick={onReset}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-white text-surface-600 border-2 border-surface-200 rounded-xl text-sm font-medium hover:bg-surface-50 transition-all"
              >
                <ArrowLeft size={14} />换个链接
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
