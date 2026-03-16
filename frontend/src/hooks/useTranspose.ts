import { useCallback, useEffect, useState } from 'react'
import type { ApiMetaResponse, ScoreJson, Warning, TargetKey, TransposeResponse } from '../types/api'

const DEFAULT_MAX_SIZE_MB = 20
const DEFAULT_ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']

type UploadRules = {
  allowedImageTypes: string[]
  maxSizeMB: number
}

type ServiceStatus = {
  systemOnline: boolean
  apiReady: boolean
  isCheckingStatus: boolean
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

async function transpose(params: { image: File; targetKey: TargetKey }): Promise<TransposeResponse> {
  const formData = new FormData()
  formData.append('image', params.image)
  formData.append('target_key', params.targetKey)
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
}> {
  try {
    const response = await fetch('/api/meta', { cache: 'no-store' })
    if (!response.ok) {
      return { systemOnline: true, apiReady: false, meta: null }
    }
    let data: unknown
    try {
      data = await response.json()
    } catch {
      return { systemOnline: true, apiReady: false, meta: null }
    }
    if (!isApiMetaResponse(data)) {
      return { systemOnline: true, apiReady: false, meta: null }
    }
    return { systemOnline: true, apiReady: true, meta: data }
  } catch {
    return { systemOnline: false, apiReady: false, meta: null }
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
      r.score_json !== undefined
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
  return Array.isArray(r.allowed_image_types) && typeof r.max_image_size_mb === 'number'
}

function formatAllowedTypes(allowedImageTypes: string[]): string {
  const set = new Set(allowedImageTypes.map((t) => t.toLowerCase()))
  const labels: string[] = []
  if (set.has('image/png')) labels.push('PNG')
  if (set.has('image/jpeg') || set.has('image/jpg')) labels.push('JPG')
  if (set.has('image/webp')) labels.push('WEBP')
  if (labels.length === 0) return '支持格式'
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
  const [pageState, setPageState] = useState<PageState>({ status: 'idle' })
  const [uploadRules, setUploadRules] = useState<UploadRules>({
    allowedImageTypes: DEFAULT_ALLOWED_IMAGE_TYPES,
    maxSizeMB: DEFAULT_MAX_SIZE_MB,
  })
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus>({
    systemOnline: false,
    apiReady: false,
    isCheckingStatus: true,
  })

  useEffect(() => {
    let cancelled = false
    let timer: number | null = null
    const loadRules = async () => {
      try {
        const { systemOnline, apiReady, meta } = await checkServiceStatus()
        if (cancelled) return
        setServiceStatus({
          systemOnline,
          apiReady,
          isCheckingStatus: false,
        })
        if (meta) {
          setUploadRules({
            allowedImageTypes:
              meta.allowed_image_types.length > 0 ? meta.allowed_image_types : DEFAULT_ALLOWED_IMAGE_TYPES,
            maxSizeMB: meta.max_image_size_mb > 0 ? meta.max_image_size_mb : DEFAULT_MAX_SIZE_MB,
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
    if (!selectedFile || !selectedPreviewUrl) return
    setPageState({ status: 'loading', previewUrl: selectedPreviewUrl })
    try {
      const res = await transpose({ image: selectedFile, targetKey })
      if (res.success) {
        setPageState({
          status: 'success',
          originalPreview: selectedPreviewUrl,
          outputImage: res.output_image,
          scoreJson: res.score_json,
          warnings: res.warnings ?? [],
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
  }, [selectedFile, selectedPreviewUrl, targetKey])

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
    controlError,
    pageState,
    serviceStatus,
    
    // 计算属性
    isLoading,
    isSuccess,
    leftImageUrl,
    
    // 操作方法
    setTargetKey,
    handleFileChange,
    handleSubmit,
    handleRetry,
    handleContinueUpload,
  }
}
