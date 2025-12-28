"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { ExecutiveDashboard } from "@/components/executive-dashboard"
import { reviewApi, type Analytics } from "@/lib/api"
import { useAuth } from "@/components/auth-provider"
import { motion } from "framer-motion"

export default function ExecutivePage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
      return
    }

    if (user) {
      loadData()
      const interval = setInterval(loadData, 30000) // Update every 30 seconds
      return () => clearInterval(interval)
    }
  }, [user, authLoading, router])

  const loadData = async () => {
    try {
      const data = await reviewApi.getAnalytics(90) // Last 90 days
      setAnalytics(data)
    } catch (error) {
      console.error("Error loading analytics:", error)
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full"
        />
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">No data available</p>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <ExecutiveDashboard analytics={analytics} />
    </main>
  )
}

