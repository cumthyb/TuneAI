import { useCallback, useEffect, useState } from 'react'
import type { ApiMetaResponse, ScoreJson, Warning, TargetKey, TransposeResponse } from '../types/api'

type UploadRules = {
  allowedImageTypes: string[]
  maxSizeMB: number
}

type ServiceStatus = {
  systemOnline: boolean
  apiReady: boolean
  isCheckingStatus: boolean
}

const META_CONFIG_ERROR_MESSAGE =
  '后端配置缺失或无效：请检查 config.json 中 provider_policy.default_provider 与 providers 配置'

type ProviderOptions = {
  llmProviders: string[]
  visionLlmProviders: string[]
  ocrProviders: string[]
}

const logger = {
  error(message: string, payload?: Record<string, unknown>) {
    if (payload) {
      console.error(`[tuneai] ${message}`, payload)
      return
    }
    console.error(`[tuneai] ${message}`)
  },
}

async function transpose(params: {
  image: File
  targetKey: TargetKey
  llmProvider: string
  visionLlmProvider: string
  ocrProvider: string
}): Promise<TransposeResponse> {
  const formData = new FormData()
  formData.append('image', params.image)
  formData.append('target_key', params.targetKey)
  formData.append('llm_provider', params.llmProvider)
  formData.append('vision_llm_provider', params.visionLlmProvider)
  formData.append('ocr_provider', params.ocrProvider)
  const response = await fetch('/api/transpose', {
    method: 'POST',
    body: formData,
  })
  let data: unknown
  try {
    data = await response.json()
  } catch {
    throw new Error(`请求失败（HTTP ${response.status}）：服务器返回非 JSON`)
  }
  if (!isTransposeResponse(data)) {
    throw new Error(`请求失败（HTTP ${response.status}）：返回数据格式不正确`)
  }
  return data
}

async function checkServiceStatus(): Promise<{
  systemOnline: boolean
  apiReady: boolean
  meta: ApiMetaResponse | null
  errorMessage: string | null
}> {
  try {
    const response = await fetch('/api/meta', { cache: 'no-store' })
    if (!response.ok) {
      return { systemOnline: true, apiReady: false, meta: null, errorMessage: META_CONFIG_ERROR_MESSAGE }
    }
    let data: unknown
    try {
      data = await response.json()
    } catch {
      return { systemOnline: true, apiReady: false, meta: null, errorMessage: META_CONFIG_ERROR_MESSAGE }
    }
    if (!isApiMetaResponse(data)) {
      return { systemOnline: true, apiReady: false, meta: null, errorMessage: META_CONFIG_ERROR_MESSAGE }
    }
    if (!data.llm_providers.length || !data.vision_llm_providers.length || !data.ocr_providers.length) {
      return { systemOnline: true, apiReady: false, meta: null, errorMessage: '未配置 API Key，请在 config.json 中填写 providers 的 api_key' }
    }
    return { systemOnline: true, apiReady: true, meta: data, errorMessage: null }
  } catch {
    return { systemOnline: false, apiReady: false, meta: null, errorMessage: '无法连接后端服务，请确认服务已启动' }
  }
}

function isTransposeResponse(value: unknown): value is TransposeResponse {
  if (!value || typeof value !== 'object') return false
  const r = value as Record<string, unknown>
  if (r.success === true) {
    return (
      typeof r.output_image === 'string' &&
      typeof r.processing_time_ms === 'number' &&
      typeof r.request_id === 'string' &&
      Array.isArray(r.warnings) &&
      isScoreJson(r.score_json)
    )
  }
  if (r.success === false) {
    return (
      typeof r.error_code === 'string' &&
      typeof r.error_message === 'string' &&
      typeof r.request_id === 'string'
    )
  }
  return false
}

function isApiMetaResponse(value: unknown): value is ApiMetaResponse {
  if (!value || typeof value !== 'object') return false
  const r = value as Record<string, unknown>
  return (
    Array.isArray(r.allowed_image_types) &&
    typeof r.max_image_size_mb === 'number' &&
    Array.isArray(r.providers) &&
    typeof r.default_provider === 'string' &&
    Array.isArray(r.llm_providers) &&
    Array.isArray(r.vision_llm_providers) &&
    Array.isArray(r.ocr_providers) &&
    typeof r.default_llm_provider === 'string' &&
    typeof r.default_vision_llm_provider === 'string' &&
    typeof r.default_ocr_provider === 'string'
  )
}

function normalizeProviders(providers: unknown): string[] {
  if (!Array.isArray(providers)) {
    throw new Error('api/meta providers 必须是数组')
  }
  const safe = providers
    .filter((item): item is string => typeof item === 'string')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean)
  if (safe.length === 0) {
    throw new Error('api/meta providers 不能为空')
  }
  return Array.from(new Set(safe))
}

function normalizeProviderValue(value: unknown): string {
  if (typeof value !== 'string') {
    throw new Error('provider 值必须是字符串')
  }
  const normalized = value.trim().toLowerCase()
  if (!normalized) {
    throw new Error('provider 值不能为空')
  }
  return normalized
}

