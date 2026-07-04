import URLInput from './components/URLInput';
import VideoInfo from './components/VideoInfo';
import AISummary from './components/AISummary';
import DownloadOptions from './components/DownloadOptions';
import LoadingSkeleton from './components/LoadingSkeleton';
import ErrorMessage from './components/ErrorMessage';
import MindMapPanel from './components/MindMapPanel';
import SubtitlesPanel from './components/SubtitlesPanel';
import AskPanel from './components/AskPanel';
import Footer from './components/Footer';
import { useVideoData } from './hooks/useVideoData';
import { Sparkles, Download, FileText, Brain, MessageCircle, Globe } from 'lucide-react';

const FEATURES = [
  { icon: Globe, label: '1000+ 网站', desc: 'YouTube、Bilibili、TikTok 等' },
  { icon: Sparkles, label: 'AI 智能总结', desc: '基于 Claude/DeepSeek' },
  { icon: Download, label: '多格式下载', desc: '视频+音频/仅视频/仅音频' },
  { icon: FileText, label: '字幕提取', desc: '自动获取中英文字幕' },
  { icon: Brain, label: '思维导图', desc: '视频内容结构化呈现' },
  { icon: MessageCircle, label: 'AI 问答', desc: '基于视频内容自由提问' },
];

export default function App() {
  const {
    phase, videoInfo, summary, summaryError, error,
    downloadingId, downloadProgress,
    submitUrl, retry, reset, download: triggerDownload,
  } = useVideoData();

  const handleDownload = async (formatId, type) => {
    if (!videoInfo?.webpage_url) return;
    await triggerDownload(videoInfo.webpage_url, formatId, type);
  };

  const showResults = phase === 'loaded' && videoInfo;
  const isIdle = phase === 'idle';

  return (
    <div className="min-h-screen bg-surface-50 text-surface-900 flex flex-col">
      {/* ── Hero / Input Section ── */}
      <URLInput onSubmit={submitUrl} isLoading={phase === 'loading'} isIdle={isIdle} />

      {/* ── Loading ── */}
      {phase === 'loading' && (
        <div className="max-w-4xl mx-auto px-4 w-full -mt-4">
          <LoadingSkeleton />
        </div>
      )}

      {/* ── Error ── */}
      {phase === 'error' && (
        <div className="max-w-4xl mx-auto px-4 w-full -mt-4">
          <ErrorMessage error={error} onRetry={retry} onReset={reset} />
        </div>
      )}

      {/* ── Results: Video Info + AI Summary + Download on ONE page ── */}
      {showResults && (
        <div className="max-w-5xl mx-auto px-4 w-full -mt-6 pb-8">
          <div className="animate-stagger space-y-5">
            {/* Row 1: Video Info + AI Summary side by side on desktop */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
              <div className="lg:col-span-3">
                <VideoInfo videoInfo={videoInfo} />
              </div>
              <div className="lg:col-span-2">
                <AISummary summary={summary} error={summaryError} />
              </div>
            </div>

            {/* Row 2: Download Options - full width */}
            <DownloadOptions
              formats={videoInfo?.formats || []}
              onDownload={handleDownload}
              downloadingId={downloadingId}
              downloadProgress={downloadProgress}
            />

            {/* Row 3: Advanced features in collapsible panels */}
            <details className="glass-card rounded-2xl p-5 group cursor-pointer">
              <summary className="flex items-center gap-2 text-sm font-semibold text-surface-600 select-none list-none">
                <Brain size={18} className="text-accent-500" />
                高级功能
                <span className="text-xs text-surface-400 ml-auto group-open:hidden">展开</span>
                <span className="text-xs text-surface-400 ml-auto hidden group-open:inline">收起</span>
              </summary>
              <div className="mt-5 space-y-4">
                <MindMapPanel url={videoInfo?.webpage_url} title={videoInfo?.title} />
                <SubtitlesPanel url={videoInfo?.webpage_url} />
                <AskPanel url={videoInfo?.webpage_url} title={videoInfo?.title} />
              </div>
            </details>
          </div>
        </div>
      )}

      {/* ── Idle state: features showcase ── */}
      {isIdle && (
        <div className="flex-1 flex flex-col items-center justify-center -mt-12 pb-20">
          <div className="max-w-3xl mx-auto px-4 text-center">
            <p className="text-surface-400 text-sm mb-10">
              支持 YouTube、Bilibili、TikTok、抖音 等 1000+ 网站
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {FEATURES.map((f, i) => {
                const Icon = f.icon;
                return (
                  <div key={i} className="glass-card rounded-xl p-5 text-center animate-fade-in-up"
                    style={{ animationDelay: `${i * 0.08}s` }}>
                    <Icon size={24} className="text-accent-500 mx-auto mb-2" />
                    <p className="text-sm font-semibold text-surface-800 mb-0.5">{f.label}</p>
                    <p className="text-xs text-surface-400">{f.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}
