import { useState, useEffect } from 'react';
import { Loader2, FileText } from 'lucide-react';
import api from '../api/client';

export default function SubtitlesPanel({ url }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!url) return;
    setLoading(true);
    setError('');
    api.get('/video/subtitles', { params: { url } })
      .then(r => { setText(r.data.text); setLoading(false); })
      .catch(() => { setError('字幕提取失败'); setLoading(false); });
  }, [url]);

  if (loading) return (
    <div className="flex items-center gap-2 text-surface-500 py-8 justify-center">
      <Loader2 size={18} className="animate-spin text-accent-500" /> 提取字幕中...
    </div>
  );
  if (error) return <div className="text-red-500 text-sm py-6 text-center">{error}</div>;

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-bold text-surface-700 mb-3 flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-accent-100 flex items-center justify-center">
          <FileText size={14} className="text-accent-600" />
        </div>
        字幕文本
      </h3>
      <div className="text-sm text-surface-600 leading-relaxed whitespace-pre-wrap max-h-80 overflow-y-auto bg-surface-50 rounded-lg p-4 border border-surface-100">
        {text || '该视频没有可提取的字幕'}
      </div>
    </div>
  );
}
