export default function LoadingSkeleton() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-pulse space-y-6">
      {/* Video info skeleton */}
      <div className="bg-white rounded-2xl shadow-md p-6">
        <div className="flex flex-col md:flex-row gap-6">
          <div className="w-full md:w-2/5 aspect-video bg-gray-200 rounded-xl" />
          <div className="flex-1 space-y-3">
            <div className="h-7 bg-gray-200 rounded w-3/4" />
            <div className="h-4 bg-gray-200 rounded w-1/2" />
            <div className="h-4 bg-gray-200 rounded w-2/3" />
            <div className="space-y-2 mt-4">
              <div className="h-3 bg-gray-100 rounded w-full" />
              <div className="h-3 bg-gray-100 rounded w-5/6" />
              <div className="h-3 bg-gray-100 rounded w-4/6" />
            </div>
          </div>
        </div>
      </div>
      {/* Summary skeleton */}
      <div className="bg-white rounded-2xl shadow-md p-6 space-y-3">
        <div className="h-6 bg-gray-200 rounded w-1/4" />
        <div className="space-y-2">
          <div className="h-4 bg-gray-100 rounded w-full" />
          <div className="h-4 bg-gray-100 rounded w-11/12" />
          <div className="h-4 bg-gray-100 rounded w-3/4" />
        </div>
      </div>
      {/* Download options skeleton */}
      <div className="bg-white rounded-2xl shadow-md p-6">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}
