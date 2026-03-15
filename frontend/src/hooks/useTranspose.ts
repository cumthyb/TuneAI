import { useCallback, useEffect, useState } from 'react'
import { transpose } from '../lib/api'
import { logger } from '../lib/logger'
import type { ScoreJson, Warning, TargetKey } from '../types/api'

const MAX_SIZE_MB = 20

function validateFile(f: File): string | null {
  const okType = ['image/png', 'image/jpeg', 'image/jpg'].some((t) => f.type === t)
  if (!okType) return '请上传 PNG 或 JPG 图片'
  if (f.size > MAX_SIZE_MB * 1024 * 1024) return `图片大小不超过 ${MAX_SIZE_MB}MB`
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
    const err = validateFile(file)
    if (err) {
      setControlError(err)
      setSelectedFile(null)
      return
    }
    setSelectedFile(file)
  }, [])

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
