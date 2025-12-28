"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { type Review } from "@/lib/api"
import { formatDate, getRiskColor } from "@/lib/utils"
import { Shield, DollarSign, Activity, Code, AlertTriangle, CheckCircle, ArrowLeft, Download } from "lucide-react"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface PRReviewReportProps {
  review: Review
}

export function PRReviewReport({ review }: PRReviewReportProps) {
  const router = useRouter()
  const aiResult = review.ai_review_result

  if (!aiResult) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              Review analysis not yet completed
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const security = aiResult.security_analysis
  const cost = aiResult.cost_analysis
  const reliability = aiResult.reliability_analysis

  // Parse Terraform code for diff view
  const terraformLines = review.terraform_code.split('\n')
  const findingsByLine = new Map<number, typeof security.findings[0]>()
  
  security.findings.forEach(finding => {
    if (finding.line_number) {
      findingsByLine.set(finding.line_number, finding)
    }
  })

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              PR Review Report
            </h1>
            <p className="text-muted-foreground mt-1">
              Review ID: {review.review_id} • {formatDate(review.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Overall Risk</p>
            <p className={`text-3xl font-bold ${getRiskColor(aiResult.overall_risk_score)}`}>
              {(aiResult.overall_risk_score * 100).toFixed(1)}%
            </p>
          </div>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </motion.div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-l-4 border-l-red-500 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Security Findings</CardTitle>
              <Shield className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{security.total_findings}</div>
              <div className="flex gap-2 mt-2">
                <Badge variant="destructive">{security.high_severity} High</Badge>
                <Badge variant="default" className="bg-amber-500">{security.medium_severity} Med</Badge>
                <Badge variant="secondary">{security.low_severity} Low</Badge>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-l-4 border-l-orange-500 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Cost Analysis</CardTitle>
              <DollarSign className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${cost.estimated_monthly_cost.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground mt-1">
                ${cost.estimated_annual_cost.toFixed(2)}/year • {cost.resource_count} resources
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="border-l-4 border-l-blue-500 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Reliability Score</CardTitle>
              <Activity className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(reliability.reliability_score * 100).toFixed(0)}%
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {reliability.single_points_of_failure.length} SPOFs identified
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="code" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="code">
            <Code className="h-4 w-4 mr-2" />
            Terraform Code
          </TabsTrigger>
          <TabsTrigger value="security">
            <Shield className="h-4 w-4 mr-2" />
            Security ({security.total_findings})
          </TabsTrigger>
          <TabsTrigger value="cost">
            <DollarSign className="h-4 w-4 mr-2" />
            Cost
          </TabsTrigger>
          <TabsTrigger value="reliability">
            <Activity className="h-4 w-4 mr-2" />
            Reliability
          </TabsTrigger>
        </TabsList>

        {/* Terraform Code with Highlighted Risk Lines */}
        <TabsContent value="code" className="space-y-4">
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Terraform Code</CardTitle>
              <CardDescription>
                Risk-highlighted code view. Lines with findings are marked.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg overflow-hidden border">
                <SyntaxHighlighter
                  language="hcl"
                  style={vscDarkPlus}
                  customStyle={{
                    margin: 0,
                    padding: '1rem',
                    fontSize: '14px',
                    lineHeight: '1.6',
                  }}
                  lineProps={(lineNumber) => {
                    const finding = findingsByLine.get(lineNumber)
                    if (finding) {
                      return {
                        style: {
                          backgroundColor: finding.severity === 'high' 
                            ? 'rgba(239, 68, 68, 0.2)' 
                            : finding.severity === 'medium'
                            ? 'rgba(245, 158, 11, 0.2)'
                            : 'rgba(59, 130, 246, 0.2)',
                          borderLeft: `3px solid ${
                            finding.severity === 'high' 
                              ? '#ef4444' 
                              : finding.severity === 'medium'
                              ? '#f59e0b'
                              : '#3b82f6'
                          }`,
                          paddingLeft: '0.5rem',
                          display: 'block',
                        }
                      }
                    }
                    return {}
                  }}
                  showLineNumbers
                >
                  {review.terraform_code}
                </SyntaxHighlighter>
              </div>
              
              {/* Legend */}
              <div className="mt-4 flex gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-red-500/20 border-l-4 border-red-500" />
                  <span>High Severity</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-amber-500/20 border-l-4 border-amber-500" />
                  <span>Medium Severity</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-500/20 border-l-4 border-blue-500" />
                  <span>Low Severity</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Findings */}
        <TabsContent value="security" className="space-y-4">
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Security Findings</CardTitle>
              <CardDescription>
                {security.total_findings} total findings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {security.findings.map((finding, index) => (
                <motion.div
                  key={finding.finding_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`p-4 border rounded-lg space-y-2 ${
                    finding.severity === 'high' ? 'border-red-500 bg-red-50/50' :
                    finding.severity === 'medium' ? 'border-amber-500 bg-amber-50/50' :
                    'border-blue-500 bg-blue-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold">{finding.title}</h4>
                        <Badge
                          variant={
                            finding.severity === "high"
                              ? "destructive"
                              : finding.severity === "medium"
                              ? "default"
                              : "secondary"
                          }
                          className={
                            finding.severity === "medium" ? "bg-amber-500" : ""
                          }
                        >
                          {finding.severity}
                        </Badge>
                        {finding.line_number && (
                          <Badge variant="outline">
                            Line {finding.line_number}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {finding.description}
                      </p>
                      {finding.file_path && (
                        <p className="text-xs text-muted-foreground mt-1">
                          File: {finding.file_path}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 p-3 bg-white rounded border">
                    <p className="text-sm font-medium mb-1">Recommendation:</p>
                    <p className="text-sm">{finding.recommendation}</p>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cost Analysis */}
        <TabsContent value="cost" className="space-y-4">
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Cost Optimizations</CardTitle>
              <CardDescription>
                {cost.cost_optimizations.length} opportunities identified
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {cost.cost_optimizations.map((finding, index) => (
                <motion.div
                  key={finding.finding_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-4 border rounded-lg space-y-2 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold">{finding.title}</h4>
                        {finding.estimated_cost_impact && (
                          <Badge variant="default" className="bg-orange-500">
                            ${finding.estimated_cost_impact.toFixed(2)}/mo
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {finding.description}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 p-3 bg-white rounded border">
                    <p className="text-sm font-medium mb-1">Recommendation:</p>
                    <p className="text-sm">{finding.recommendation}</p>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reliability */}
        <TabsContent value="reliability" className="space-y-4">
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Reliability Analysis</CardTitle>
              <CardDescription>
                Reliability Score: {(reliability.reliability_score * 100).toFixed(0)}%
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {reliability.single_points_of_failure.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">Single Points of Failure</h4>
                  <div className="space-y-3">
                    {reliability.single_points_of_failure.map((finding, index) => (
                      <motion.div
                        key={finding.finding_id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="p-4 border border-yellow-500 rounded-lg bg-yellow-50/50"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-600" />
                          <h5 className="font-medium">{finding.title}</h5>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {finding.description}
                        </p>
                        <p className="text-sm mt-2">{finding.recommendation}</p>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}
              {reliability.recommendations.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">General Recommendations</h4>
                  <ul className="list-disc list-inside space-y-2">
                    {reliability.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

