import { useTranspose } from './hooks/useTranspose'
import TechBackground from './components/TechBackground'
import Header from './components/Header'
import InputPanel from './components/InputPanel'
import OutputPanel from './components/OutputPanel'
import ResultSection from './components/ResultSection'

export default function App() {
  const {
    selectedFile,
    targetKey,
    controlError,
    pageState,
    isLoading,
    isSuccess,
    leftImageUrl,
    setTargetKey,
    handleFileChange,
    handleSubmit,
    handleRetry,
    handleContinueUpload,
  } = useTranspose()

  return (
    <main className="relative flex min-h-screen flex-col bg-[#050508]">
      {/* 科技感背景 */}
      <TechBackground />
      
      {/* 顶部霓虹发光条 */}
      <div className="relative h-1 w-full overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500" />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-[shimmer_2s_infinite]" />
      </div>

      {/* 顶部控制区 */}
      <Header
        selectedFile={selectedFile}
        targetKey={targetKey}
        controlError={controlError}
        isLoading={isLoading}
        onTargetKeyChange={setTargetKey}
        onSubmit={handleSubmit}
      />

      {/* 主内容区：左右面板 */}
      <div className="flex-1 px-4 py-6 sm:px-6">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 lg:grid-cols-2 lg:gap-8">
          {/* 左侧面板：输入/原图 */}
          <InputPanel
            selectedFile={selectedFile}
            leftImageUrl={leftImageUrl}
            scoreJson={pageState.status === 'success' ? pageState.scoreJson : null}
            isLoading={isLoading}
            isSuccess={isSuccess}
            onFileChange={handleFileChange}
          />

          {/* 右侧面板：输出/结果 */}
          <OutputPanel
            pageState={pageState}
            onRetry={handleRetry}
          />
        </div>

        {/* 成功后的结果展示区域 */}
        {pageState.status === 'success' && (
          <ResultSection
            processingTimeMs={pageState.processingTimeMs}
            warnings={pageState.warnings}
            outputImage={pageState.outputImage}
            scoreJson={pageState.scoreJson}
            requestId={pageState.requestId}
            onContinue={handleContinueUpload}
          />
        )}
      </div>
    </main>
  )
}
