/**
 * API 请求/响应类型（与后端 /api/transpose 契约一致）
 */

/** 支持的目标调（与文档 8.2 一致） */
export const TARGET_KEYS = [
  'C',
  'C#',
  'Db',
  'D',
  'D#',
  'Eb',
  'E',
  'F',
  'F#',
  'Gb',
  'G',
  'G#',
  'Ab',
  'A',
  'A#',
  'Bb',
  'B',
] as const

export type TargetKey = (typeof TARGET_KEYS)[number]

/** 成功响应 */
export interface TransposeSuccessResponse {
  success: true
  output_image: string // base64
  score_json: ScoreJson
  warnings: Warning[]
  processing_time_ms: number
  request_id: string
}

/** 错误响应 */
export interface TransposeErrorResponse {
  success: false
  error_code: string
  error_message: string
  request_id: string
}

export type TransposeResponse = TransposeSuccessResponse | TransposeErrorResponse

export interface Warning {
  type: string
  measure?: number
  message: string
}

/** 乐谱 JSON 简化结构（与文档 §7 对应） */
export interface ScoreJson {
  score_id?: string
  source_key?: { label: string; tonic: string; mode?: string }
  target_key?: { label: string; tonic: string; mode?: string }
  measures?: unknown[]
  [key: string]: unknown
}
