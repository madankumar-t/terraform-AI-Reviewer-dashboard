"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { FixEffectivenessComparison } from "@/components/fix-effectiveness-comparison"
import { reviewApi, type Review } from "@/lib/api"
import { useAuth } from "@/components/auth-provider"
import { motion } from "framer-motion"

export default function FixComparisonPage() {
  const params = useParams()
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [review, setReview] = useState<Review | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
      return
    }

    if (user && params.reviewId) {
      loadReview()
    }
  }, [user, authLoading, params.reviewId, router])

  const loadReview = async () => {
    try {
      const data = await reviewApi.getReview(params.reviewId as string)
      setReview(data)
    } catch (error) {
      console.error("Error loading review:", error)
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

  if (!review) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Review not found</p>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <FixEffectivenessComparison review={review} />
    </main>
  )
}