function isScoreJson(value: unknown): value is ScoreJson {
  if (!value || typeof value !== 'object') return false
  const r = value as Record<string, unknown>
  const sourceKey = r.source_key
  const targetKey = r.target_key
  return (
    typeof r.score_id === 'string' &&
    Array.isArray(r.events) &&
    !!sourceKey &&
    typeof sourceKey === 'object' &&
    typeof (sourceKey as Record<string, unknown>).label === 'string' &&
    typeof (sourceKey as Record<string, unknown>).tonic === 'string' &&
    !!targetKey &&
    typeof targetKey === 'object' &&
    typeof (targetKey as Record<string, unknown>).label === 'string' &&
    typeof (targetKey as Record<string, unknown>).tonic === 'string'
  )
}

function formatAllowedTypes(allowedImageTypes: string[]): string {
  const set = new Set(allowedImageTypes.map((t) => t.toLowerCase()))
  const labels: string[] = []
  if (set.has('image/png')) labels.push('PNG')
  if (set.has('image/jpeg') || set.has('image/jpg')) labels.push('JPG')
  if (set.has('image/webp')) labels.push('WEBP')
  if (labels.length === 0) {
    throw new Error('allowed_image_types 不包含受支持的显示格式')
  }
  if (labels.length === 1) return labels[0]
  if (labels.length === 2) return `${labels[0]} 或 ${labels[1]}`
  return `${labels.slice(0, -1).join('、')} 或 ${labels[labels.length - 1]}`
}

function validateFile(f: File, rules: UploadRules): string | null {
  const okType = rules.allowedImageTypes.includes(f.type)
  if (!okType) return `请上传 ${formatAllowedTypes(rules.allowedImageTypes)} 图片`
  if (f.size > rules.maxSizeMB * 1024 * 1024) return `图片大小不超过 ${rules.maxSizeMB}MB`
  return null
}

type PageState =
  | { status: 'idle' }
  | { status: 'loading'; previewUrl: string }
  | {
      status: 'error'
      error: string
      errorCode?: string
      requestId?: string
    }
  | {
      status: 'success'
      originalPreview: string
      outputImage: string
      scoreJson: ScoreJson
      warnings: Warning[]
      requestId: string
      processingTimeMs: number
    }

