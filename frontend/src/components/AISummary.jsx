import { Sparkles, Circle } from 'lucide-react';

export default function AISummary({ summary, error }) {
  // If there's an error and no summary, show error state
  if (error && !summary) {
    return (
      <div className="max-w-3xl mx-auto px-4 animate-fade-in-delay-1">
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={18} className="text-amber-500" />
            <span className="text-sm font-semibold text-amber-700">AI 智能总结</span>
          </div>
          <p className="text-sm text-amber-600">
            AI 总结暂时不可用：{error.detail || '服务异常'}
          </p>
        </div>
      </div>
    );
  }

  // If no summary at all, show empty state
  if (!summary) return null;

  const { summary: text, key_points } = summary;

  return (
    <div className="max-w-3xl mx-auto px-4 animate-fade-in-delay-1">
      <div className="bg-white rounded-2xl shadow-md border-l-4 border-purple-500 p-5 md:p-6">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
            <Sparkles size={16} className="text-purple-600" />
          </div>
          <div>
            <span className="text-sm font-semibold text-purple-700">AI 智能总结</span>
            <span className="text-xs text-gray-400 ml-2">由 Claude 生成</span>
          </div>
        </div>

        {/* Summary text */}
        {text && (
          <p className="text-sm text-gray-700 leading-relaxed mb-4">{text}</p>
        )}

        {/* Key points */}
        {key_points && key_points.length > 0 && (
          <div className="space-y-2">
            {key_points.map((point, idx) => (
              <div key={idx} className="flex items-start gap-2">
                <Circle size={8} className="mt-2 text-purple-400 flex-shrink-0 fill-purple-400" />
                <span className="text-sm text-gray-600">{point}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
