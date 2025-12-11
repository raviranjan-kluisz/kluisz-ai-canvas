/**
 * Usage Analytics Component for Super Admin
 * 
 * Features:
 * - Platform-wide overview
 * - Tenant-wise filtering and detailed view
 * - User-wise breakdown within each tenant
 * - Cost in USD for super admin, credits for others
 * - Best UX with tables and progress bars
 */

import { useState, useMemo, useCallback } from "react";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
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
  DollarSign,
  Users,
  Zap,
  TrendingUp,
  Building2,
  RefreshCw,
  Search,
  ChevronRight,
  Coins,
  AlertCircle,
} from "lucide-react";
import {
  useGetPlatformDashboard,
  useGetTenantDashboard,
  useSyncUsageStats,
  type TenantDashboard,
} from "@/controllers/API/queries/analytics";
import { useGetTenants, type Tenant } from "@/controllers/API/queries/tenants";
import moment from "moment";
import useAuthStore from "@/stores/authStore";
import { cn } from "@/utils/utils";

interface UsageAnalyticsProps {
  className?: string;
}

export default function UsageAnalytics({ className }: UsageAnalyticsProps) {
  const [dateRange, setDateRange] = useState<"7d" | "30d" | "90d">("30d");
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"overview" | "tenant">("overview");
  
  const userData = useAuthStore((state) => state.userData);
  const isSuperAdmin = userData?.is_platform_superadmin ?? false;
  
  // Memoize date range to prevent unnecessary re-fetches
  const { startDate, endDate } = useMemo(() => {
    const days = dateRange === "7d" ? 7 : dateRange === "30d" ? 30 : 90;
    // Round to start of day to keep consistent timestamps
    const end = moment().endOf("day");
    const start = moment().subtract(days, "days").startOf("day");
    return {
      startDate: start.toISOString(),
      endDate: end.toISOString(),
    };
  }, [dateRange]);
  
  // Queries
  const { data: tenants, isLoading: tenantsLoading } = useGetTenants();
  const { data: platformDashboard, isLoading: platformLoading, refetch: refetchPlatform } = useGetPlatformDashboard({
    startDate,
    endDate,
    enabled: isSuperAdmin && viewMode === "overview",
  });
  const { data: tenantDashboard, isLoading: tenantLoading, refetch: refetchTenant } = useGetTenantDashboard(
    selectedTenantId || "",
    {
      startDate,
      endDate,
      enabled: isSuperAdmin && viewMode === "tenant" && !!selectedTenantId,
    }
  );
  
  const syncStatsMutation = useSyncUsageStats();
  
  // Filter tenants by search
  const filteredTenants = useMemo(() => {
    if (!tenants) return [];
    if (!searchQuery) return tenants;
    return tenants.filter(
      (t) =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.slug.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [tenants, searchQuery]);
  
  // Get selected tenant
  const selectedTenant = useMemo(() => {
    if (!selectedTenantId || !tenants) return null;
    return tenants.find((t) => t.id === selectedTenantId) || null;
  }, [selectedTenantId, tenants]);
  
  const handleSyncStats = async () => {
    await syncStatsMutation.mutateAsync({ startDate, endDate });
    if (viewMode === "overview") {
      refetchPlatform();
    } else {
      refetchTenant();
    }
  };
  
  const handleSelectTenant = (tenantId: string) => {
    setSelectedTenantId(tenantId);
    setViewMode("tenant");
  };
  
  const handleBackToOverview = () => {
    setSelectedTenantId(null);
    setViewMode("overview");
  };
  
  if (!isSuperAdmin) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Only super admins can view usage analytics</p>
        </CardContent>
      </Card>
    );
  }
  
  const isLoading = platformLoading || tenantLoading || tenantsLoading;
  const hasError = platformDashboard?.error || tenantDashboard?.error;
  
  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          {viewMode === "tenant" && selectedTenant && (
            <Button variant="ghost" size="sm" onClick={handleBackToOverview}>
              <ChevronRight className="h-4 w-4 rotate-180 mr-1" />
              Back
            </Button>
          )}
          <div>
            <h3 className="text-xl font-semibold flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              {viewMode === "overview" ? "Platform Usage Analytics" : `${selectedTenant?.name} Usage`}
            </h3>
            <p className="text-sm text-muted-foreground">
              {viewMode === "overview" 
                ? "Monitor usage across all tenants"
                : "Detailed usage breakdown for this tenant"
              }
            </p>
          </div>
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
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncStats}
            disabled={syncStatsMutation.isPending}
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", syncStatsMutation.isPending && "animate-spin")} />
            Sync
          </Button>
        </div>
      </div>
      
      {/* Error State */}
      {hasError && (
        <Card className="border-amber-500/50 bg-amber-500/5">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-amber-500" />
            <div>
              <p className="font-medium text-amber-600">Langfuse Not Configured</p>
              <p className="text-sm text-muted-foreground">
                Set KLUISZ_LANGFUSE_* environment variables to enable real-time analytics
              </p>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Main Content */}
      {viewMode === "overview" ? (
        <PlatformOverview
          dashboard={platformDashboard}
          tenants={filteredTenants}
          isLoading={isLoading}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onSelectTenant={handleSelectTenant}
        />
      ) : (
        <TenantDetail
          tenant={selectedTenant}
          dashboard={tenantDashboard}
          isLoading={tenantLoading}
          isSuperAdmin={isSuperAdmin}
        />
      )}
    </div>
  );
}