export function useTranspose() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedPreviewUrl, setSelectedPreviewUrl] = useState<string | null>(null)
  const [targetKey, setTargetKey] = useState<TargetKey>('C')
  const [controlError, setControlError] = useState<string | null>(null)
  const [serviceError, setServiceError] = useState<string | null>(null)
  const [pageState, setPageState] = useState<PageState>({ status: 'idle' })
  const [uploadRules, setUploadRules] = useState<UploadRules>({
    allowedImageTypes: [],
    maxSizeMB: 0,
  })
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus>({
    systemOnline: false,
    apiReady: false,
    isCheckingStatus: true,
  })
  const [providerOptions, setProviderOptions] = useState<ProviderOptions>({
    llmProviders: [],
    visionLlmProviders: [],
    ocrProviders: [],
  })
  const [selectedLlmProvider, setSelectedLlmProvider] = useState<string>('')
  const [selectedVisionLlmProvider, setSelectedVisionLlmProvider] = useState<string>('')
  const [selectedOcrProvider, setSelectedOcrProvider] = useState<string>('')

  useEffect(() => {
    let cancelled = false
    let timer: number | null = null
    const loadRules = async () => {
      try {
        const { systemOnline, apiReady, meta, errorMessage } = await checkServiceStatus()
        if (cancelled) return
        setServiceStatus({
          systemOnline,
          apiReady,
          isCheckingStatus: false,
        })
        setServiceError(errorMessage)
        if (meta) {
          if (meta.allowed_image_types.length === 0) {
            throw new Error('api/meta 返回的 allowed_image_types 不能为空')
          }
          if (meta.max_image_size_mb <= 0) {
            throw new Error('api/meta 返回的 max_image_size_mb 必须大于 0')
          }
          setUploadRules({
            allowedImageTypes: meta.allowed_image_types,
            maxSizeMB: meta.max_image_size_mb,
          })
          const llmProviders = normalizeProviders(meta.llm_providers)
          const visionLlmProviders = normalizeProviders(meta.vision_llm_providers)
          const ocrProviders = normalizeProviders(meta.ocr_providers)
          const defaultLlmProvider = normalizeProviderValue(meta.default_llm_provider)
          const defaultVisionLlmProvider = normalizeProviderValue(meta.default_vision_llm_provider)
          const defaultOcrProvider = normalizeProviderValue(meta.default_ocr_provider)
          if (!llmProviders.includes(defaultLlmProvider)) {
            throw new Error(`default_llm_provider 未包含在 llm_providers 中: ${defaultLlmProvider}`)
          }
          if (!visionLlmProviders.includes(defaultVisionLlmProvider)) {
            throw new Error(`default_vision_llm_provider 未包含在 vision_llm_providers 中: ${defaultVisionLlmProvider}`)
          }
          if (!ocrProviders.includes(defaultOcrProvider)) {
            throw new Error(`default_ocr_provider 未包含在 ocr_providers 中: ${defaultOcrProvider}`)
          }

          setProviderOptions({ llmProviders, visionLlmProviders, ocrProviders })

          setSelectedLlmProvider((prev) => {
            if (prev && llmProviders.includes(prev)) return prev
            return defaultLlmProvider
          })
          setSelectedVisionLlmProvider((prev) => {
            if (prev && visionLlmProviders.includes(prev)) return prev
            return defaultVisionLlmProvider
          })
          setSelectedOcrProvider((prev) => {
            if (prev && ocrProviders.includes(prev)) return prev
            return defaultOcrProvider
          })
        }
      } catch (err) {
        if (cancelled) return
        const message = err instanceof Error ? err.message : 'unknown error'
        logger.error('load api meta failed', { error: message })
        setServiceStatus({
          systemOnline: false,
          apiReady: false,
          isCheckingStatus: false,
        })
      }
    }
    void loadRules()
    timer = window.setInterval(() => {
      void loadRules()
    }, 10000)
    return () => {
      cancelled = true
      if (timer != null) {
        window.clearInterval(timer)
      }
    }
  }, [])

  // 为选中的文件维护 object URL，清除时 revoke
  useEffect(() => {
    if (!selectedFile) {
      if (selectedPreviewUrl) {
        URL.revokeObjectURL(selectedPreviewUrl)
        setSelectedPreviewUrl(null)
      }
      return
    }
    const url = URL.createObjectURL(selectedFile)
    setSelectedPreviewUrl(url)
    return () => {
      URL.revokeObjectURL(url)
      setSelectedPreviewUrl(null)
    }
  }, [selectedFile])

  const handleFileChange = useCallback((file: File | null) => {
    setControlError(null)
    // 选择新文件或清除文件时，若当前是成功/错误状态则重置，
    // 防止旧的 Object URL 被 revoke 后 originalPreview 仍被引用
    setPageState((prev) => (prev.status !== 'idle' && prev.status !== 'loading' ? { status: 'idle' } : prev))
    if (!file) {
      setSelectedFile(null)
      return
    }
    const err = validateFile(file, uploadRules)
    if (err) {
      setControlError(err)
      setSelectedFile(null)
      return
    }
    setSelectedFile(file)
  }, [uploadRules])

  const handleSubmit = useCallback(async () => {
    if (!selectedFile || !selectedPreviewUrl || !selectedLlmProvider || !selectedVisionLlmProvider || !selectedOcrProvider) {
      setPageState({ status: 'error', error: '提交参数不完整：缺少文件、预览地址或模型 provider' })
      return
    }
    setPageState({ status: 'loading', previewUrl: selectedPreviewUrl })
    try {
      const res = await transpose({
        image: selectedFile,
        targetKey,
        llmProvider: selectedLlmProvider,
        visionLlmProvider: selectedVisionLlmProvider,
        ocrProvider: selectedOcrProvider,
      })
      if (res.success) {
        setPageState({
          status: 'success',
          originalPreview: selectedPreviewUrl,
          outputImage: res.output_image,
          scoreJson: res.score_json,
          warnings: res.warnings,
          requestId: res.request_id,
          processingTimeMs: res.processing_time_ms,
        })
      } else {
        setPageState({
          status: 'error',
          error: res.error_message,
          errorCode: res.error_code,
          requestId: res.request_id,
        })
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '网络或服务器错误'
      logger.error('transpose fetch failed', { error: message })
      setPageState({ status: 'error', error: message })
    }
  }, [selectedFile, selectedPreviewUrl, selectedLlmProvider, selectedVisionLlmProvider, selectedOcrProvider, targetKey])

  const handleRetry = useCallback(() => {
    setPageState({ status: 'idle' })
  }, [])

  const handleContinueUpload = useCallback(() => {
    setSelectedFile(null)
    setPageState({ status: 'idle' })
  }, [])

  const isLoading = pageState.status === 'loading'
  const isSuccess = pageState.status === 'success'

  // 左侧图片 URL：成功时显示原图，否则显示选中的预览
  const leftImageUrl =
    pageState.status === 'success'
      ? pageState.originalPreview
      : selectedPreviewUrl

  return {
    // 状态
    selectedFile,
    selectedPreviewUrl,
    targetKey,
    controlError: controlError !== null ? controlError : serviceError,
    pageState,
    serviceStatus,
    providerOptions,
    selectedLlmProvider,
    selectedVisionLlmProvider,
    selectedOcrProvider,
    
    // 计算属性
    isLoading,
    isSuccess,
    leftImageUrl,
    
    // 操作方法
    setTargetKey,
    setSelectedLlmProvider,
    setSelectedVisionLlmProvider,
    setSelectedOcrProvider,
    handleFileChange,
    handleSubmit,
    handleRetry,
    handleContinueUpload,
  }
}
