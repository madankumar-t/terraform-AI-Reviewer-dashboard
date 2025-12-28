"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { LayoutDashboard, FileText, GitBranch, TrendingUp, Shield, Home } from "lucide-react"
import { useAuth } from "@/components/auth-provider"
import { motion } from "framer-motion"

export function Navigation() {
  const pathname = usePathname()
  const { user, signOut } = useAuth()

  const navItems = [
    { href: "/", label: "Home", icon: Home },
    { href: "/executive", label: "Executive", icon: TrendingUp },
    { href: "/spacelift-runs", label: "Spacelift Runs", icon: GitBranch },
    { href: "/compliance", label: "Compliance", icon: Shield },
  ]

  return (
    <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Terraform AI Reviewer
            </Link>
            <div className="hidden md:flex items-center gap-2">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href))
                return (
                  <Link key={item.href} href={item.href}>
                    <Button
                      variant={isActive ? "default" : "ghost"}
                      size="sm"
                      className={isActive ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white" : ""}
                    >
                      <Icon className="h-4 w-4 mr-2" />
                      {item.label}
                    </Button>
                  </Link>
                )
              })}
            </div>
          </div>
          {user && (
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium">{user.email}</p>
                <p className="text-xs text-muted-foreground">
                  {user.groups.join(', ')}
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={signOut}>
                Sign Out
              </Button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

