import axios from 'axios';

// 生产环境使用环境变量中的后端地址，本地开发使用 Vite proxy
const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

export default api;

/**
 * Normalize error from API responses
 */
function normalizeError(err) {
  if (err.response?.data?.detail) {
    const d = err.response.data.detail;
    return {
      title: d.error || '请求失败',
      detail: d.detail || '未知错误',
      retryable: d.retryable ?? true,
    };
  }
  if (err.code === 'ERR_CANCELED') {
    return { title: '请求已取消', detail: '', retryable: false };
  }
  return {
    title: '网络错误',
    detail: err.message || '无法连接到服务器',
    retryable: true,
  };
}

/**
 * POST /api/video/info
 */
export async function fetchVideoInfo(url, signal) {
  try {
    const { data } = await api.post('/video/info', { url }, { signal });
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: normalizeError(err) };
  }
}

/**
 * POST /api/video/summary
 */
export async function fetchVideoSummary(url, signal) {
  try {
    const { data } = await api.post('/video/summary', { url }, { signal });
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: normalizeError(err) };
  }
}

/**
 * POST /api/download — returns blob for file download
 */
export async function downloadVideo(url, formatId, type, onProgress) {
  try {
    const response = await api.post('/download', { url, format_id: formatId, type }, {
      responseType: 'blob',
      timeout: 600000,
      onDownloadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      },
    });

    // Extract filename from Content-Disposition header
    const disposition = response.headers['content-disposition'];
    let filename = 'download';
    if (disposition) {
      const match = disposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/);
      if (match) {
        filename = decodeURIComponent(match[1]);
      }
    }

    // Trigger browser download
    const blobUrl = URL.createObjectURL(response.data);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);

    return { ok: true };
  } catch (err) {
    return { ok: false, error: normalizeError(err) };
  }
}
