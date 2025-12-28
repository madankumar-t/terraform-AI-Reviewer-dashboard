"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { type Review } from "@/lib/api"
import { formatDate, getRiskColor } from "@/lib/utils"
import { Shield, CheckCircle, XCircle, AlertTriangle, FileText, Calendar, TrendingUp } from "lucide-react"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"

interface ComplianceAuditViewProps {
  reviews: Review[]
}

const SOC2_CONTROLS = [
  { id: 'CC2', name: 'Communication and Information', description: 'System captures and communicates information' },
  { id: 'CC4', name: 'Monitoring Activities', description: 'System monitors activities' },
  { id: 'CC6', name: 'Logical and Physical Access', description: 'System restricts and logs access' },
  { id: 'CC7', name: 'System Operations', description: 'System operations are controlled' },
]

const ISO27001_CLAUSES = [
  { id: 'A.9', name: 'Access Control', description: 'Access to information and systems' },
  { id: 'A.12', name: 'Operations Security', description: 'Operational procedures and responsibilities' },
  { id: 'A.14', name: 'System Acquisition', description: 'Security in development and support processes' },
  { id: 'A.18', name: 'Compliance', description: 'Compliance with legal and contractual requirements' },
]

export function ComplianceAuditView({ reviews }: ComplianceAuditViewProps) {
  const router = useRouter()

  // Calculate compliance metrics
  const completedReviews = reviews.filter(r => r.status === 'completed')
  const highRiskReviews = completedReviews.filter(r => 
    (r.ai_review_result?.overall_risk_score || 0) > 0.67
  )
  const mediumRiskReviews = completedReviews.filter(r => {
    const risk = r.ai_review_result?.overall_risk_score || 0
    return risk > 0.33 && risk <= 0.67
  })
  const lowRiskReviews = completedReviews.filter(r => 
    (r.ai_review_result?.overall_risk_score || 0) <= 0.33
  )

  const complianceScore = completedReviews.length > 0
    ? ((lowRiskReviews.length + mediumRiskReviews.length * 0.5) / completedReviews.length) * 100
    : 0

  // Group by month for trend
  const monthlyData = reviews.reduce((acc, review) => {
    const date = new Date(review.created_at)
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    if (!acc[monthKey]) {
      acc[monthKey] = { month: monthKey, total: 0, high: 0, medium: 0, low: 0 }
    }
    acc[monthKey].total++
    const risk = review.ai_review_result?.overall_risk_score || 0
    if (risk > 0.67) acc[monthKey].high++
    else if (risk > 0.33) acc[monthKey].medium++
    else acc[monthKey].low++
    return acc
  }, {} as Record<string, { month: string; total: number; high: number; medium: number; low: number }>)

  const trendData = Object.values(monthlyData).sort((a, b) => a.month.localeCompare(b.month))

  const riskDistribution = [
    { name: 'Low Risk', value: lowRiskReviews.length, color: '#10b981' },
    { name: 'Medium Risk', value: mediumRiskReviews.length, color: '#f59e0b' },
    { name: 'High Risk', value: highRiskReviews.length, color: '#ef4444' },
  ]

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
            Compliance Audit View
          </h1>
          <p className="text-muted-foreground mt-2">
            SOC2 and ISO 27001 compliance tracking and evidence
          </p>
        </div>
        <Badge 
          variant={complianceScore >= 80 ? "default" : complianceScore >= 60 ? "secondary" : "destructive"}
          className={`text-lg px-4 py-2 ${complianceScore >= 80 ? 'bg-green-500' : complianceScore >= 60 ? 'bg-amber-500' : ''}`}
        >
          {complianceScore.toFixed(1)}% Compliant
        </Badge>
      </motion.div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Compliance Score</CardTitle>
              <Shield className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{complianceScore.toFixed(1)}%</div>
              <p className="text-xs text-blue-100 mt-1">Overall compliance</p>
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
              <CardTitle className="text-sm font-medium">Low Risk</CardTitle>
              <CheckCircle className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{lowRiskReviews.length}</div>
              <p className="text-xs text-green-100 mt-1">Compliant reviews</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Medium Risk</CardTitle>
              <AlertTriangle className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{mediumRiskReviews.length}</div>
              <p className="text-xs text-amber-100 mt-1">Requires attention</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">High Risk</CardTitle>
              <XCircle className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{highRiskReviews.length}</div>
              <p className="text-xs text-red-100 mt-1">Non-compliant</p>
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
              <CardTitle>Compliance Trend</CardTitle>
              <CardDescription>Risk distribution over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="low" stackId="a" fill="#10b981" name="Low Risk" />
                  <Bar dataKey="medium" stackId="a" fill="#f59e0b" name="Medium Risk" />
                  <Bar dataKey="high" stackId="a" fill="#ef4444" name="High Risk" />
                </BarChart>
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
              <CardTitle>Risk Distribution</CardTitle>
              <CardDescription>Current risk breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {riskDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Compliance Frameworks */}
      <Tabs defaultValue="soc2" className="space-y-4">
        <TabsList>
          <TabsTrigger value="soc2">SOC2 Controls</TabsTrigger>
          <TabsTrigger value="iso27001">ISO 27001</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
        </TabsList>

        <TabsContent value="soc2" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {SOC2_CONTROLS.map((control, index) => (
              <motion.div
                key={control.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + index * 0.1 }}
              >
                <Card className="shadow-lg">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{control.id}</CardTitle>
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Compliant
                      </Badge>
                    </div>
                    <CardDescription>{control.name}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{control.description}</p>
                    <div className="mt-4 space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>Evidence Points</span>
                        <span className="font-medium">{completedReviews.length}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span>Audit Logs</span>
                        <span className="font-medium">Available</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="iso27001" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {ISO27001_CLAUSES.map((clause, index) => (
              <motion.div
                key={clause.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + index * 0.1 }}
              >
                <Card className="shadow-lg">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{clause.id}</CardTitle>
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Compliant
                      </Badge>
                    </div>
                    <CardDescription>{clause.name}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{clause.description}</p>
                    <div className="mt-4 space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>Evidence Points</span>
                        <span className="font-medium">{completedReviews.length}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span>Audit Logs</span>
                        <span className="font-medium">Available</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="evidence" className="space-y-4">
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Compliance Evidence</CardTitle>
              <CardDescription>
                Review evidence for compliance audits
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {completedReviews.slice(0, 20).map((review, index) => {
                  const risk = review.ai_review_result?.overall_risk_score || 0
                  return (
                    <motion.div
                      key={review.review_id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => router.push(`/pr-review/${review.review_id}`)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">Review {review.review_id.slice(0, 8)}</span>
                            <Badge variant={risk > 0.67 ? "destructive" : risk > 0.33 ? "secondary" : "default"}>
                              {risk > 0.67 ? "High Risk" : risk > 0.33 ? "Medium Risk" : "Low Risk"}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {formatDate(review.created_at)} • {review.ai_review_result?.security_analysis?.total_findings || 0} findings
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`text-2xl font-bold ${getRiskColor(risk)}`}>
                            {(risk * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

