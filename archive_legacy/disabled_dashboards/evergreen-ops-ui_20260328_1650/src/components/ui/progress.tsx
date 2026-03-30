import * as React from "react"

import { cn } from "@/lib/utils"

type ProgressProps = React.HTMLAttributes<HTMLDivElement> & {
  value?: number
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, ...props }, ref) => {
    const safeValue = Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0))

    return (
      <div
        ref={ref}
        role="progressbar"
        aria-valuenow={safeValue}
        aria-valuemin={0}
        aria-valuemax={100}
        className={cn("relative h-4 w-full overflow-hidden rounded-full bg-slate-200", className)}
        {...props}
      >
        <div
          className="h-full bg-slate-900 transition-all"
          style={{ width: `${safeValue}%` }}
        />
      </div>
    )
  }
)

Progress.displayName = "Progress"

export { Progress }
