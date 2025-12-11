// UserUsagePage - Personal usage dashboard for all users

import { useState, useMemo } from "react";
import { 
  Activity, 
  Zap, 
  TrendingUp, 
  Calendar,
  Sparkles,
  Coins,
  BarChart3,
  RefreshCw,
  Loader2,
  AlertCircle,
  ArrowLeft
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import PageLayout from "@/components/common/pageLayout";
import { useGetUserDashboard, useGetCreditStatus, type UserDashboard } from "@/controllers/API/queries/analytics";
import { useUserLimits } from "@/controllers/API/queries/features";
import { cn } from "@/utils/utils";

// Simple line chart component using CSS
const SimpleLineChart = ({ data, dataKey, color }: { data: any[]; dataKey: string; color: string }) => {
  if (!data || data.length === 0) return null;
  
  const values = data.map(d => d[dataKey] || 0);
  if (values.length === 0 || values.every(v => v === 0)) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <AlertCircle className="h-10 w-10 text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No data points to display</p>
      </div>
    );
  }
  
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1 || 1)) * 100;
    const y = 100 - ((v - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="w-full h-[200px] relative">
      <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />
        <defs>
          <linearGradient id={`gradient-${dataKey}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.05" />
          </linearGradient>
        </defs>
        <polygon
          points={`0,100 ${points} 100,100`}
          fill={`url(#gradient-${dataKey})`}
        />
      </svg>
      {/* X-axis labels */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-muted-foreground px-2">
        {data.length > 0 && (
          <>
            <span>{new Date(data[0].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
            {data.length > 2 && (
              <span>{new Date(data[Math.floor(data.length / 2)].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
            )}
            <span>{new Date(data[data.length - 1].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
          </>
        )}
      </div>
    </div>
  );
};

export default function UserUsagePage() {
  const navigate = useNavigate();
  const [dateRange, setDateRange] = useState("30d");
  
  // Calculate date range
  const { startDate, endDate } = useMemo(() => {
    const end = new Date();
    const start = new Date();
    
    switch (dateRange) {
      case "7d":
        start.setDate(end.getDate() - 7);
        break;
      case "14d":
        start.setDate(end.getDate() - 14);
        break;
      case "30d":
        start.setDate(end.getDate() - 30);
        break;
      case "90d":
        start.setDate(end.getDate() - 90);
        break;
      default:
        start.setDate(end.getDate() - 30);
    }
    
    return {
      startDate: start.toISOString(),
      endDate: end.toISOString(),
    };
  }, [dateRange]);

  // Fetch data
  const { data: dashboard, isLoading: dashboardLoading, refetch } = useGetUserDashboard({
    startDate,
    endDate,
  });
  
  const { data: creditStatus, isLoading: creditsLoading } = useGetCreditStatus();
  const { data: limits, isLoading: limitsLoading } = useUserLimits();

  const isLoading = dashboardLoading || creditsLoading || limitsLoading;

  // Calculate credit percentage
  const creditsRemaining = creditStatus?.credits_remaining ?? 0;
  const creditsAllocated = creditStatus?.credits_allocated ?? 0;
  const creditsPercentage = creditsAllocated > 0 ? Math.round((creditsRemaining / creditsAllocated) * 100) : 0;

  // Format numbers
  const formatNumber = (num: number | undefined | null) => {
    const safeNum = num ?? 0;
    if (safeNum >= 1000000) return `${(safeNum / 1000000).toFixed(1)}M`;
    if (safeNum >= 1000) return `${(safeNum / 1000).toFixed(1)}K`;
    return safeNum.toLocaleString();
  };

  // Header actions component
  const headerActions = (
    <div className="flex items-center gap-3">
      <Select value={dateRange} onValueChange={setDateRange}>
        <SelectTrigger className="w-[160px] h-9">
          <SelectValue placeholder="Select period" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="7d">Last 7 days</SelectItem>
          <SelectItem value="14d">Last 14 days</SelectItem>
          <SelectItem value="30d">Last 30 days</SelectItem>
          <SelectItem value="90d">Last 90 days</SelectItem>
        </SelectContent>
      </Select>
      <Button variant="outline" size="sm" onClick={() => refetch()} className="h-9">
        <RefreshCw className="h-4 w-4 mr-2" />
        Refresh
      </Button>
    </div>
  );

  return (
    <PageLayout
      title="My Usage"
      description="Monitor your personal usage and credit consumption"
      button={headerActions}
    >
      <div className="max-w-7xl mx-auto w-full">
        {/* Back button */}
        <div className="mb-6">
          <Button variant="outline" onClick={() => navigate(-1)} className="h-9">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-6">
          {/* Credits Card - Prominent */}
          <Card className="bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 border-primary/20">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Coins className="h-5 w-5 text-amber-500" />
                    Your Credits
                  </CardTitle>
                  <CardDescription className="mt-2">
                    {creditStatus?.license_tier?.name ? (
                      <span className="flex items-center gap-2">
                        <Badge variant="secondary">{creditStatus.license_tier.name}</Badge>
                        {creditStatus.credits_per_month != null && creditStatus.credits_per_month > 0 && (
                          <span className="text-xs">+{creditStatus.credits_per_month.toLocaleString()}/month</span>
                        )}
                      </span>
                    ) : (
                      "Your available credits"
                    )}
                  </CardDescription>
                </div>
                <Badge 
                  variant={creditsPercentage > 20 ? "default" : creditsPercentage > 10 ? "secondary" : "destructive"}
                  className="text-lg px-3 py-1"
                >
                  {creditsPercentage}% remaining
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-4xl font-bold">
                      {formatNumber(creditsRemaining)}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      of {formatNumber(creditsAllocated)} credits remaining
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-semibold text-muted-foreground">
                      {formatNumber(creditStatus?.credits_used ?? 0)}
                    </p>
                    <p className="text-sm text-muted-foreground">used</p>
                  </div>
                </div>
                <Progress 
                  value={creditsPercentage} 
                  className={cn(
                    "h-3",
                    creditsPercentage <= 10 && "[&>div]:bg-destructive",
                    creditsPercentage > 10 && creditsPercentage <= 20 && "[&>div]:bg-amber-500"
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Resource Limits Card */}
          {limits && !limits.is_superadmin && (limits.flows || limits.api_calls) && (
            <Card className="border-primary/20">
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-semibold">Resource Limits</CardTitle>
                <CardDescription>Your plan limits and current usage</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 md:grid-cols-2">
                  {/* Flow Limit */}
                  {limits.flows && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Flows</span>
                        <span className="text-sm text-muted-foreground">
                          {limits.flows.unlimited 
                            ? "Unlimited" 
                            : `${limits.flows.current} / ${limits.flows.max}`
                          }
                        </span>
                      </div>
                      {!limits.flows.unlimited && limits.flows.max && (
                        <Progress 
                          value={limits.flows.percent_used} 
                          className={cn(
                            "h-2",
                            limits.flows.percent_used >= 90 && "[&>div]:bg-destructive",
                            limits.flows.percent_used >= 75 && limits.flows.percent_used < 90 && "[&>div]:bg-amber-500"
                          )}
                        />
                      )}
                      <p className="text-xs text-muted-foreground">
                        {limits.flows.unlimited 
                          ? "No limit on flows"
                          : `${limits.flows.remaining ?? 0} flows remaining`
                        }
                      </p>
                    </div>
                  )}

                  {/* API Calls Limit */}
                  {limits.api_calls && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">API Calls (this month)</span>
                        <span className="text-sm text-muted-foreground">
                          {limits.api_calls.unlimited 
                            ? "Unlimited" 
                            : `${limits.api_calls.current} / ${limits.api_calls.max}`
                          }
                        </span>
                      </div>
                      {!limits.api_calls.unlimited && limits.api_calls.max && (
                        <Progress 
                          value={limits.api_calls.percent_used} 
                          className={cn(
                            "h-2",
                            limits.api_calls.percent_used >= 90 && "[&>div]:bg-destructive",
                            limits.api_calls.percent_used >= 75 && limits.api_calls.percent_used < 90 && "[&>div]:bg-amber-500"
                          )}
                        />
                      )}
                      <p className="text-xs text-muted-foreground">
                        {limits.api_calls.unlimited 
                          ? "No limit on API calls"
                          : `${limits.api_calls.remaining ?? 0} calls remaining`
                        }
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Usage Stats Grid */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Total Runs</p>
                    <p className="text-3xl font-bold text-blue-600">
                      {formatNumber((dashboard as any)?.summary?.total_executions ?? dashboard?.summary?.total_traces ?? 0)}
                    </p>
                  </div>
                  <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Activity className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Total Tokens</p>
                    <p className="text-3xl font-bold text-purple-600">
                      {formatNumber(dashboard?.summary?.total_tokens ?? 0)}
                    </p>
                  </div>
                  <div className="h-12 w-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Zap className="h-6 w-6 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Avg. Latency</p>
                    <p className="text-3xl font-bold text-green-600">
                      {dashboard?.summary?.average_latency 
                        ? `${(dashboard.summary.average_latency / 1000).toFixed(1)}s`
                        : "—"
                      }
                    </p>
                  </div>
                  <div className="h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Active Flows</p>
                    <p className="text-3xl font-bold text-amber-600">
                      {limits?.flows?.current ?? dashboard?.top_flows?.length ?? 0}
                    </p>
                  </div>
                  <div className="h-12 w-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <Sparkles className="h-6 w-6 text-amber-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Usage Over Time Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <BarChart3 className="h-5 w-5 text-primary" />
                Usage Over Time
              </CardTitle>
              <CardDescription>Token consumption over the selected period</CardDescription>
            </CardHeader>
            <CardContent>
              {dashboard?.time_series && dashboard.time_series.length > 0 ? (
                <SimpleLineChart 
                  data={dashboard.time_series} 
                  dataKey="tokens" 
                  color="hsl(var(--primary))"
                />
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <AlertCircle className="h-10 w-10 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No usage data for this period</p>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Top Flows */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Most Used Flows</CardTitle>
                <CardDescription>Your flows with highest usage</CardDescription>
              </CardHeader>
              <CardContent>
                {dashboard?.top_flows && dashboard.top_flows.length > 0 ? (
                  <div className="rounded-lg border overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-muted/50">
                          <TableHead>Flow</TableHead>
                          <TableHead className="text-right">Runs</TableHead>
                          <TableHead className="text-right">Tokens</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {dashboard.top_flows.slice(0, 5).map((flow: any, index) => (
                          <TableRow key={flow.flow_id || index}>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                                  #{index + 1}
                                </div>
                                <span className="font-medium truncate max-w-[150px]">
                                  {flow.flow_id?.substring(0, 8) || "Unknown"}...
                                </span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              {(flow.executions ?? flow.trace_count ?? 0).toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatNumber(flow.tokens ?? flow.total_tokens ?? 0)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
                    <p className="text-muted-foreground">No flow usage yet</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Model Usage Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Model Usage</CardTitle>
                <CardDescription>Token usage by AI model</CardDescription>
              </CardHeader>
              <CardContent>
                {dashboard?.by_model && Object.keys(dashboard.by_model).length > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(dashboard.by_model)
                      .sort((a, b) => b[1].total_tokens - a[1].total_tokens)
                      .slice(0, 5)
                      .map(([model, usage]) => {
                        const totalTokens = dashboard?.summary?.total_tokens || 1;
                        const percentage = Math.round((usage.total_tokens / totalTokens) * 100);
                        
                        return (
                          <div key={model} className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium truncate max-w-[200px]">{model}</span>
                              <span className="text-sm text-muted-foreground">
                                {formatNumber(usage.total_tokens)} ({percentage}%)
                              </span>
                            </div>
                            <Progress value={percentage} className="h-2" />
                          </div>
                        );
                      })}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
                    <p className="text-muted-foreground">No model usage yet</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Model usage will appear after you run flows with AI models
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Period Info */}
          <div className="text-center text-sm text-muted-foreground pb-4">
            Showing data from {new Date(startDate).toLocaleDateString()} to {new Date(endDate).toLocaleDateString()}
          </div>
          </div>
        )}
      </div>
    </PageLayout>
  );
}
