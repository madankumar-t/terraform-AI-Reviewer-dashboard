import { Dashboard } from "@/components/dashboard"
import { useAuth } from "@/components/auth-provider"
import { redirect } from "next/navigation"

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Dashboard />
    </main>
  )
}

