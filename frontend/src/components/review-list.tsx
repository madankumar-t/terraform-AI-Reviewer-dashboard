"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { type Review } from "@/lib/api"
import { formatDate, getRiskColor, getRiskBgColor } from "@/lib/utils"
import { RefreshCw, Eye, Clock, CheckCircle, XCircle, Loader } from "lucide-react"

interface ReviewListProps {
  reviews: Review[]
  onReviewSelect: (reviewId: string) => void
  onRefresh: () => void
}

export function ReviewList({ reviews, onReviewSelect, onRefresh }: ReviewListProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />
      case "in_progress":
        return <Loader className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  const getStatusVariant = (status: string): "success" | "warning" | "danger" | "default" => {
    switch (status) {
      case "completed":
        return "success"
      case "failed":
        return "danger"
      case "in_progress":
        return "warning"
      default:
        return "default"
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Recent Reviews</h2>
        <Button onClick={onRefresh} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid gap-4">
        {reviews.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">No reviews found</p>
            </CardContent>
          </Card>
        ) : (
          reviews.map((review) => {
            const riskScore = review.ai_review_result?.overall_risk_score || 0
            const securityFindings = review.ai_review_result?.security_analysis?.total_findings || 0
            const costOptimizations = review.ai_review_result?.cost_analysis?.cost_optimizations?.length || 0

            return (
              <Card
                key={review.review_id}
                className={`cursor-pointer transition-all hover:shadow-lg ${getRiskBgColor(riskScore)}`}
                onClick={() => onReviewSelect(review.review_id)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">
                        Review {review.review_id.slice(0, 8)}
                      </CardTitle>
                      <CardDescription>
                        {review.spacelift_run_id ? (
                          <span>Spacelift Run: {review.spacelift_run_id}</span>
                        ) : (
                          <span>Manual Review</span>
                        )}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(review.status)}
                      <Badge variant={getStatusVariant(review.status)}>
                        {review.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Risk Score</p>
                      <p className={`text-2xl font-bold ${getRiskColor(riskScore)}`}>
                        {(riskScore * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Security Findings</p>
                      <p className="text-2xl font-bold">{securityFindings}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Cost Optimizations</p>
                      <p className="text-2xl font-bold">{costOptimizations}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Created: {formatDate(review.created_at)}
                    </p>
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}

