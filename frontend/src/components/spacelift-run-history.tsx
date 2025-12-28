"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { type Review } from "@/lib/api"
import { formatDate, getRiskColor, getRiskBgColor } from "@/lib/utils"
import { RefreshCw, Eye, Clock, CheckCircle, XCircle, Loader, GitBranch, TrendingUp, AlertTriangle } from "lucide-react"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

interface SpaceliftRunHistoryProps {
  reviews: Review[]
}

export function SpaceliftRunHistory({ reviews }: SpaceliftRunHistoryProps) {
  const router = useRouter()

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

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case "completed":
        return "default"
      case "failed":
        return "destructive"
      case "in_progress":
        return "secondary"
      default:
        return "outline"
    }
  }

  // Group by date for trend chart
  const trendData = reviews.reduce((acc, review) => {
    const date = formatDate(review.created_at).split(',')[0]
    const existing = acc.find(d => d.date === date)
    if (existing) {
      existing.count++
      if (review.status === 'completed') existing.completed++
      if (review.status === 'failed') existing.failed++
    } else {
      acc.push({
        date,
        count: 1,
        completed: review.status === 'completed' ? 1 : 0,
        failed: review.status === 'failed' ? 1 : 0,
      })
    }
    return acc
  }, [] as Array<{ date: string; count: number; completed: number; failed: number }>)

  // Group by Spacelift run ID
  const runsBySpaceliftId = reviews.reduce((acc, review) => {
    if (!review.spacelift_run_id) return acc
    if (!acc[review.spacelift_run_id]) {
      acc[review.spacelift_run_id] = []
    }
    acc[review.spacelift_run_id].push(review)
    return acc
  }, {} as Record<string, Review[]>)

  const runs = Object.entries(runsBySpaceliftId).map(([runId, runReviews]) => {
    const latestReview = runReviews.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )[0]
    const avgRisk = runReviews.reduce((sum, r) => 
      sum + (r.ai_review_result?.overall_risk_score || 0), 0
    ) / runReviews.length

    return {
      runId,
      reviews: runReviews,
      latestReview,
      avgRisk,
      status: latestReview.status,
      createdAt: latestReview.created_at,
    }
  }).sort((a, b) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  )

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Spacelift Run History
          </h1>
          <p className="text-muted-foreground mt-2">
            Track and analyze Spacelift runs with AI review insights
          </p>
        </div>
        <Badge variant="outline" className="text-lg px-4 py-2">
          {runs.length} Runs
        </Badge>
      </motion.div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
              <GitBranch className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{runs.length}</div>
              <p className="text-xs text-blue-100 mt-1">All Spacelift runs</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {runs.filter(r => r.status === 'completed').length}
              </div>
              <p className="text-xs text-green-100 mt-1">Successful runs</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
              <XCircle className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {runs.filter(r => r.status === 'failed').length}
              </div>
              <p className="text-xs text-red-100 mt-1">Failed runs</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Risk</CardTitle>
              <TrendingUp className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {runs.length > 0 
                  ? (runs.reduce((sum, r) => sum + r.avgRisk, 0) / runs.length * 100).toFixed(1)
                  : '0'
                }%
              </div>
              <p className="text-xs text-purple-100 mt-1">Average risk score</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Run Trends</CardTitle>
              <CardDescription>Spacelift runs over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="url(#colorCount)" name="Total Runs" />
                  <Area type="monotone" dataKey="completed" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Completed" />
                  <Area type="monotone" dataKey="failed" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} name="Failed" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Status Distribution</CardTitle>
              <CardDescription>Runs by status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {['completed', 'failed', 'in_progress', 'pending'].map((status) => {
                  const count = runs.filter(r => r.status === status).length
                  const percentage = runs.length > 0 ? (count / runs.length) * 100 : 0
                  return (
                    <div key={status} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="capitalize">{status.replace('_', ' ')}</span>
                        <span className="font-medium">{count} ({percentage.toFixed(1)}%)</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percentage}%` }}
                          transition={{ duration: 0.5, delay: 0.7 }}
                          className={`h-2 rounded-full ${
                            status === 'completed' ? 'bg-green-500' :
                            status === 'failed' ? 'bg-red-500' :
                            status === 'in_progress' ? 'bg-blue-500' :
                            'bg-gray-500'
                          }`}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Runs List */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
          <CardDescription>
            Click on a run to view detailed review
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {runs.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">No Spacelift runs found</p>
            ) : (
              runs.map((run, index) => (
                <motion.div
                  key={run.runId}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 + index * 0.05 }}
                >
                  <Card
                    className={`cursor-pointer transition-all hover:shadow-lg ${getRiskBgColor(run.avgRisk)}`}
                    onClick={() => router.push(`/pr-review/${run.latestReview.review_id}`)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <CardTitle className="text-lg">
                            Run {run.runId.slice(0, 12)}
                          </CardTitle>
                          <CardDescription>
                            {formatDate(run.createdAt)} • {run.reviews.length} review{run.reviews.length !== 1 ? 's' : ''}
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(run.status)}
                          <Badge variant={getStatusVariant(run.status)}>
                            {run.status}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-muted-foreground">Avg Risk</p>
                          <p className={`text-2xl font-bold ${getRiskColor(run.avgRisk)}`}>
                            {(run.avgRisk * 100).toFixed(0)}%
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Reviews</p>
                          <p className="text-2xl font-bold">{run.reviews.length}</p>
                        </div>
                        <div>
                          <p className="text-sm text-muted-foreground">Latest</p>
                          <p className="text-2xl font-bold">
                            {run.latestReview.ai_review_result?.security_analysis?.total_findings || 0}
                          </p>
                          <p className="text-xs text-muted-foreground">Findings</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                          {run.avgRisk > 0.67 && (
                            <Badge variant="destructive">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              High Risk
                            </Badge>
                          )}
                        </div>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

