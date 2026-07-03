import { AlertTriangle, RefreshCw, RotateCcw } from 'lucide-react';

export default function ErrorMessage({ error, onRetry, onReset }) {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">
      <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
        <AlertTriangle size={40} className="mx-auto text-red-400 mb-3" />
        <h3 className="text-lg font-semibold text-red-800 mb-1">{error?.title || '出错了'}</h3>
        {error?.detail && (
          <p className="text-sm text-red-600 mb-4">{error.detail}</p>
        )}
        <div className="flex justify-center gap-3">
          {error?.retryable !== false && onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white rounded-full text-sm font-medium hover:bg-red-700 transition-colors"
            >
              <RefreshCw size={16} />
              重试
            </button>
          )}
          {onReset && (
            <button
              onClick={onReset}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-gray-700 border border-gray-300 rounded-full text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              <RotateCcw size={16} />
              换个链接
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
