import URLInput from './components/URLInput';
import VideoInfo from './components/VideoInfo';
import AISummary from './components/AISummary';
import DownloadOptions from './components/DownloadOptions';
import LoadingSkeleton from './components/LoadingSkeleton';
import ErrorMessage from './components/ErrorMessage';
import Footer from './components/Footer';
import { useVideoData } from './hooks/useVideoData';

export default function App() {
  const {
    phase,
    videoInfo,
    summary,
    summaryError,
    error,
    downloadingId,
    downloadProgress,
    submitUrl,
    retry,
    reset,
    download: triggerDownload,
  } = useVideoData();

  const handleDownload = async (formatId) => {
    if (!videoInfo?.webpage_url) return;
    await triggerDownload(videoInfo.webpage_url, formatId);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero / Input area — always visible */}
      <URLInput onSubmit={submitUrl} isLoading={phase === 'loading'} />

      {/* Content area */}
      {phase === 'loading' && <LoadingSkeleton />}

      {phase === 'error' && (
        <ErrorMessage
          error={error}
          onRetry={retry}
          onReset={reset}
        />
      )}

      {phase === 'loaded' && (
        <>
          <div className="space-y-4 mt-6">
            <VideoInfo videoInfo={videoInfo} />
            <AISummary summary={summary} error={summaryError} />
            <DownloadOptions
              formats={videoInfo?.formats || []}
              onDownload={handleDownload}
              downloadingId={downloadingId}
              downloadProgress={downloadProgress}
            />
          </div>
        </>
      )}

      {/* Footer — always visible */}
      <Footer />
    </div>
  );
}
