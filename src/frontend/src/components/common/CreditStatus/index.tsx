/**
 * Credit Status Component
 * 
 * Displays user's current credit balance and usage.
 * Shows a warning when credits are low.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, CheckCircle, Coins, TrendingDown } from "lucide-react";
import { useGetCreditStatus } from "@/controllers/API/queries/analytics";
import { cn } from "@/lib/utils";

interface CreditStatusProps {
  className?: string;
  compact?: boolean;
  showTier?: boolean;
}

export default function CreditStatus({ className, compact = false, showTier = true }: CreditStatusProps) {
  const { data: creditStatus, isLoading, error } = useGetCreditStatus();
  
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className={compact ? "pb-2" : undefined}>
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-2 w-full mt-2" />
        </CardContent>
      </Card>
    );
  }
  
  if (error || !creditStatus) {
    return (
      <Card className={cn("border-destructive/50", className)}>
        <CardContent className="flex items-center gap-2 p-4">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <span className="text-sm text-muted-foreground">
            Unable to load credit status
          </span>
        </CardContent>
      </Card>
    );
  }
  
  const usagePercent = creditStatus.credits_allocated > 0
    ? (creditStatus.credits_used / creditStatus.credits_allocated) * 100
    : 0;
  
  const isLow = usagePercent > 80;
  const isExhausted = creditStatus.credits_remaining <= 0;
  const isInactive = !creditStatus.license_is_active;
  
  // Get status color
  const getStatusColor = () => {
    if (isInactive || isExhausted) return "text-destructive";
    if (isLow) return "text-amber-500";
    return "text-emerald-500";
  };
  
  const getProgressColor = () => {
    if (isInactive || isExhausted) return "bg-destructive";
    if (isLow) return "bg-amber-500";
    return "bg-emerald-500";
  };
  
  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Coins className={cn("h-4 w-4", getStatusColor())} />
        <span className="text-sm font-medium">
          {creditStatus.credits_remaining.toLocaleString()}
        </span>
        <span className="text-xs text-muted-foreground">credits</span>
        {isLow && !isExhausted && (
          <TrendingDown className="h-4 w-4 text-amber-500" />
        )}
        {isExhausted && (
          <AlertCircle className="h-4 w-4 text-destructive" />
        )}
      </div>
    );
  }
  
  return (
    <Card className={cn(
      isExhausted || isInactive ? "border-destructive/50" : isLow ? "border-amber-500/50" : "",
      className
    )}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Coins className="h-4 w-4" />
            Credits
          </CardTitle>
          {creditStatus.license_is_active ? (
            <Badge variant="outline" className="text-emerald-500 border-emerald-500/50">
              <CheckCircle className="h-3 w-3 mr-1" />
              Active
            </Badge>
          ) : (
            <Badge variant="destructive">
              <AlertCircle className="h-3 w-3 mr-1" />
              Inactive
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Credits Display */}
        <div className="flex items-baseline justify-between">
          <div>
            <span className={cn("text-2xl font-bold", getStatusColor())}>
              {creditStatus.credits_remaining.toLocaleString()}
            </span>
            <span className="text-muted-foreground text-sm ml-1">
              / {creditStatus.credits_allocated.toLocaleString()}
            </span>
          </div>
          {showTier && creditStatus.license_tier && (
            <Badge variant="secondary">
              {creditStatus.license_tier.name}
            </Badge>
          )}
        </div>
        
        {/* Progress Bar */}
        <div className="space-y-1">
          <Progress 
            value={usagePercent} 
            className={cn("h-2", getProgressColor())}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{creditStatus.credits_used.toLocaleString()} used</span>
            <span>{usagePercent.toFixed(1)}%</span>
          </div>
        </div>
        
        {/* Warning Messages */}
        {isExhausted && (
          <div className="flex items-center gap-2 text-destructive text-sm bg-destructive/10 p-2 rounded-md">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>No credits remaining. Flow execution is blocked.</span>
          </div>
        )}
        
        {isLow && !isExhausted && (
          <div className="flex items-center gap-2 text-amber-600 text-sm bg-amber-500/10 p-2 rounded-md">
            <TrendingDown className="h-4 w-4 flex-shrink-0" />
            <span>Low credits. Consider upgrading your plan.</span>
          </div>
        )}
        
        {isInactive && !isExhausted && (
          <div className="flex items-center gap-2 text-destructive text-sm bg-destructive/10 p-2 rounded-md">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>License inactive. Contact your administrator.</span>
          </div>
        )}
        
        {/* Monthly Credits Info */}
        {creditStatus.credits_per_month && (
          <div className="text-xs text-muted-foreground pt-2 border-t">
            <span className="font-medium">{creditStatus.credits_per_month.toLocaleString()}</span> credits/month
          </div>
        )}
      </CardContent>
    </Card>
  );
}

