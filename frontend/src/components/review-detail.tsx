"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { type Review } from "@/lib/api"
import { formatDate, getRiskColor } from "@/lib/utils"
import { Shield, DollarSign, Activity, Code, AlertTriangle, CheckCircle } from "lucide-react"
// Diff viewer can be added later if needed

interface ReviewDetailProps {
  review: Review
}

export function ReviewDetail({ review }: ReviewDetailProps) {
  const aiResult = review.ai_review_result

  if (!aiResult) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">
            Review analysis not yet completed
          </p>
        </CardContent>
      </Card>
    )
  }

  const security = aiResult.security_analysis
  const cost = aiResult.cost_analysis
  const reliability = aiResult.reliability_analysis

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Review Details</CardTitle>
              <CardDescription>
                Review ID: {review.review_id} • Created: {formatDate(review.created_at)}
              </CardDescription>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Overall Risk</p>
              <p className={`text-3xl font-bold ${getRiskColor(aiResult.overall_risk_score)}`}>
                {(aiResult.overall_risk_score * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-l-4 border-l-red-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security Findings</CardTitle>
            <Shield className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{security.total_findings}</div>
            <div className="flex gap-2 mt-2">
              <Badge variant="danger">{security.high_severity} High</Badge>
              <Badge variant="warning">{security.medium_severity} Med</Badge>
              <Badge variant="success">{security.low_severity} Low</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
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

        <Card className="border-l-4 border-l-blue-500">
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
      </div>

      {/* Detailed Analysis */}
      <Tabs defaultValue="security" className="space-y-4">
        <TabsList>
          <TabsTrigger value="security">
            <Shield className="h-4 w-4 mr-2" />
            Security
          </TabsTrigger>
          <TabsTrigger value="cost">
            <DollarSign className="h-4 w-4 mr-2" />
            Cost
          </TabsTrigger>
          <TabsTrigger value="reliability">
            <Activity className="h-4 w-4 mr-2" />
            Reliability
          </TabsTrigger>
          <TabsTrigger value="fixes">
            <Code className="h-4 w-4 mr-2" />
            Fix Suggestions
          </TabsTrigger>
        </TabsList>

        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Security Findings</CardTitle>
              <CardDescription>
                {security.total_findings} total findings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {security.findings.map((finding) => (
                <div
                  key={finding.finding_id}
                  className="p-4 border rounded-lg space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold">{finding.title}</h4>
                        <Badge
                          variant={
                            finding.severity === "high"
                              ? "danger"
                              : finding.severity === "medium"
                              ? "warning"
                              : "success"
                          }
                        >
                          {finding.severity}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {finding.description}
                      </p>
                      {finding.line_number && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Line {finding.line_number}
                          {finding.file_path && ` in ${finding.file_path}`}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 p-2 bg-muted rounded">
                    <p className="text-sm font-medium">Recommendation:</p>
                    <p className="text-sm">{finding.recommendation}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cost" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cost Optimizations</CardTitle>
              <CardDescription>
                {cost.cost_optimizations.length} opportunities identified
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {cost.cost_optimizations.map((finding) => (
                <div
                  key={finding.finding_id}
                  className="p-4 border rounded-lg space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold">{finding.title}</h4>
                        {finding.estimated_cost_impact && (
                          <Badge variant="warning">
                            ${finding.estimated_cost_impact.toFixed(2)}/mo
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {finding.description}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 p-2 bg-muted rounded">
                    <p className="text-sm font-medium">Recommendation:</p>
                    <p className="text-sm">{finding.recommendation}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reliability" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Reliability Analysis</CardTitle>
              <CardDescription>
                Reliability Score: {(reliability.reliability_score * 100).toFixed(0)}%
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {reliability.single_points_of_failure.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Single Points of Failure</h4>
                  <div className="space-y-2">
                    {reliability.single_points_of_failure.map((finding) => (
                      <div
                        key={finding.finding_id}
                        className="p-4 border rounded-lg"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          <h5 className="font-medium">{finding.title}</h5>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {finding.description}
                        </p>
                        <p className="text-sm mt-2">{finding.recommendation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {reliability.recommendations.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">General Recommendations</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {reliability.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fixes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Fix Suggestions</CardTitle>
              <CardDescription>
                {aiResult.fix_suggestions.length} suggested fixes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {aiResult.fix_suggestions.map((fix) => (
                <div
                  key={fix.fix_id}
                  className="p-4 border rounded-lg space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Fix for Finding: {fix.finding_id}</h4>
                    {fix.effectiveness_score && (
                      <Badge variant="success">
                        {(fix.effectiveness_score * 100).toFixed(0)}% effective
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{fix.explanation}</p>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium mb-2">Original Code</p>
                      <pre className="p-2 bg-muted rounded text-xs overflow-x-auto">
                        {fix.original_code}
                      </pre>
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-2">Suggested Code</p>
                      <pre className="p-2 bg-muted rounded text-xs overflow-x-auto">
                        {fix.suggested_code}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

