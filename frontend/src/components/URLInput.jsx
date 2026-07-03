import { useState } from 'react';
import { LinkIcon, Loader2 } from 'lucide-react';

export default function URLInput({ onSubmit, isLoading }) {
  const [url, setUrl] = useState('');
  const [localError, setLocalError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) {
      setLocalError('请输入视频链接');
      return;
    }
    // Basic URL validation
    try {
      new URL(trimmed);
    } catch {
      setLocalError('请输入有效的 URL 地址');
      return;
    }
    if (!trimmed.startsWith('http')) {
      setLocalError('链接必须以 http:// 或 https:// 开头');
      return;
    }
    setLocalError('');
    onSubmit(trimmed);
  };

  const handlePaste = () => {
    navigator.clipboard.readText().then((text) => {
      if (text) {
        setUrl(text);
        setLocalError('');
      }
    }).catch(() => {});
  };

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMiIvPjwvZz48L2c+PC9zdmc+')] opacity-50"></div>
      <div className="relative max-w-3xl mx-auto px-4 py-20 sm:py-28">
        <div className="text-center mb-10">
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 tracking-tight">
            🎬 万能视频下载器
          </h1>
          <p className="text-lg sm:text-xl text-indigo-100">
            粘贴视频链接，一键获取视频信息和下载选项
          </p>
          <p className="text-sm text-indigo-200/80 mt-2">
            支持 YouTube · Bilibili · TikTok · Twitter/X · Vimeo 等 1000+ 网站
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-xl mx-auto">
          <div className="flex-1 relative">
            <input
              type="text"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setLocalError(''); }}
              onPaste={() => {
                setTimeout(() => setLocalError(''), 100);
              }}
              placeholder="粘贴视频链接到此处..."
              disabled={isLoading}
              className={`w-full px-5 py-4 rounded-full text-gray-900 text-base shadow-lg border-2 transition-all outline-none
                ${localError ? 'border-red-400 bg-red-50' : 'border-transparent focus:border-indigo-300 bg-white'}`}
            />
            <button
              type="button"
              onClick={handlePaste}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-indigo-600 bg-gray-100 hover:bg-indigo-50 px-3 py-1.5 rounded-full transition-colors"
            >
              <LinkIcon size={14} className="inline mr-1" />
              粘贴
            </button>
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="px-8 py-4 rounded-full font-semibold text-white shadow-lg transition-all
              bg-indigo-900/20 backdrop-blur border border-white/20 hover:bg-white/20
              disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                解析中...
              </>
            ) : (
              '解析视频'
            )}
          </button>
        </form>
        {localError && (
          <p className="text-center mt-3 text-red-200 text-sm">{localError}</p>
        )}
      </div>
    </section>
  );
}
