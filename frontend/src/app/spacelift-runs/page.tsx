"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { SpaceliftRunHistory } from "@/components/spacelift-run-history"
import { reviewApi, type Review } from "@/lib/api"
import { useAuth } from "@/components/auth-provider"
import { motion } from "framer-motion"

export default function SpaceliftRunsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
      return
    }

    if (user) {
      loadRuns()
      const interval = setInterval(loadRuns, 15000) // Update every 15 seconds
      return () => clearInterval(interval)
    }
  }, [user, authLoading, router])

  const loadRuns = async () => {
    try {
      const data = await reviewApi.getReviews({ limit: 100 })
      // Filter for Spacelift runs only
      const spaceliftReviews = data.reviews.filter(r => r.spacelift_run_id)
      setReviews(spaceliftReviews)
    } catch (error) {
      console.error("Error loading runs:", error)
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

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <SpaceliftRunHistory reviews={reviews} />
    </main>
  )
}

