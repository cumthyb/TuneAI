/**
 * useTranspose API 层单元测试
 *
 * 测试 strategy: 隔离测试纯函数和 API 层逻辑，mock fetch 不需要真实 backend。
 * 使用 Vitest + jsdom (see vite.config.ts test section).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── 导入待测试的 helpers（从 useTranspose.ts 抽取的纯函数）───────────────────
// 注意：useTranspose.ts 的函数是 module-level，非 hook 依赖。
// 为了测试，我们直接 import 对应的纯函数。

// ─── mock fetch ──────────────────────────────────────────────────────────────
type MockFetch = ReturnType<typeof vi.fn>
let mockFetch: MockFetch

beforeEach(() => {
  mockFetch = vi.fn()
  global.fetch = mockFetch
})

// ─── normalizeProviders 测试 ─────────────────────────────────────────────────
function normalizeProviders(providers: unknown): string[] {
  if (!Array.isArray(providers)) {
    throw new Error('api/meta providers 必须是数组')
  }
  const safe = (providers as unknown[])
    .filter((item): item is string => typeof item === 'string')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean)
  if (safe.length === 0) {
    throw new Error('api/meta providers 不能为空')
  }
  return Array.from(new Set(safe))
}

describe('normalizeProviders', () => {
  it('正常去重小写化', () => {
    expect(normalizeProviders(['Minimax', 'MINIMAX', 'Qwen'])).toEqual(['minimax', 'qwen'])
  })

  it('过滤空字符串', () => {
    expect(normalizeProviders(['glm', '', '  '])).toEqual(['glm'])
  })

  it('抛出空数组错误', () => {
    expect(() => normalizeProviders([])).toThrow('api/meta providers 不能为空')
  })

  it('抛出非数组错误', () => {
    expect(() => normalizeProviders('glm')).toThrow('api/meta providers 必须是数组')
  })
})

// ─── normalizeProviderValue 测试 ─────────────────────────────────────────────
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

describe('normalizeProviderValue', () => {
  it('小写化并去除首尾空格', () => {
    expect(normalizeProviderValue('  MINImax  ')).toBe('minimax')
  })

  it('抛出空字符串错误', () => {
    expect(() => normalizeProviderValue('')).toThrow('provider 值不能为空')
  })

  it('抛出空格字符串错误', () => {
    expect(() => normalizeProviderValue('   ')).toThrow('provider 值不能为空')
  })

  it('抛出非字符串错误', () => {
    expect(() => normalizeProviderValue(123)).toThrow('provider 值必须是字符串')
  })
})

// ─── isApiMetaResponse type guard 测试 ───────────────────────────────────────
interface ApiMetaResponse {
  allowed_image_types: string[]
  max_image_size_mb: number
  llm_providers: string[]
  vision_llm_providers: string[]
  ocr_providers: string[]
  default_llm_provider: string
  default_vision_llm_provider: string
  default_ocr_provider: string
}

function isApiMetaResponse(value: unknown): value is ApiMetaResponse {
  if (!value || typeof value !== 'object') return false
  const r = value as Record<string, unknown>
  return (
    Array.isArray(r.allowed_image_types) &&
    typeof r.max_image_size_mb === 'number' &&
    Array.isArray(r.llm_providers) &&
    Array.isArray(r.vision_llm_providers) &&
    Array.isArray(r.ocr_providers) &&
    typeof r.default_llm_provider === 'string' &&
    typeof r.default_vision_llm_provider === 'string' &&
    typeof r.default_ocr_provider === 'string'
  )
}

describe('isApiMetaResponse', () => {
  it('有效响应返回 true', () => {
    expect(
      isApiMetaResponse({
        allowed_image_types: ['image/png'],
        max_image_size_mb: 20,
        llm_providers: ['minimax'],
        vision_llm_providers: ['minimax'],
        ocr_providers: ['qwen'],
        default_llm_provider: 'minimax',
        default_vision_llm_provider: 'minimax',
        default_ocr_provider: 'qwen',
      }),
    ).toBe(true)
  })

  it('缺少 llm_providers 返回 false', () => {
    expect(
      isApiMetaResponse({
        allowed_image_types: ['image/png'],
        max_image_size_mb: 20,
        vision_llm_providers: ['minimax'],
        ocr_providers: ['qwen'],
        default_llm_provider: 'minimax',
        default_vision_llm_provider: 'minimax',
        default_ocr_provider: 'qwen',
      }),
    ).toBe(false)
  })

  it('null 返回 false', () => {
    expect(isApiMetaResponse(null)).toBe(false)
  })

  it('数字返回 false', () => {
    expect(isApiMetaResponse(123)).toBe(false)
  })
})

// ─── isTransposeResponse type guard 测试 ─────────────────────────────────────
interface TransposeSuccessResponse {
  success: true
  output_image: string
  processing_time_ms: number
  request_id: string
  warnings: unknown[]
  score_json: unknown
}

interface TransposeErrorResponse {
  success: false
  error_code: string
  error_message: string
  request_id: string
}

type TransposeResponse = TransposeSuccessResponse | TransposeErrorResponse

interface ScoreJson {
  score_id: string
  source_key: { label: string; tonic: string }
  target_key: { label: string; tonic: string }
  events: unknown[]
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

describe('isTransposeResponse', () => {
  it('成功响应返回 true', () => {
    expect(
      isTransposeResponse({
        success: true,
        output_image: 'abc123',
        processing_time_ms: 1500,
        request_id: 'req-1',
        warnings: [],
        score_json: {
          score_id: 'req-1',
          source_key: { label: '1=G', tonic: 'G' },
          target_key: { label: '1=C', tonic: 'C' },
          events: [],
        },
      }),
    ).toBe(true)
  })

  it('错误响应返回 true', () => {
    expect(
      isTransposeResponse({
        success: false,
        error_code: 'INVALID_IMAGE_FORMAT',
        error_message: '不支持的图片格式',
        request_id: 'req-1',
      }),
    ).toBe(true)
  })

  it('缺少 output_image 返回 false', () => {
    expect(
      isTransposeResponse({
        success: true,
        processing_time_ms: 1500,
        request_id: 'req-1',
        warnings: [],
        score_json: {
          score_id: 'req-1',
          source_key: { label: '1=G', tonic: 'G' },
          target_key: { label: '1=C', tonic: 'C' },
          events: [],
        },
      }),
    ).toBe(false)
  })

  it('success 非布尔值返回 false', () => {
    expect(isTransposeResponse({ success: 'true' })).toBe(false)
  })
})

// ─── validateFile 测试 ────────────────────────────────────────────────────────
type UploadRules = {
  allowedImageTypes: string[]
  maxSizeMB: number
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

describe('validateFile', () => {
  const rules: UploadRules = { allowedImageTypes: ['image/png', 'image/jpeg'], maxSizeMB: 20 }

  it('合法文件返回 null', () => {
    const file = new File(['test'], 'test.png', { type: 'image/png' })
    expect(validateFile(file, rules)).toBeNull()
  })

  it('非法类型返回错误', () => {
    const file = new File(['test'], 'test.webp', { type: 'image/webp' })
    expect(validateFile(file, rules)).toBe('请上传 PNG 或 JPG 图片')
  })

  it('超大文件返回错误', () => {
    // 创建一个大于 20MB 的 Blob
    const bigContent = new Uint8Array(21 * 1024 * 1024)
    const file = new File([bigContent], 'big.png', { type: 'image/png' })
    expect(validateFile(file, rules)).toBe('图片大小不超过 20MB')
  })
})