// Platform Overview Component
function PlatformOverview({
  dashboard,
  tenants,
  isLoading,
  searchQuery,
  onSearchChange,
  onSelectTenant,
}: {
  dashboard: any;
  tenants: Tenant[];
  isLoading: boolean;
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onSelectTenant: (id: string) => void;
}) {
  const summary = dashboard?.summary || {
    total_executions: 0,
    total_credits: 0,
    total_tokens: 0,
    total_cost_usd: 0,
    total_tenants: 0,
    total_active_users: 0,
  };
  
  const topTenants = dashboard?.top_tenants || [];
  const byModel = dashboard?.by_model || {};
  const timeSeries = dashboard?.time_series || [];
  
  if (isLoading) {
    return <LoadingSkeleton />;
  }
  
  return (
    <>
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Total Flow Executions"
          value={(summary.total_executions || 0).toLocaleString()}
          subtitle={`${(summary.total_credits || 0).toLocaleString()} credits`}
          icon={Activity}
          color="violet"
        />
        <SummaryCard
          title="Total Tokens Used"
          value={`${(summary.total_tokens / 1000000).toFixed(2)}M`}
          subtitle={`${summary.total_tokens.toLocaleString()} tokens`}
          icon={Zap}
          color="cyan"
        />
        <SummaryCard
          title="Total Cost (USD)"
          value={`$${summary.total_cost_usd.toFixed(2)}`}
          subtitle="Actual LLM cost"
          icon={DollarSign}
          color="emerald"
        />
        <SummaryCard
          title="Active Users"
          value={summary.total_active_users || 0}
          subtitle={`Across ${summary.total_tenants || 0} tenants`}
          icon={Users}
          color="amber"
        />
      </div>
      
      {/* Usage Breakdown */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Daily Usage Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              Usage Trends
            </CardTitle>
            <CardDescription>Daily activity breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {timeSeries.length > 0 ? (
              <div className="space-y-4">
                {timeSeries.slice(-7).map((day: any) => {
                  const maxExecs = Math.max(...timeSeries.map((d: any) => d.executions || 1));
                  return (
                    <div key={day.date} className="flex items-center gap-4">
                      <div className="w-20 text-sm text-muted-foreground">
                        {moment(day.date).format("MMM D")}
                      </div>
                      <div className="flex-1">
                        <Progress 
                          value={Math.min(((day.executions || 0) / maxExecs) * 100, 100)} 
                          className="h-2"
                        />
                      </div>
                      <div className="w-24 text-right">
                        <span className="text-sm font-medium">{day.executions || 0}</span>
                        <span className="text-xs text-muted-foreground ml-1">runs</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState message="No usage data for this period" />
            )}
          </CardContent>
        </Card>
        
        {/* Cost by Model */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-primary" />
              Cost by Model
            </CardTitle>
            <CardDescription>LLM cost breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {Object.keys(byModel).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(byModel)
                  .sort(([, a]: any, [, b]: any) => b.total_cost_usd - a.total_cost_usd)
                  .slice(0, 6)
                  .map(([model, data]: [string, any]) => {
                    const totalCost = Object.values(byModel).reduce((sum: number, m: any) => sum + m.total_cost_usd, 0);
                    const percent = totalCost > 0 ? (data.total_cost_usd / totalCost) * 100 : 0;
                    return (
                      <div key={model} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="font-medium truncate max-w-[150px]">{model}</span>
                          <span className="text-emerald-600">${data.total_cost_usd.toFixed(4)}</span>
                        </div>
                        <Progress value={percent} className="h-2" />
                        <p className="text-xs text-muted-foreground">
                          {data.trace_count} traces • {(data.total_tokens / 1000).toFixed(1)}k tokens
                        </p>
                      </div>
                    );
                  })}
              </div>
            ) : (
              <EmptyState message="No model usage data" />
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Tenant List with Usage */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Building2 className="h-4 w-4 text-primary" />
                Tenant Usage
              </CardTitle>
              <CardDescription>Click on a tenant to view detailed user breakdown</CardDescription>
            </div>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tenants..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {tenants.length > 0 ? (
            <div className="space-y-3">
              {tenants.map((tenant) => {
                const tenantUsage = topTenants.find((t: any) => t.tenant_id === tenant.id);
                const usage = tenantUsage || { executions: 0, tokens: 0, cost_usd: 0, active_users_count: 0, credits_used: 0 };
                
                return (
                  <div
                    key={tenant.id}
                    onClick={() => onSelectTenant(tenant.id)}
                    className="flex items-center justify-between p-4 rounded-xl border bg-card hover:bg-muted/50 cursor-pointer transition-all group"
                  >
                    <div className="flex items-center gap-4">
                      <div className={cn(
                        "h-12 w-12 rounded-xl flex items-center justify-center transition-colors",
                        tenant.is_active ? "bg-primary/10 group-hover:bg-primary/20" : "bg-muted"
                      )}>
                        <Building2 className={cn(
                          "h-6 w-6",
                          tenant.is_active ? "text-primary" : "text-muted-foreground"
                        )} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-semibold group-hover:text-primary transition-colors">{tenant.name}</p>
                          <Badge variant={tenant.is_active ? "default" : "secondary"} className="text-xs">
                            {tenant.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">@{tenant.slug}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-8">
                      <div className="text-right">
                        <p className="text-sm font-medium">{(usage.executions || 0).toLocaleString()}</p>
                        <p className="text-xs text-muted-foreground">Executions</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{((usage.tokens || 0) / 1000).toFixed(1)}k</p>
                        <p className="text-xs text-muted-foreground">Tokens</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-emerald-600">${(usage.cost_usd || 0).toFixed(2)}</p>
                        <p className="text-xs text-muted-foreground">Cost</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{usage.active_users_count || 0}</p>
                        <p className="text-xs text-muted-foreground">Users</p>
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyState message="No tenants found" />
          )}
        </CardContent>
      </Card>
    </>
  );
}

// Tenant Detail Component
function TenantDetail({
  tenant,
  dashboard,
  isLoading,
  isSuperAdmin,
}: {
  tenant: Tenant | null;
  dashboard: TenantDashboard | undefined;
  isLoading: boolean;
  isSuperAdmin: boolean;
}) {
  if (isLoading) {
    return <LoadingSkeleton />;
  }
  
  if (!tenant || !dashboard) {
    return <EmptyState message="Select a tenant to view details" />;
  }
  
  const summary = dashboard.summary || {
    total_executions: 0,
    total_credits: 0,
    total_tokens: 0,
    total_cost_usd: 0,
    active_users_count: 0,
  };
  
  const topUsers = dashboard.top_users || [];
  const topFlows = dashboard.top_flows || [];
  
  return (
    <>
      {/* Tenant Info Header */}
      <Card className="bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 border-primary/20">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-2xl bg-primary/20 flex items-center justify-center">
              <Building2 className="h-8 w-8 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-bold">{tenant.name}</h2>
                <Badge variant={tenant.is_active ? "default" : "secondary"}>
                  {tenant.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
              <p className="text-muted-foreground">@{tenant.slug}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Flow Executions"
          value={(summary.total_executions || 0).toLocaleString()}
          subtitle={`${(summary.total_credits || 0).toLocaleString()} credits`}
          icon={Activity}
          color="violet"
        />
        <SummaryCard
          title="Tokens Used"
          value={`${((summary.total_tokens || 0) / 1000).toFixed(1)}k`}
          subtitle={`${(summary.total_tokens || 0).toLocaleString()} tokens`}
          icon={Zap}
          color="cyan"
        />
        <SummaryCard
          title={isSuperAdmin ? "Cost (USD)" : "Credits Used"}
          value={isSuperAdmin ? `$${(summary.total_cost_usd || 0).toFixed(2)}` : `${(summary.total_credits || 0).toLocaleString()}`}
          subtitle={isSuperAdmin ? "Actual LLM cost" : "Based on tier pricing"}
          icon={isSuperAdmin ? DollarSign : Coins}
          color="emerald"
        />
        <SummaryCard
          title="Active Users"
          value={summary.active_users_count || 0}
          subtitle="In this period"
          icon={Users}
          color="amber"
        />
      </div>
      
      {/* Top Flows */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Most Used Flows</CardTitle>
          <CardDescription>Top flows by execution count</CardDescription>
        </CardHeader>
        <CardContent>
          {topFlows.length > 0 ? (
            <div className="space-y-3">
              {topFlows.slice(0, 5).map((flow: any, index: number) => (
                <div
                  key={flow.flow_id}
                  className="flex items-center gap-4 p-3 rounded-lg bg-muted/50"
                >
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-sm font-bold">
                    #{index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{flow.flow_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {flow.executions || 0} executions • {((flow.tokens || 0) / 1000).toFixed(1)}k tokens
                    </p>
                  </div>
                  {isSuperAdmin && (
                    <div className="text-right">
                      <p className="text-sm font-medium text-emerald-600">${(flow.cost_usd || 0).toFixed(4)}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No flow data" />
          )}
        </CardContent>
      </Card>
      
      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="h-4 w-4 text-primary" />
            User Usage Breakdown
          </CardTitle>
          <CardDescription>
            {isSuperAdmin ? "Usage and cost per user" : "Usage and credits per user"}
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
                  {isSuperAdmin && <TableHead className="text-right">Cost (USD)</TableHead>}
                  <TableHead className="text-right">Credits</TableHead>
                  <TableHead className="text-right">Remaining</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {topUsers.map((user: any) => {
                  const creditsRemaining = user.credits_remaining ?? ((user.credits_allocated || 0) - (user.credits_used || 0));
                  const usagePercent = user.credits_allocated > 0 
                    ? (((user.credits_used || 0) / user.credits_allocated) * 100) 
                    : 0;
                  const isLow = usagePercent > 80;
                  
                  return (
                    <TableRow key={user.user_id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <Users className="h-4 w-4 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium">{user.username}</p>
                            <p className="text-xs text-muted-foreground truncate max-w-[150px]">
                              {user.user_id}
                            </p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {(user.executions || 0).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {((user.tokens || 0) / 1000).toFixed(1)}k
                      </TableCell>
                      {isSuperAdmin && (
                        <TableCell className="text-right font-mono text-emerald-600">
                          ${(user.cost_usd || 0).toFixed(4)}
                        </TableCell>
                      )}
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span className="font-mono">{(user.credits_used || 0).toLocaleString()}</span>
                          <span className="text-muted-foreground">/</span>
                          <span className="text-muted-foreground">{(user.credits_allocated || 0).toLocaleString()}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span className={cn(
                            "font-mono font-medium",
                            isLow ? "text-amber-600" : "text-emerald-600"
                          )}>
                            {creditsRemaining.toLocaleString()}
                          </span>
                          {isLow && <AlertCircle className="h-4 w-4 text-amber-500" />}
                        </div>
                        <Progress 
                          value={usagePercent} 
                          className={cn("h-1 mt-1", isLow ? "bg-amber-100" : "")} 
                        />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <EmptyState message="No user data available" />
          )}
        </CardContent>
      </Card>
    </>
  );
}

// Summary Card Component
function SummaryCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ElementType;
  color: "violet" | "cyan" | "emerald" | "amber";
}) {
  const colorClasses = {
    violet: "from-violet-500/10 to-violet-600/5 border-violet-500/20 text-violet-600",
    cyan: "from-cyan-500/10 to-cyan-600/5 border-cyan-500/20 text-cyan-600",
    emerald: "from-emerald-500/10 to-emerald-600/5 border-emerald-500/20 text-emerald-600",
    amber: "from-amber-500/10 to-amber-600/5 border-amber-500/20 text-amber-600",
  };
  
  const iconBgClasses = {
    violet: "bg-violet-500/20",
    cyan: "bg-cyan-500/20",
    emerald: "bg-emerald-500/20",
    amber: "bg-amber-500/20",
  };
  
  return (
    <Card className={`bg-gradient-to-br ${colorClasses[color]}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={`h-8 w-8 rounded-full ${iconBgClasses[color]} flex items-center justify-center`}>
          <Icon className={`h-4 w-4 ${colorClasses[color].split(" ").pop()}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${colorClasses[color].split(" ").pop()}`}>{value}</div>
        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

// Loading Skeleton
function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="h-3 w-20 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Empty State
function EmptyState({ message }: { message: string }) {
  return (
    <div className="h-[200px] flex flex-col items-center justify-center text-muted-foreground">
      <Activity className="h-10 w-10 mb-2 opacity-50" />
      <p>{message}</p>
    </div>
  );
}
