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
    providerOptions,
    selectedLlmProvider,
    selectedVisionLlmProvider,
    selectedOcrProvider,
    controlError,
    pageState,
    serviceStatus,
    isLoading,
    isSuccess,
    leftImageUrl,
    setTargetKey,
    setSelectedLlmProvider,
    setSelectedVisionLlmProvider,
    setSelectedOcrProvider,
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
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-600" />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-[shimmer_2s_infinite]" />
      </div>

      {/* 顶部控制区 */}
      <Header
        selectedFile={selectedFile}
        targetKey={targetKey}
        llmProvider={selectedLlmProvider}
        llmProviders={providerOptions.llmProviders}
        visionLlmProvider={selectedVisionLlmProvider}
        visionLlmProviders={providerOptions.visionLlmProviders}
        ocrProvider={selectedOcrProvider}
        ocrProviders={providerOptions.ocrProviders}
        controlError={controlError}
        isLoading={isLoading}
        systemOnline={serviceStatus.systemOnline}
        apiReady={serviceStatus.apiReady}
        isCheckingStatus={serviceStatus.isCheckingStatus}
        onTargetKeyChange={setTargetKey}
        onLlmProviderChange={setSelectedLlmProvider}
        onVisionLlmProviderChange={setSelectedVisionLlmProvider}
        onOcrProviderChange={setSelectedOcrProvider}
        onSubmit={handleSubmit}
      />

      {/* 主内容区：左右面板 */}
      <div className="relative flex-1 px-4 py-6 sm:px-6 lg:px-8 xl:px-10">
        {/* 主区科技感装饰层 */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.05)_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_at_center,black_45%,transparent_85%)]" />
          <div className="absolute -left-24 top-10 h-72 w-72 rounded-full bg-indigo-500/15 blur-3xl" />
          <div className="absolute -right-24 bottom-0 h-72 w-72 rounded-full bg-violet-500/15 blur-3xl" />
        </div>

        <div className="relative grid w-full grid-cols-1 gap-6 lg:grid-cols-2 lg:gap-8">
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
          <div className="relative mt-8">
            <ResultSection
              processingTimeMs={pageState.processingTimeMs}
              warnings={pageState.warnings}
              outputImage={pageState.outputImage}
              scoreJson={pageState.scoreJson}
              requestId={pageState.requestId}
              onContinue={handleContinueUpload}
            />
          </div>
        )}
      </div>
    </main>
  )
}
