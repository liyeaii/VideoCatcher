import { useState } from 'react';
import { User, Clock, Eye, ChevronDown, ChevronUp } from 'lucide-react';

export default function VideoInfo({ videoInfo }) {
  const [showDesc, setShowDesc] = useState(false);

  if (!videoInfo) return null;

  const {
    title,
    thumbnail,
    description,
    duration_str,
    uploader,
    view_count,
    webpage_url,
  } = videoInfo;

  const desc = description || '暂无简介';
  const hasLongDesc = desc.length > 150;

  const formatViewCount = (count) => {
    if (count == null) return null;
    if (count >= 10000) {
      return `${(count / 10000).toFixed(1)}万`;
    }
    return count.toLocaleString();
  };

  return (
    <div className="max-w-3xl mx-auto px-4 animate-fade-in">
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <div className="flex flex-col md:flex-row">
          {/* Thumbnail */}
          {thumbnail ? (
            <div className="md:w-2/5 flex-shrink-0">
              <a href={webpage_url} target="_blank" rel="noopener noreferrer">
                <img
                  src={thumbnail}
                  alt={title}
                  className="w-full h-48 md:h-full object-cover"
                  loading="lazy"
                />
              </a>
            </div>
          ) : (
            <div className="md:w-2/5 flex-shrink-0 h-48 md:h-auto bg-gray-200 flex items-center justify-center">
              <span className="text-gray-400 text-4xl">🎬</span>
            </div>
          )}

          {/* Info */}
          <div className="flex-1 p-5 md:p-6 space-y-3">
            <a
              href={webpage_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-lg md:text-xl font-bold text-gray-900 hover:text-indigo-600 transition-colors line-clamp-2"
            >
              {title}
            </a>

            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              {uploader && (
                <span className="inline-flex items-center gap-1.5">
                  <User size={15} />
                  <span className="font-medium text-gray-700">{uploader}</span>
                </span>
              )}
              {duration_str && (
                <span className="inline-flex items-center gap-1.5">
                  <Clock size={15} />
                  {duration_str}
                </span>
              )}
              {view_count != null && (
                <span className="inline-flex items-center gap-1.5">
                  <Eye size={15} />
                  {formatViewCount(view_count)} 次播放
                </span>
              )}
            </div>

            {/* Description */}
            <div className="relative">
              <p
                className={`text-sm text-gray-600 leading-relaxed ${
                  !showDesc ? 'line-clamp-3' : ''
                }`}
              >
                {desc}
              </p>
              {hasLongDesc && (
                <button
                  onClick={() => setShowDesc(!showDesc)}
                  className="mt-1 text-indigo-500 hover:text-indigo-700 text-xs font-medium inline-flex items-center gap-1 transition-colors"
                >
                  {showDesc ? (
                    <>
                      收起 <ChevronUp size={14} />
                    </>
                  ) : (
                    <>
                      展开全部 <ChevronDown size={14} />
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
