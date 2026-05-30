import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="text-8xl mb-6">📚</div>
        <h1 className="text-4xl font-bold text-slate-800 mb-3">Page Not Found</h1>
        <p className="text-slate-500 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex gap-3 justify-center">
          <Link href="/dashboard"
            className="bg-blue-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-blue-700 transition-colors">
            Go to Dashboard
          </Link>
          <Link href="/"
            className="border border-slate-200 px-6 py-2.5 rounded-xl font-medium hover:bg-slate-50 transition-colors">
            Home
          </Link>
        </div>
      </div>
    </div>
  );
}
