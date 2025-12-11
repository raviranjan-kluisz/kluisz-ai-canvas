import { Sparkles, Users, AlertTriangle, RefreshCw, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useGetMyTenantPools, useListLicenseTiers } from "@/controllers/API/queries/licensing";
import useAuthStore from "@/stores/authStore";
import { cn } from "@/utils/utils";

const TIER_GRADIENTS = [
  "from-blue-500/20 to-blue-600/10 border-blue-500/20",
  "from-purple-500/20 to-purple-600/10 border-purple-500/20",
  "from-amber-500/20 to-amber-600/10 border-amber-500/20",
  "from-emerald-500/20 to-emerald-600/10 border-emerald-500/20",
  "from-rose-500/20 to-rose-600/10 border-rose-500/20",
];

export default function LicensePoolView() {
  const { isTenantAdmin, isSuperAdmin } = useAuthStore();
  const canAccessLicenseData = isTenantAdmin || isSuperAdmin;
  
  const { data: pools, isLoading, refetch } = useGetMyTenantPools({ enabled: canAccessLicenseData });
  const { data: tiers } = useListLicenseTiers({ enabled: canAccessLicenseData });

  const getTierInfo = (tierId: string) => {
    return tiers?.find((t) => t.id === tierId);
  };

  const getGradient = (index: number) => {
    return TIER_GRADIENTS[index % TIER_GRADIENTS.length];
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  const poolEntries = pools ? Object.entries(pools) : [];
  const totalLicenses = poolEntries.reduce((acc, [, pool]) => acc + pool.total_count, 0);
  const assignedLicenses = poolEntries.reduce((acc, [, pool]) => acc + pool.assigned_count, 0);
  const availableLicenses = poolEntries.reduce((acc, [, pool]) => acc + pool.available_count, 0);

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Licenses</p>
                <p className="text-3xl font-bold text-blue-600">{totalLicenses}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Available</p>
                <p className="text-3xl font-bold text-green-600">{availableLicenses}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center">
                <Users className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Assigned</p>
                <p className="text-3xl font-bold text-purple-600">{assignedLicenses}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                <RefreshCw className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pool Cards */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>License Pools</CardTitle>
            <CardDescription>Available license pools for your organization</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {poolEntries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="h-16 w-16 rounded-full bg-amber-500/20 flex items-center justify-center mb-4">
                <AlertTriangle className="h-8 w-8 text-amber-600" />
              </div>
              <h3 className="text-lg font-semibold">No License Pools</h3>
              <p className="text-muted-foreground max-w-sm mt-1">
                Your organization doesn't have any license pools yet. Contact your administrator to set up licenses.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {poolEntries.map(([tierId, pool], index) => {
                const tier = getTierInfo(tierId);
                const usagePercent = pool.total_count > 0 
                  ? Math.round((pool.assigned_count / pool.total_count) * 100)
                  : 0;
                const isLow = pool.available_count <= 2 && pool.available_count > 0;
                const isEmpty = pool.available_count === 0;

                return (
                  <Card 
                    key={tierId} 
                    className={cn(
                      "overflow-hidden transition-all hover:shadow-md",
                      `bg-gradient-to-br ${getGradient(index)}`
                    )}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="font-bold text-lg">{tier?.name || "Unknown Tier"}</h3>
                          {tier?.description && (
                            <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                              {tier.description}
                            </p>
                          )}
                        </div>
                        <Badge 
                          variant={isEmpty ? "destructive" : isLow ? "secondary" : "default"}
                          className={cn(
                            !isEmpty && !isLow && "bg-green-500"
                          )}
                        >
                          {pool.available_count} available
                        </Badge>
                      </div>

                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-muted-foreground">Usage</span>
                            <span className="font-medium">{usagePercent}%</span>
                          </div>
                          <Progress 
                            value={usagePercent} 
                            className={cn(
                              "h-2",
                              usagePercent >= 90 && "[&>div]:bg-amber-500",
                              usagePercent === 100 && "[&>div]:bg-destructive"
                            )}
                          />
                        </div>

                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Assigned</span>
                          <span className="font-medium">{pool.assigned_count} / {pool.total_count}</span>
                        </div>

                        {tier?.default_credits && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Credits per License</span>
                            <span className="font-medium">{tier.default_credits.toLocaleString()}</span>
                          </div>
                        )}

                        {tier?.default_credits_per_month && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Monthly Credits</span>
                            <span className="font-medium">+{tier.default_credits_per_month.toLocaleString()}/mo</span>
                          </div>
                        )}
                      </div>

                      {isEmpty && (
                        <div className="mt-4 p-2 rounded-lg bg-destructive/10 border border-destructive/20">
                          <p className="text-xs text-destructive text-center">
                            No licenses available. Contact admin to add more.
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
