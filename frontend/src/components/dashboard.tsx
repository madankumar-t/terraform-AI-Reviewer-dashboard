"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ReviewList } from "@/components/review-list"
import { AnalyticsDashboard } from "@/components/analytics-dashboard"
import { ReviewDetail } from "@/components/review-detail"
import { reviewApi, type Review, type Analytics } from "@/lib/api"
import { Activity, Shield, DollarSign, TrendingUp, AlertTriangle } from "lucide-react"
import { useAuth } from "@/components/auth-provider"

export function Dashboard() {
  const router = useRouter()
  const { user, loading: authLoading, signOut } = useAuth()
  const [reviews, setReviews] = useState<Review[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [selectedReview, setSelectedReview] = useState<Review | null>(null)
  const [dataLoading, setDataLoading] = useState(true)

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!authLoading && !user) {
      router.push('/auth/login')
      return
    }

    if (user) {
      loadData()
      // Poll for updates every 10 seconds
      const interval = setInterval(loadData, 10000)
      return () => clearInterval(interval)
    }
  }, [user, authLoading, router])

  const loadData = async () => {
    try {
      const [reviewsData, analyticsData] = await Promise.all([
        reviewApi.getReviews({ limit: 50 }),
        reviewApi.getAnalytics(30)
      ])
      setReviews(reviewsData.reviews)
      setAnalytics(analyticsData)
    } catch (error) {
      console.error("Error loading data:", error)
    } finally {
      setDataLoading(false)
    }
  }

  const handleReviewSelect = async (reviewId: string) => {
    try {
      const review = await reviewApi.getReview(reviewId)
      setSelectedReview(review)
    } catch (error) {
      console.error("Error loading review:", error)
    }
  }

  if (authLoading || (dataLoading && !analytics)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Terraform + Spacelift AI Reviewer
          </h1>
          <p className="text-muted-foreground mt-2">
            AI-powered code review with security, cost, and reliability analysis
          </p>
        </div>
        {user && (
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium">{user.email}</p>
              <p className="text-xs text-muted-foreground">
                {user.groups.join(', ')}
              </p>
            </div>
            <button
              onClick={signOut}
              className="px-4 py-2 text-sm border rounded-md hover:bg-muted"
            >
              Sign Out
            </button>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      {analytics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Reviews</CardTitle>
              <Activity className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.total_reviews}</div>
              <p className="text-xs text-blue-100">Last 30 days</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Risk Score</CardTitle>
              <Shield className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(analytics.average_risk_score * 100).toFixed(1)}%
              </div>
              <p className="text-xs text-green-100">
                {analytics.average_risk_score < 0.33 ? "Low Risk" : 
                 analytics.average_risk_score < 0.67 ? "Medium Risk" : "High Risk"}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">High Risk</CardTitle>
              <AlertTriangle className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.reviews_by_risk.high || 0}</div>
              <p className="text-xs text-purple-100">Requires attention</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <TrendingUp className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {analytics.reviews_by_status.completed || 0}
              </div>
              <p className="text-xs text-orange-100">Reviews finished</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs defaultValue="reviews" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="reviews">Reviews</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="detail" disabled={!selectedReview}>
            Review Detail
          </TabsTrigger>
        </TabsList>

        <TabsContent value="reviews" className="space-y-4">
          <ReviewList
            reviews={reviews}
            onReviewSelect={handleReviewSelect}
            onRefresh={loadData}
          />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          {analytics && <AnalyticsDashboard analytics={analytics} />}
        </TabsContent>

        <TabsContent value="detail" className="space-y-4">
          {selectedReview && <ReviewDetail review={selectedReview} />}
        </TabsContent>
      </Tabs>
    </div>
  )
}

