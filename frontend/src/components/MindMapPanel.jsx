import { useState, useEffect } from 'react';
import { Loader2, GitFork, ChevronRight } from 'lucide-react';
import api from '../api/client';

export default function MindMapPanel({ url, title }) {
  const [mindmap, setMindmap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!url) return;
    setLoading(true);
    setError('');
    api.post('/video/mindmap', { url })
      .then(r => { setMindmap(r.data); setLoading(false); })
      .catch(() => { setError('生成失败，请重试'); setLoading(false); });
  }, [url]);

  if (loading) return (
    <div className="flex items-center gap-2 text-surface-500 py-8 justify-center">
      <Loader2 size={18} className="animate-spin text-accent-500" /> 生成思维导图...
    </div>
  );
  if (error) return <div className="text-red-500 text-sm py-6 text-center">{error}</div>;
  if (!mindmap) return null;

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-bold text-surface-700 mb-4 flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-accent-100 flex items-center justify-center">
          <GitFork size={14} className="text-accent-600" />
        </div>
        思维导图
      </h3>
      <MindNode node={mindmap} depth={0} />
    </div>
  );
}

function MindNode({ node, depth }) {
  const colors = ['text-accent-700', 'text-amber-600', 'text-sky-600', 'text-rose-600'];
  const bgColors = ['bg-accent-50', 'bg-amber-50', 'bg-sky-50', 'bg-rose-50'];
  const borderColors = ['border-accent-200', 'border-amber-200', 'border-sky-200', 'border-rose-200'];

  const hasChildren = node.children && node.children.length > 0;
  const ci = Math.min(depth, 3);

  return (
    <div className={`${depth === 0 ? 'mb-2' : 'ml-5 mb-1'} ${depth > 0 ? borderColors[Math.min(depth - 1, 3)] + ' border-l-2 pl-4' : ''}`}>
      <div className={`inline-flex items-center gap-1.5 font-semibold px-2 py-0.5 rounded-lg ${bgColors[ci]}
        ${depth === 0 ? 'text-base ' + colors[0] : depth === 1 ? 'text-sm ' + colors[1] : 'text-xs text-surface-500'}`}>
        {depth === 0 && <ChevronRight size={14} />}
        {node.label || node.theme}
      </div>
      {hasChildren && (
        <div className="mt-1.5 space-y-0.5">
          {node.children.map((child, i) => (
            <MindNode key={i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
