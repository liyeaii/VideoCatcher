import { useState } from 'react';
import { Link, Loader2, Search, ArrowRight } from 'lucide-react';

export default function URLInput({ onSubmit, isLoading, isIdle }) {
  const [url, setUrl] = useState('');
  const [localError, setLocalError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) { setLocalError('请输入视频链接'); return; }
    try { new URL(trimmed); } catch { setLocalError('请输入有效的 URL'); return; }
    if (!trimmed.startsWith('http')) { setLocalError('链接必须以 http:// 或 https:// 开头'); return; }
    setLocalError('');
    onSubmit(trimmed);
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) { setUrl(text); setLocalError(''); }
    } catch {}
  };

  return (
    <header className={`relative transition-all duration-500 ${isIdle ? 'hero-gradient py-20 sm:py-28' : 'bg-white border-b border-surface-200 py-6 sm:py-8'}`}>
      {/* Decorative blobs for idle state */}
      {isIdle && (
        <>
          <div className="absolute top-10 left-10 w-64 h-64 bg-accent-400/10 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-blue-400/5 rounded-full blur-3xl" />
        </>
      )}

      <div className="max-w-3xl mx-auto px-4 relative z-10">
        {/* Logo / Title */}
        <div className={`text-center transition-all duration-500 ${isIdle ? 'mb-10' : 'mb-4'}`}>
          <div className="inline-flex items-center gap-2.5 mb-3">
            <div className="w-9 h-9 rounded-xl bg-accent-600 flex items-center justify-center shadow-lg shadow-accent-500/25">
              <Search size={18} className="text-white" />
            </div>
            <h1 className={`font-extrabold tracking-tight text-surface-900 ${isIdle ? 'text-3xl sm:text-4xl' : 'text-xl'}`}>
              Video<span className="text-accent-600">Catcher</span>
            </h1>
          </div>
          {isIdle && (
            <p className="text-surface-500 text-base sm:text-lg max-w-md mx-auto leading-relaxed">
              粘贴视频链接，一键获取信息、AI 智能总结与多格式下载
            </p>
          )}
        </div>

        {/* Search Box */}
        <form onSubmit={handleSubmit} className="max-w-xl mx-auto">
          <div className={`flex gap-2 ${isIdle ? 'shadow-lg shadow-surface-900/5' : ''}`}>
            <div className="flex-1 relative group">
              <input
                type="text"
                value={url}
                onChange={e => { setUrl(e.target.value); setLocalError(''); }}
                placeholder={isIdle ? '粘贴视频链接... 支持 YouTube、Bilibili、抖音等' : '粘贴视频链接...'}
                disabled={isLoading}
                className={`w-full pl-4 pr-16 py-3.5 rounded-xl text-sm outline-none transition-all duration-200
                  ${localError
                    ? 'border-2 border-red-300 bg-red-50 text-red-700 placeholder-red-400'
                    : 'border-2 border-surface-200 bg-white text-surface-900 placeholder-surface-400 hover:border-surface-300 focus:border-accent-500 focus:ring-4 focus:ring-accent-500/10'}`}
              />
              <button
                type="button"
                onClick={handlePaste}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 text-xs font-medium text-surface-500 hover:text-accent-600 bg-surface-100 hover:bg-accent-50 px-3 py-1.5 rounded-lg transition-all duration-150 flex items-center gap-1.5"
                title="从剪贴板粘贴"
              >
                <Link size={12} />
                粘贴
              </button>
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-3.5 rounded-xl font-semibold text-sm text-white transition-all duration-200
                bg-accent-600 hover:bg-accent-700 active:bg-accent-700
                disabled:opacity-50 disabled:cursor-not-allowed
                shadow-lg shadow-accent-500/25 hover:shadow-accent-500/40
                flex items-center gap-2 whitespace-nowrap"
            >
              {isLoading ? (
                <><Loader2 size={16} className="animate-spin" />解析中</>
              ) : (
                <><Search size={16} />解析</>
              )}
            </button>
          </div>
          {localError && (
            <p className="mt-2 text-red-500 text-xs font-medium text-center">{localError}</p>
          )}
        </form>

        {/* Quick hint for idle state */}
        {isIdle && (
          <p className="text-center mt-4 text-xs text-surface-400">
            按 <kbd className="px-1.5 py-0.5 bg-surface-200 rounded text-surface-500 font-mono text-xs">Ctrl+V</kbd> 粘贴 &nbsp;·&nbsp; 支持 1000+ 视频平台
          </p>
        )}
      </div>
    </header>
  );
}
