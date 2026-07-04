import { useState } from 'react';
import { User, Clock, Eye, ChevronDown, ChevronUp, ExternalLink, Play } from 'lucide-react';

// 生产环境图片代理：GitHub Pages 无法直接访问第三方图片（防盗链/跨域）
// 通过后端代理所有外部图片
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
function proxyImage(url) {
  if (!url) return '';
  if (url.startsWith('http')) {
    return `${API_BASE}/api/image/proxy?url=${encodeURIComponent(url)}`;
  }
  return url;
}

function formatViewCount(n) {
  if (n == null) return null;
  if (n >= 100000000) return `${(n / 100000000).toFixed(1)}亿`;
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  return n.toLocaleString();
}

export default function VideoInfo({ videoInfo }) {
  const [showDesc, setShowDesc] = useState(false);
  if (!videoInfo) return null;

  const { title, thumbnail, description, duration_str, uploader, view_count, webpage_url } = videoInfo;
  const desc = description || '暂无简介';
  const hasLongDesc = desc.length > 150;

  return (
    <div className="glass-card rounded-2xl overflow-hidden animate-fade-in-up group">
      <div className="flex flex-col sm:flex-row">
        {/* Thumbnail */}
        <div className="sm:w-2/5 flex-shrink-0 relative overflow-hidden bg-surface-100">
          {thumbnail ? (
            <a href={webpage_url} target="_blank" rel="noopener noreferrer" className="block">
              <img
                src={proxyImage(thumbnail)}
                alt={title}
                className="w-full h-48 sm:h-full object-cover transition-transform duration-500 group-hover:scale-105"
                loading="lazy"
              />
            </a>
          ) : (
            <div className="w-full h-48 sm:h-full min-h-[180px] bg-surface-100 flex items-center justify-center">
              <Play size={40} className="text-surface-300" />
            </div>
          )}
          {/* Duration badge */}
          {duration_str && (
            <span className="absolute bottom-2 right-2 bg-black/70 backdrop-blur text-white text-xs font-medium px-2 py-1 rounded-md">
              {duration_str}
            </span>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 p-5 flex flex-col justify-between">
          <div className="space-y-3">
            <a
              href={webpage_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-base md:text-lg font-semibold text-surface-900 hover:text-accent-600 transition-colors line-clamp-2 group/link"
            >
              {title}
              <ExternalLink size={12} className="inline ml-1.5 opacity-0 group-hover/link:opacity-100 transition-opacity text-accent-400" />
            </a>

            <div className="flex flex-wrap items-center gap-3 text-xs text-surface-500">
              {uploader && (
                <span className="inline-flex items-center gap-1.5 bg-surface-100 px-2.5 py-1 rounded-full">
                  <User size={12} className="text-accent-500" />
                  <span className="font-medium text-surface-700">{uploader}</span>
                </span>
              )}
              {view_count != null && (
                <span className="inline-flex items-center gap-1.5">
                  <Eye size={12} />
                  {formatViewCount(view_count)} 次播放
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="mt-3">
            <p className={`text-xs text-surface-500 leading-relaxed ${!showDesc ? 'line-clamp-3' : ''}`}>
              {desc}
            </p>
            {hasLongDesc && (
              <button
                onClick={() => setShowDesc(!showDesc)}
                className="mt-1.5 text-accent-600 hover:text-accent-700 text-xs font-medium inline-flex items-center gap-1 transition-colors"
              >
                {showDesc ? <>收起 <ChevronUp size={12} /></> : <>展开全部 <ChevronDown size={12} /></>}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
