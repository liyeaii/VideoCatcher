import { useState, useRef, useCallback } from 'react';
import { fetchVideoInfo, fetchVideoSummary, downloadVideo } from '../api/client';

export function useVideoData() {
  const [phase, setPhase] = useState('idle'); // idle | loading | loaded | error
  const [videoInfo, setVideoInfo] = useState(null);
  const [summary, setSummary] = useState(null);
  const [summaryError, setSummaryError] = useState(null);
  const [error, setError] = useState(null);
  const [lastUrl, setLastUrl] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);
  const [downloadProgress, setDownloadProgress] = useState({});

  const abortRef = useRef(null);

  const cancelPending = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
  }, []);

  const submitUrl = useCallback(async (url) => {
    cancelPending();
    const controller = new AbortController();
    abortRef.current = controller;

    setPhase('loading');
    setVideoInfo(null);
    setSummary(null);
    setSummaryError(null);
    setError(null);
    setLastUrl(url);

    // Fetch info + summary in parallel
    const [infoResult, summaryResult] = await Promise.allSettled([
      fetchVideoInfo(url, controller.signal),
      fetchVideoSummary(url, controller.signal),
    ]);

    // If cancelled, don't update state
    if (controller.signal.aborted) return;

    // Handle info result
    if (infoResult.status === 'fulfilled' && infoResult.value.ok) {
      setVideoInfo(infoResult.value.data);
    } else {
      const err = infoResult.status === 'fulfilled' ? infoResult.value.error : { title: '请求失败', detail: '', retryable: true };
      setError(err);
      setPhase('error');
      return;
    }

    // Handle summary result
    if (summaryResult.status === 'fulfilled') {
      if (summaryResult.value.ok) {
        setSummary(summaryResult.value.data);
      } else {
        setSummaryError(summaryResult.value.error);
      }
    }

    setPhase('loaded');
  }, [cancelPending]);

  const retry = useCallback(() => {
    if (lastUrl) {
      submitUrl(lastUrl);
    } else {
      setPhase('idle');
      setError(null);
    }
  }, [lastUrl, submitUrl]);

  const reset = useCallback(() => {
    cancelPending();
    setPhase('idle');
    setVideoInfo(null);
    setSummary(null);
    setSummaryError(null);
    setError(null);
    setLastUrl('');
    setDownloadingId(null);
    setDownloadProgress({});
  }, [cancelPending]);

  const download = useCallback(async (url, formatId, type) => {
    setDownloadingId(formatId);
    setDownloadProgress((prev) => ({ ...prev, [formatId]: 0 }));

    const result = await downloadVideo(url, formatId, type, (pct) => {
      setDownloadProgress((prev) => ({ ...prev, [formatId]: pct }));
    });

    setDownloadingId(null);
    return result;
  }, []);

  return {
    phase, videoInfo, summary, summaryError, error, lastUrl,
    downloadingId, downloadProgress,
    submitUrl, retry, reset, download,
  };
}
