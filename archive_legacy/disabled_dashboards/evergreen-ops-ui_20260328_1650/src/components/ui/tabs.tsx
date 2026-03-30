"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

type TabsContextValue = {
  value: string
  setValue: (value: string) => void
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

function useTabsContext() {
  const context = React.useContext(TabsContext)
  if (!context) {
    throw new Error("Tabs components must be used within Tabs")
  }
  return context
}

type TabsProps = React.HTMLAttributes<HTMLDivElement> & {
  defaultValue: string
  value?: string
  onValueChange?: (value: string) => void
}

const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  ({ className, defaultValue, value, onValueChange, children, ...props }, ref) => {
    const [internalValue, setInternalValue] = React.useState(defaultValue)
    const currentValue = value ?? internalValue

    const setValue = React.useCallback(
      (nextValue: string) => {
        if (value === undefined) {
          setInternalValue(nextValue)
        }
        onValueChange?.(nextValue)
      },
      [onValueChange, value]
    )

    return (
      <TabsContext.Provider value={{ value: currentValue, setValue }}>
        <div ref={ref} className={cn("w-full", className)} {...props}>
          {children}
        </div>
      </TabsContext.Provider>
    )
  }
)

Tabs.displayName = "Tabs"

const TabsList = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "inline-flex min-h-10 items-center justify-center rounded-md bg-slate-100 p-1 text-slate-500",
        className
      )}
      {...props}
    />
  )
)

TabsList.displayName = "TabsList"

type TabsTriggerProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  value: string
}

const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, value, onClick, ...props }, ref) => {
    const context = useTabsContext()
    const isActive = context.value === value

    return (
      <button
        ref={ref}
        type="button"
        data-state={isActive ? "active" : "inactive"}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all",
          isActive ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-900",
          className
        )}
        onClick={(event) => {
          context.setValue(value)
          onClick?.(event)
        }}
        {...props}
      />
    )
  }
)

TabsTrigger.displayName = "TabsTrigger"

type TabsContentProps = React.HTMLAttributes<HTMLDivElement> & {
  value: string
}

const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, value, children, ...props }, ref) => {
    const context = useTabsContext()
    if (context.value !== value) {
      return null
    }

    return (
      <div
        ref={ref}
        data-state="active"
        className={cn("mt-2 focus-visible:outline-none", className)}
        {...props}
      >
        {children}
      </div>
    )
  }
)

TabsContent.displayName = "TabsContent"

export { Tabs, TabsList, TabsTrigger, TabsContent }
