export default function Footer() {
  return (
    <footer className="mt-auto py-8 text-center border-t border-surface-100">
      <div className="max-w-4xl mx-auto px-4">
        <p className="text-xs text-surface-400">
          Powered by <span className="font-semibold text-surface-500">yt-dlp</span> + <span className="font-semibold text-surface-500">AI</span>
          <span className="mx-2 text-surface-300">|</span>
          仅供个人学习使用
        </p>
        <p className="text-[10px] text-surface-300 mt-1">
          VideoCatcher &copy; {new Date().getFullYear()}
        </p>
      </div>
    </footer>
  );
}
