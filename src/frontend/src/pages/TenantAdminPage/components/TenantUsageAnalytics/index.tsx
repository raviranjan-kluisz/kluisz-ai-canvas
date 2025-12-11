/**
 * Tenant Usage Analytics Component
 * 
 * For Tenant Admins - shows cost in credits, NOT USD
 * Only super admins see actual USD costs
 */

import { useState, useMemo } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Activity,
  Users,
  Zap,
  Coins,
  AlertCircle,
  TrendingUp,
  RefreshCw,
} from "lucide-react";
import { useGetTenantDashboard } from "@/controllers/API/queries/analytics";
import moment from "moment";
import useAuthStore from "@/stores/authStore";
import { cn } from "@/utils/utils";

interface TenantUsageAnalyticsProps {
  tenantId: string;
  className?: string;
}

export default function TenantUsageAnalytics({ tenantId, className }: TenantUsageAnalyticsProps) {
  const [dateRange, setDateRange] = useState<"7d" | "30d" | "90d">("30d");
  
  const userData = useAuthStore((state) => state.userData);
  
  // Memoize date range to prevent unnecessary re-fetches
  const { startDate, endDate } = useMemo(() => {
    const days = dateRange === "7d" ? 7 : dateRange === "30d" ? 30 : 90;
    const end = moment().endOf("day");
    const start = moment().subtract(days, "days").startOf("day");
    return {
      startDate: start.toISOString(),
      endDate: end.toISOString(),
    };
  }, [dateRange]);
  
  const { data: dashboard, isLoading, refetch } = useGetTenantDashboard(tenantId, {
    startDate,
    endDate,
    enabled: !!tenantId,
  });
  
  if (isLoading) {
    return (
      <div className={cn("space-y-6", className)}>
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }
  
  if (dashboard?.error) {
    return (
      <Card className={cn("border-amber-500/50 bg-amber-500/5", className)}>
        <CardContent className="flex items-center gap-3 py-6">
          <AlertCircle className="h-5 w-5 text-amber-500" />
          <div>
            <p className="font-medium">Analytics Not Available</p>
            <p className="text-sm text-muted-foreground">
              Usage analytics will appear here once configured
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  const summary = dashboard?.summary || {
    total_executions: 0,
    total_credits: 0,
    total_tokens: 0,
    total_cost_usd: 0,
    active_users_count: 0,
  };
  
  const topUsers = dashboard?.top_users || [];
  const topFlows = dashboard?.top_flows || [];
  const timeSeries = dashboard?.time_series || [];
  
  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Usage Analytics
          </h3>
          <p className="text-sm text-muted-foreground">
            Track your organization's usage and credits
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={dateRange} onValueChange={(v: "7d" | "30d" | "90d") => setDateRange(v)}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      {/* Summary Cards - NO USD, only credits for tenant admins */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-gradient-to-br from-violet-500/10 to-violet-600/5 border-violet-500/20">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Flow Executions
            </CardTitle>
            <div className="h-8 w-8 rounded-full bg-violet-500/20 flex items-center justify-center">
              <Activity className="h-4 w-4 text-violet-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-violet-600">
              {(summary.total_executions || 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {(summary.total_credits || 0).toLocaleString()} credits used
            </p>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-cyan-500/10 to-cyan-600/5 border-cyan-500/20">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Tokens Used
            </CardTitle>
            <div className="h-8 w-8 rounded-full bg-cyan-500/20 flex items-center justify-center">
              <Zap className="h-4 w-4 text-cyan-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-cyan-600">
              {(summary.total_tokens / 1000).toFixed(1)}k
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {summary.total_tokens.toLocaleString()} tokens
            </p>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Users
            </CardTitle>
            <div className="h-8 w-8 rounded-full bg-amber-500/20 flex items-center justify-center">
              <Users className="h-4 w-4 text-amber-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">
              {summary.active_users_count || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              In this period
            </p>
          </CardContent>
        </Card>
      </div>
      
      {/* Usage Trends - Simple bar visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Usage Trends
          </CardTitle>
          <CardDescription>Daily flow executions</CardDescription>
        </CardHeader>
        <CardContent>
          {timeSeries.length > 0 ? (
            <div className="space-y-3">
              {timeSeries.slice(-7).map((day: any) => {
                const maxExecs = Math.max(...timeSeries.map((d: any) => d.executions || 1));
                const percent = ((day.executions || 0) / maxExecs) * 100;
                return (
                  <div key={day.date} className="flex items-center gap-4">
                    <div className="w-20 text-sm text-muted-foreground">
                      {moment(day.date).format("MMM D")}
                    </div>
                    <div className="flex-1">
                      <Progress value={percent} className="h-3" />
                    </div>
                    <div className="w-20 text-right">
                      <span className="text-sm font-medium">{day.executions || 0}</span>
                      <span className="text-xs text-muted-foreground ml-1">runs</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-[200px] flex flex-col items-center justify-center text-muted-foreground">
              <Activity className="h-10 w-10 mb-2 opacity-50" />
              <p>No usage data for this period</p>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Users Table with Credits - NO USD shown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="h-4 w-4 text-primary" />
            User Usage & Credits
          </CardTitle>
          <CardDescription>
            Usage and remaining credits per user
          </CardDescription>
        </CardHeader>
        <CardContent>
          {topUsers.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead className="text-right">Executions</TableHead>
                  <TableHead className="text-right">Tokens</TableHead>
                  <TableHead className="text-right">Credits Used</TableHead>
                  <TableHead className="text-right">Credits Remaining</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {topUsers.map((user: any) => {
                  const creditsRemaining = user.credits_remaining ?? ((user.credits_allocated || 0) - (user.credits_used || 0));
                  const usagePercent = user.credits_allocated > 0 
                    ? (((user.credits_used || 0) / user.credits_allocated) * 100) 
                    : 0;
                  const isLow = usagePercent > 80;
                  const isExhausted = creditsRemaining <= 0;
                  
                  return (
                    <TableRow key={user.user_id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <Users className="h-4 w-4 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium">{user.username}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {(user.executions || 0).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {((user.tokens || 0) / 1000).toFixed(1)}k
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Coins className="h-4 w-4 text-muted-foreground" />
                          <span className="font-mono">{(user.credits_used || 0).toLocaleString()}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="space-y-1">
                          <div className="flex items-center justify-end gap-2">
                            <span className={cn(
                              "font-mono font-medium",
                              isExhausted ? "text-destructive" : isLow ? "text-amber-600" : "text-emerald-600"
                            )}>
                              {creditsRemaining.toLocaleString()}
                            </span>
                            {isExhausted && <AlertCircle className="h-4 w-4 text-destructive" />}
                            {isLow && !isExhausted && <AlertCircle className="h-4 w-4 text-amber-500" />}
                          </div>
                          <Progress 
                            value={usagePercent} 
                            className={cn(
                              "h-1",
                              isExhausted ? "bg-destructive/20" : isLow ? "bg-amber-100" : ""
                            )} 
                          />
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="h-32 flex flex-col items-center justify-center text-muted-foreground">
              <Users className="h-8 w-8 mb-2 opacity-50" />
              <p>No user data available</p>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Top Flows */}
      {topFlows.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Most Used Flows</CardTitle>
            <CardDescription>Top flows by execution count</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topFlows.slice(0, 5).map((flow: any, index: number) => (
                <div
                  key={flow.flow_id}
                  className="flex items-center gap-4 p-3 rounded-lg bg-muted/50"
                >
                  <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center text-sm font-bold">
                    #{index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{flow.flow_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {flow.executions || 0} executions • {((flow.tokens || 0) / 1000).toFixed(1)}k tokens
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
