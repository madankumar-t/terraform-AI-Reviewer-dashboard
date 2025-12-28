import axios from 'axios'
import { AuthService } from './auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.example.com'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to include auth token
api.interceptors.request.use(
  async (config) => {
    const authHeader = await AuthService.getAuthHeader()
    if (authHeader) {
      config.headers.Authorization = authHeader
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, sign out
      await AuthService.signOut()
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

// ... rest of the API code from previous implementation ...

export interface Review {
  review_id: string
  terraform_code: string
  spacelift_run_id?: string
  spacelift_context?: Record<string, any>
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  ai_review_result?: AIReviewResult
  created_at: string
  updated_at: string
  version: number
}

export interface AIReviewResult {
  review_id: string
  security_analysis: SecurityAnalysis
  cost_analysis: CostAnalysis
  reliability_analysis: ReliabilityAnalysis
  overall_risk_score: number
  fix_suggestions: FixSuggestion[]
  review_metadata: Record<string, any>
}

export interface SecurityAnalysis {
  total_findings: number
  high_severity: number
  medium_severity: number
  low_severity: number
  findings: Finding[]
}

export interface CostAnalysis {
  estimated_monthly_cost: number
  estimated_annual_cost: number
  resource_count: number
  cost_optimizations: Finding[]
}

export interface ReliabilityAnalysis {
  reliability_score: number
  single_points_of_failure: Finding[]
  recommendations: string[]
}

export interface Finding {
  finding_id: string
  category: string
  severity: 'low' | 'medium' | 'high'
  title: string
  description: string
  line_number?: number
  file_path?: string
  recommendation: string
  estimated_cost_impact?: number
  confidence_score: number
}

export interface FixSuggestion {
  fix_id: string
  finding_id: string
  original_code: string
  suggested_code: string
  explanation: string
  effectiveness_score?: number
}

export interface Analytics {
  total_reviews: number
  reviews_by_status: Record<string, number>
  reviews_by_risk: Record<string, number>
  average_risk_score: number
  trend_data: Array<{ date: string; count: number }>
  top_findings: Array<{ title: string; count: number }>
}

export const reviewApi = {
  getReviews: async (params?: {
    spaceliftRunId?: string
    status?: string
    limit?: number
  }): Promise<{ reviews: Review[]; count: number }> => {
    const response = await api.get('/api/reviews', { params })
    return response.data
  },

  getReview: async (reviewId: string): Promise<Review> => {
    const response = await api.get(`/api/reviews/${reviewId}`)
    return response.data
  },

  createReview: async (data: {
    terraform_code: string
    spacelift_run_id?: string
    spacelift_context?: Record<string, any>
  }): Promise<Review> => {
    const response = await api.post('/api/reviews', data)
    return response.data
  },

  updateReview: async (
    reviewId: string,
    data: Partial<Review>
  ): Promise<Review> => {
    const response = await api.put(`/api/reviews/${reviewId}`, data)
    return response.data
  },

  getAnalytics: async (days?: number): Promise<Analytics> => {
    const response = await api.get('/api/analytics', {
      params: { days },
    })
    return response.data
  },
}
