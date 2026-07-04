export default function LoadingSkeleton() {
  return (
    <div className="animate-fade-in space-y-5">
      {/* Video info skeleton */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="flex flex-col sm:flex-row">
          <div className="sm:w-2/5 h-48 sm:h-56 skeleton rounded-none" />
          <div className="flex-1 p-5 space-y-3">
            <div className="skeleton h-5 w-3/4" />
            <div className="skeleton h-4 w-1/3" />
            <div className="space-y-2 mt-3">
              <div className="skeleton h-3 w-full" />
              <div className="skeleton h-3 w-5/6" />
              <div className="skeleton h-3 w-2/3" />
            </div>
          </div>
        </div>
      </div>

      {/* Download grid skeleton */}
      <div className="glass-card rounded-2xl p-5">
        <div className="skeleton h-5 w-28 mb-4" />
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton h-24 rounded-xl" />
          ))}
        </div>
      </div>

      <p className="text-center text-surface-400 text-xs animate-pulse">
        正在解析视频信息...
      </p>
    </div>
  );
}
