export interface PricingRequest {
  product_name: string
  category?: string
  condition?: string
  image?: string
}

export interface RiskCheckResult {
  risk_level: 'high' | 'medium' | 'low'
  risk_type?: string | null
  matched_words: string[]
  message: string
}

export interface PricingResult {
  suggested_price: number
  price_min: number
  price_max: number
  confidence: 'high' | 'medium' | 'low'
  reasoning: string
  comparables?: Array<{
    name: string
    price: number
    condition: string
  }>
  risk_check?: RiskCheckResult
}

export interface AdjustRequest {
  product_name: string
  category?: string
  condition?: string
  current_price: number
  message: string
}

export interface RecognizeResult {
  success: boolean
  product_name: string
  category: string
  condition: string
  brand: string
  notes: string
  message: string
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

class PricingService {
  async getPrice(request: PricingRequest): Promise<PricingResult> {
    const response = await fetch(`${API_BASE}/api/price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    return response.json()
  }

  async adjustPrice(request: AdjustRequest): Promise<PricingResult> {
    const response = await fetch(`${API_BASE}/api/price/adjust`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    return response.json()
  }

  async recognizeImage(imageBase64: string): Promise<RecognizeResult> {
    const response = await fetch(`${API_BASE}/api/recognize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: imageBase64 }),
    })
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    return response.json()
  }
}

export const pricingService = new PricingService()
