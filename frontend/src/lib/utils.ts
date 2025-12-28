import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getRiskColor(riskScore: number): string {
  if (riskScore < 0.33) return "text-risk-low"
  if (riskScore < 0.67) return "text-risk-medium"
  return "text-risk-high"
}

export function getRiskBgColor(riskScore: number): string {
  if (riskScore < 0.33) return "bg-risk-low/10 border-risk-low"
  if (riskScore < 0.67) return "bg-risk-medium/10 border-risk-medium"
  return "bg-risk-high/10 border-risk-high"
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

