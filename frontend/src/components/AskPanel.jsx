import { useState } from 'react';
import { Loader2, Send, MessageCircle, Sparkles } from 'lucide-react';
import api from '../api/client';

export default function AskPanel({ url, title }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim() || !url) return;
    setLoading(true);
    setError('');
    setAnswer('');
    try {
      const { data } = await api.post('/video/ask', { url, question: question.trim() });
      setAnswer(data.answer);
    } catch {
      setError('问答失败，请重试');
    }
    setLoading(false);
  };

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-5">
      <h3 className="text-sm font-bold text-surface-700 mb-4 flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-accent-100 flex items-center justify-center">
          <MessageCircle size={14} className="text-accent-600" />
        </div>
        AI 问答
        <span className="text-xs text-surface-400 font-normal">基于视频内容提问</span>
      </h3>

      <form onSubmit={handleAsk} className="flex gap-2 mb-4">
        <input
          type="text"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder={title ? `关于「${title.slice(0, 30)}...」提出问题...` : '输入你想问的问题...'}
          disabled={loading}
          className="flex-1 px-4 py-2.5 rounded-xl text-sm bg-surface-50 border-2 border-surface-200 text-surface-800 placeholder-surface-400 outline-none focus:border-accent-400 focus:ring-4 focus:ring-accent-500/10 transition-all"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="px-4 py-2.5 rounded-xl bg-accent-600 hover:bg-accent-700 disabled:opacity-40 text-white text-sm font-semibold transition-all shadow-md shadow-accent-500/20 flex items-center gap-1.5"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          提问
        </button>
      </form>

      {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

      {answer && (
        <div className="bg-surface-50 rounded-xl p-4 border border-surface-200">
          <div className="flex items-start gap-2.5">
            <div className="w-6 h-6 rounded-lg bg-accent-100 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Sparkles size={12} className="text-accent-600" />
            </div>
            <p className="text-sm text-surface-700 leading-relaxed">{answer}</p>
          </div>
        </div>
      )}

      {!answer && !loading && !error && (
        <p className="text-surface-400 text-sm text-center py-8">输入问题了解视频更多内容</p>
      )}
    </div>
  );
}
