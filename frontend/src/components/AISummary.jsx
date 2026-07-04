import { Sparkles, AlertTriangle, Zap } from 'lucide-react';

export default function AISummary({ summary, error }) {
  // Error state
  if (error && !summary) {
    return (
      <div className="glass-card rounded-2xl p-5 border-l-2 border-l-amber-400 animate-fade-in-up">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
            <AlertTriangle size={16} className="text-amber-600" />
          </div>
          <span className="text-sm font-semibold text-amber-700">AI 总结不可用</span>
        </div>
        <p className="text-xs text-surface-500 pl-10">
          请在 .env 中配置 AI_API_KEY 以启用 AI 功能
        </p>
      </div>
    );
  }

  if (!summary) return null;

  const { summary: text, key_points } = summary;

  return (
    <div className="glass-card rounded-2xl p-5 border-l-2 border-l-accent-500 animate-fade-in-up h-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-accent-100 flex items-center justify-center">
          <Sparkles size={16} className="text-accent-600" />
        </div>
        <div>
          <span className="text-sm font-semibold text-surface-800">AI 智能总结</span>
        </div>
        <span className="ml-auto text-[10px] font-medium text-surface-400 bg-surface-100 px-2 py-0.5 rounded-full flex items-center gap-1">
          <Zap size={10} />
          AI
        </span>
      </div>

      {/* Summary text */}
      <p className="text-sm text-surface-600 leading-relaxed">{text}</p>

      {/* Key points */}
      {key_points && key_points.length > 0 && (
        <div className="mt-4 pt-4 border-t border-surface-100">
          <p className="text-xs font-semibold text-surface-500 mb-2.5 uppercase tracking-wide">要点</p>
          <ul className="space-y-2">
            {key_points.map((point, i) => (
              <li key={i} className="flex gap-2.5 text-sm text-surface-600">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-accent-100 text-accent-600 text-[10px] font-bold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
