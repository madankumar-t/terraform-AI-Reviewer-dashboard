"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { type Review } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { ArrowLeft, CheckCircle, XCircle, TrendingUp, Code, Shield } from "lucide-react"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts"

interface FixEffectivenessComparisonProps {
  review: Review
}

export function FixEffectivenessComparison({ review }: FixEffectivenessComparisonProps) {
  const router = useRouter()
  const aiResult = review.ai_review_result

  if (!aiResult || !aiResult.fix_suggestions || aiResult.fix_suggestions.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              No fix suggestions available for this review
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const fixes = aiResult.fix_suggestions
  const effectivenessData = fixes
    .filter(f => f.effectiveness_score !== undefined)
    .map(f => ({
      finding: f.finding_id.slice(0, 8),
      effectiveness: (f.effectiveness_score! * 100),
      title: aiResult.security_analysis.findings.find(finding => finding.finding_id === f.finding_id)?.title || 'Unknown'
    }))
    .sort((a, b) => b.effectiveness - a.effectiveness)

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
              Fix Effectiveness Comparison
            </h1>
            <p className="text-muted-foreground mt-1">
              Review ID: {review.review_id} • {formatDate(review.created_at)}
            </p>
          </div>
        </div>
        <Badge variant="outline" className="text-lg px-4 py-2">
          {fixes.length} Fixes
        </Badge>
      </motion.div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Fixes</CardTitle>
              <Code className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{fixes.length}</div>
              <p className="text-xs text-blue-100 mt-1">Suggested fixes</p>
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
              <CardTitle className="text-sm font-medium">Avg Effectiveness</CardTitle>
              <TrendingUp className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {effectivenessData.length > 0
                  ? (effectivenessData.reduce((sum, d) => sum + d.effectiveness, 0) / effectivenessData.length).toFixed(1)
                  : 'N/A'
                }%
              </div>
              <p className="text-xs text-green-100 mt-1">Average score</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">High Impact</CardTitle>
              <Shield className="h-5 w-5" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {effectivenessData.filter(d => d.effectiveness >= 80).length}
              </div>
              <p className="text-xs text-purple-100 mt-1">80%+ effectiveness</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Effectiveness Chart */}
      {effectivenessData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Fix Effectiveness Scores</CardTitle>
              <CardDescription>
                Effectiveness ratings for each suggested fix
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={effectivenessData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="finding" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip 
                    formatter={(value: number) => `${value.toFixed(1)}%`}
                    labelFormatter={(label) => `Finding: ${label}`}
                  />
                  <Bar dataKey="effectiveness" radius={[8, 8, 0, 0]}>
                    {effectivenessData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={
                          entry.effectiveness >= 80 ? '#10b981' :
                          entry.effectiveness >= 60 ? '#f59e0b' :
                          '#ef4444'
                        } 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Fixes List */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Fixes ({fixes.length})</TabsTrigger>
          <TabsTrigger value="high">
            High Impact ({effectivenessData.filter(d => d.effectiveness >= 80).length})
          </TabsTrigger>
          <TabsTrigger value="medium">
            Medium Impact ({effectivenessData.filter(d => d.effectiveness >= 60 && d.effectiveness < 80).length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {fixes.map((fix, index) => {
            const finding = aiResult.security_analysis.findings.find(f => f.finding_id === fix.finding_id)
            return (
              <motion.div
                key={fix.fix_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + index * 0.05 }}
              >
                <Card className="shadow-lg">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">
                          {finding?.title || `Fix for Finding ${fix.finding_id.slice(0, 8)}`}
                        </CardTitle>
                        <CardDescription>
                          Finding ID: {fix.finding_id} • Severity: {finding?.severity || 'Unknown'}
                        </CardDescription>
                      </div>
                      {fix.effectiveness_score && (
                        <Badge 
                          variant={
                            fix.effectiveness_score >= 0.8 ? "default" :
                            fix.effectiveness_score >= 0.6 ? "secondary" :
                            "destructive"
                          }
                          className={
                            fix.effectiveness_score >= 0.8 ? "bg-green-500" :
                            fix.effectiveness_score >= 0.6 ? "bg-amber-500" :
                            ""
                          }
                        >
                          {(fix.effectiveness_score * 100).toFixed(0)}% Effective
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm font-medium mb-2">Explanation</p>
                      <p className="text-sm text-muted-foreground">{fix.explanation}</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium mb-2 flex items-center gap-2">
                          <XCircle className="h-4 w-4 text-red-500" />
                          Original Code
                        </p>
                        <div className="rounded-lg overflow-hidden border">
                          <SyntaxHighlighter
                            language="hcl"
                            style={vscDarkPlus}
                            customStyle={{
                              margin: 0,
                              padding: '1rem',
                              fontSize: '13px',
                            }}
                          >
                            {fix.original_code}
                          </SyntaxHighlighter>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium mb-2 flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          Suggested Code
                        </p>
                        <div className="rounded-lg overflow-hidden border">
                          <SyntaxHighlighter
                            language="hcl"
                            style={vscDarkPlus}
                            customStyle={{
                              margin: 0,
                              padding: '1rem',
                              fontSize: '13px',
                            }}
                          >
                            {fix.suggested_code}
                          </SyntaxHighlighter>
                        </div>
                      </div>
                    </div>

                    {finding && (
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-sm font-medium mb-1">Original Finding</p>
                        <p className="text-sm text-muted-foreground">{finding.description}</p>
                        <p className="text-sm mt-2">
                          <span className="font-medium">Recommendation:</span> {finding.recommendation}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </TabsContent>

        <TabsContent value="high" className="space-y-4">
          {fixes
            .filter(fix => fix.effectiveness_score && fix.effectiveness_score >= 0.8)
            .map((fix, index) => {
              const finding = aiResult.security_analysis.findings.find(f => f.finding_id === fix.finding_id)
              return (
                <motion.div
                  key={fix.fix_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="shadow-lg border-green-500">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">
                            {finding?.title || `Fix for Finding ${fix.finding_id.slice(0, 8)}`}
                          </CardTitle>
                          <CardDescription>
                            High effectiveness fix
                          </CardDescription>
                        </div>
                        <Badge className="bg-green-500">
                          {(fix.effectiveness_score! * 100).toFixed(0)}% Effective
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-muted-foreground">{fix.explanation}</p>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium mb-2">Original</p>
                          <SyntaxHighlighter language="hcl" style={vscDarkPlus}>
                            {fix.original_code}
                          </SyntaxHighlighter>
                        </div>
                        <div>
                          <p className="text-sm font-medium mb-2">Suggested</p>
                          <SyntaxHighlighter language="hcl" style={vscDarkPlus}>
                            {fix.suggested_code}
                          </SyntaxHighlighter>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })}
        </TabsContent>

        <TabsContent value="medium" className="space-y-4">
          {fixes
            .filter(fix => fix.effectiveness_score && fix.effectiveness_score >= 0.6 && fix.effectiveness_score < 0.8)
            .map((fix, index) => {
              const finding = aiResult.security_analysis.findings.find(f => f.finding_id === fix.finding_id)
              return (
                <motion.div
                  key={fix.fix_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="shadow-lg border-amber-500">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">
                            {finding?.title || `Fix for Finding ${fix.finding_id.slice(0, 8)}`}
                          </CardTitle>
                          <CardDescription>
                            Medium effectiveness fix
                          </CardDescription>
                        </div>
                        <Badge className="bg-amber-500">
                          {(fix.effectiveness_score! * 100).toFixed(0)}% Effective
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-muted-foreground">{fix.explanation}</p>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium mb-2">Original</p>
                          <SyntaxHighlighter language="hcl" style={vscDarkPlus}>
                            {fix.original_code}
                          </SyntaxHighlighter>
                        </div>
                        <div>
                          <p className="text-sm font-medium mb-2">Suggested</p>
                          <SyntaxHighlighter language="hcl" style={vscDarkPlus}>
                            {fix.suggested_code}
                          </SyntaxHighlighter>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })}
        </TabsContent>
      </Tabs>
    </div>
  )
}

