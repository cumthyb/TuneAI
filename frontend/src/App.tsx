export default function App() {
  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-2xl font-semibold text-gray-900">
          TuneAI 简谱移调
        </h1>
        <p className="mt-2 text-gray-600">
          上传 PNG/JPG 简谱图，选择目标调，获取移调后的图片与解析结果。
        </p>
        <div className="mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <p className="text-sm text-gray-500">
            上传区、目标调选择、结果对比与下载等模块可在此处接续实现。
          </p>
        </div>
      </div>
    </main>
  )
}
