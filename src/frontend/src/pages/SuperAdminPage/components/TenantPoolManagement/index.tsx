import { useState } from "react";
import { 
  Plus, 
  Building2, 
  Users, 
  Search, 
  ChevronRight,
  Loader2,
  Edit2,
  Save,
  X,
  AlertTriangle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useGetTenantLicensePools,
  useCreateOrUpdatePool,
  useListLicenseTiers,
  type LicensePool,
} from "@/controllers/API/queries/licensing";
import { useGetTenants, type Tenant } from "@/controllers/API/queries/tenants";
import useAlertStore from "@/stores/alertStore";
import useAuthStore from "@/stores/authStore";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/utils/utils";
import { useEffect } from "react";

interface EditingPool {
  tenantId: string;
  tierId: string;
  totalCount: number;
}

interface TenantPoolManagementProps {
  initialTenantId?: string;
}

export default function TenantPoolManagement({ initialTenantId }: TenantPoolManagementProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [editingPool, setEditingPool] = useState<EditingPool | null>(null);
  const [poolData, setPoolData] = useState({ tier_id: "", total_count: 0 });

  const { isSuperAdmin } = useAuthStore();
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const queryClient = useQueryClient();

  // Only fetch data if user is a super admin
  const { data: tenants, isLoading: tenantsLoading } = useGetTenants();
  const { data: tiers } = useListLicenseTiers({ enabled: isSuperAdmin });

  // Auto-select tenant if initialTenantId is provided
  useEffect(() => {
    if (initialTenantId && tenants && !selectedTenant) {
      const tenant = tenants.find((t) => t.id === initialTenantId);
      if (tenant) {
        setSelectedTenant(tenant);
      }
    }
  }, [initialTenantId, tenants, selectedTenant]);

  const createPool = useCreateOrUpdatePool({
    onSuccess: () => {
      setSuccessData({ title: "License pool updated successfully" });
      setIsCreateDialogOpen(false);
      
      // Get the tenant ID from either selectedTenant or editingPool
      const tenantId = selectedTenant?.id || editingPool?.tenantId;
      
      // Invalidate and refetch tenant pools for this tenant
      if (tenantId) {
        queryClient.invalidateQueries({ 
          queryKey: ["useGetTenantLicensePools", tenantId] 
        });
      }
      
      // Also invalidate the tenants list to update license_pools JSON
      queryClient.invalidateQueries({ 
        queryKey: ["useGetTenants"] 
      });
      
      // Reset state
      setEditingPool(null);
      setPoolData({ tier_id: "", total_count: 0 });
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to update license pool"],
      });
    },
  });

  const handleCreatePool = async () => {
    if (!selectedTenant || !poolData.tier_id || poolData.total_count < 0) {
      setErrorData({ title: "Error", list: ["Please fill in all fields correctly"] });
      return;
    }
    await createPool.mutateAsync({
      tenantId: selectedTenant.id,
      data: poolData,
    });
  };

  const handleSaveEditingPool = async () => {
    if (!editingPool) return;
    await createPool.mutateAsync({
      tenantId: editingPool.tenantId,
      data: {
        tier_id: editingPool.tierId,
        total_count: editingPool.totalCount,
      },
    });
  };

  const getTierName = (tierId: string) => {
    return tiers?.find((t) => t.id === tierId)?.name || tierId;
  };

  const getTierById = (tierId: string) => {
    return tiers?.find((t) => t.id === tierId);
  };

  const filteredTenants = tenants?.filter(
    (tenant) => tenant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                tenant.slug.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate overall stats
  const totalTenants = tenants?.length || 0;
  const tenantsWithPools = tenants?.filter((t) => t.license_pools && Object.keys(t.license_pools).length > 0)?.length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">License Pool Management</h2>
          <p className="text-muted-foreground">
            Manage license pools for each tenant organization
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                <Building2 className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalTenants}</p>
                <p className="text-sm text-muted-foreground">Total Tenants</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center">
                <Users className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{tenantsWithPools}</p>
                <p className="text-sm text-muted-foreground">With License Pools</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                <Plus className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{tiers?.filter((t) => t.is_active)?.length || 0}</p>
                <p className="text-sm text-muted-foreground">Active Tiers</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tenants..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Tenants Accordion */}
      {tenantsLoading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      ) : filteredTenants?.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              {searchQuery ? "No tenants match your search" : "No tenants found"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Accordion type="multiple" className="space-y-4" defaultValue={selectedTenant ? [selectedTenant.id] : []}>
          {filteredTenants?.map((tenant) => (
            <TenantPoolCard 
              key={tenant.id}
              tenant={tenant}
              tiers={tiers || []}
              getTierName={getTierName}
              getTierById={getTierById}
              editingPool={editingPool}
              setEditingPool={setEditingPool}
              onSavePool={handleSaveEditingPool}
              onAddPool={() => {
                setSelectedTenant(tenant);
                setIsCreateDialogOpen(true);
              }}
              isPending={createPool.isPending}
            />
          ))}
        </Accordion>
      )}

      {/* Create/Update Pool Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add License Pool</DialogTitle>
            <DialogDescription>
              Add or update a license pool for {selectedTenant?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="tier">License Tier *</Label>
              <Select
                value={poolData.tier_id}
                onValueChange={(value) => setPoolData({ ...poolData, tier_id: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a tier" />
                </SelectTrigger>
                <SelectContent>
                  {tiers?.filter((t) => t.is_active).map((tier) => (
                    <SelectItem key={tier.id} value={tier.id}>
                      <div className="flex items-center gap-2">
                        <span>{tier.name}</span>
                        <Badge variant="secondary" className="text-xs">
                          {tier.default_credits} credits
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="total_count">Total Licenses *</Label>
              <Input
                id="total_count"
                type="number"
                min="0"
                value={poolData.total_count}
                onChange={(e) => setPoolData({ ...poolData, total_count: parseInt(e.target.value) || 0 })}
              />
              <p className="text-xs text-muted-foreground">
                Number of licenses available in this pool. Cannot be reduced below assigned count.
              </p>
            </div>
            {poolData.tier_id && (
              <div className="rounded-lg border p-4 bg-muted/50">
                <h4 className="font-medium mb-2">Tier Details</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Default Credits</span>
                    <span>{getTierById(poolData.tier_id)?.default_credits?.toLocaleString()}</span>
                  </div>
                  {getTierById(poolData.tier_id)?.default_credits_per_month && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Monthly Credits</span>
                      <span>{getTierById(poolData.tier_id)?.default_credits_per_month?.toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreatePool}
              disabled={!poolData.tier_id || poolData.total_count < 0 || createPool.isPending}
            >
              {createPool.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Pool"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Separate component for tenant pool card
interface TenantPoolCardProps {
  tenant: Tenant;
  tiers: any[];
  getTierName: (tierId: string) => string;
  getTierById: (tierId: string) => any;
  editingPool: EditingPool | null;
  setEditingPool: (pool: EditingPool | null) => void;
  onSavePool: () => void;
  onAddPool: () => void;
  isPending: boolean;
}

function TenantPoolCard({ 
  tenant, 
  tiers,
  getTierName, 
  getTierById,
  editingPool, 
  setEditingPool, 
  onSavePool,
  onAddPool,
  isPending
}: TenantPoolCardProps) {
  const { data: pools, refetch } = useGetTenantLicensePools({ 
    tenantId: tenant.id, 
    enabled: true 
  });

  const poolsArray = pools ? Object.entries(pools) : [];
  const totalLicenses = poolsArray.reduce((acc, [, pool]) => acc + pool.total_count, 0);
  const assignedLicenses = poolsArray.reduce((acc, [, pool]) => acc + pool.assigned_count, 0);

  return (
    <AccordionItem value={tenant.id} className="border rounded-lg bg-card">
      <AccordionTrigger className="px-6 hover:no-underline [&[data-state=open]>div>svg]:rotate-90">
        <div className="flex items-center justify-between w-full pr-4">
          <div className="flex items-center gap-4">
            <div className={cn(
              "h-10 w-10 rounded-lg flex items-center justify-center",
              tenant.is_active ? "bg-primary/10" : "bg-muted"
            )}>
              <Building2 className={cn(
                "h-5 w-5",
                tenant.is_active ? "text-primary" : "text-muted-foreground"
              )} />
            </div>
            <div className="text-left">
              <div className="flex items-center gap-2">
                <span className="font-semibold">{tenant.name}</span>
                <Badge variant={tenant.is_active ? "default" : "secondary"} className="text-xs">
                  {tenant.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
              <span className="text-sm text-muted-foreground">@{tenant.slug}</span>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform duration-200" />
          </div>
          <div className="flex items-center gap-6 text-sm">
            <div className="text-right">
              <p className="font-medium">{poolsArray.length}</p>
              <p className="text-xs text-muted-foreground">Pools</p>
            </div>
            <div className="text-right">
              <p className="font-medium">{totalLicenses}</p>
              <p className="text-xs text-muted-foreground">Total</p>
            </div>
            <div className="text-right">
              <p className="font-medium">{assignedLicenses}</p>
              <p className="text-xs text-muted-foreground">Assigned</p>
            </div>
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-6 pb-6">
        {poolsArray.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center border rounded-lg border-dashed">
            <AlertTriangle className="h-8 w-8 text-amber-500 mb-2" />
            <p className="text-muted-foreground mb-4">No license pools configured for this tenant</p>
            <Button onClick={onAddPool} variant="outline" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add First Pool
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-lg border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead className="w-[200px]">Tier</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Available</TableHead>
                    <TableHead>Assigned</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {poolsArray.map(([tierId, pool]) => {
                    const isEditing = editingPool?.tenantId === tenant.id && editingPool?.tierId === tierId;
                    const usagePercent = pool.total_count > 0 
                      ? Math.round((pool.assigned_count / pool.total_count) * 100) 
                      : 0;
                    const tier = getTierById(tierId);
                    
                    return (
                      <TableRow key={tierId}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{getTierName(tierId)}</span>
                            {tier?.default_credits_per_month && (
                              <Badge variant="outline" className="text-xs">
                                Subscription
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {isEditing ? (
                            <Input
                              type="number"
                              min={pool.assigned_count}
                              value={editingPool.totalCount}
                              onChange={(e) => setEditingPool({
                                ...editingPool,
                                totalCount: parseInt(e.target.value) || 0
                              })}
                              className="w-20 h-8"
                            />
                          ) : (
                            <Badge variant="secondary">{pool.total_count}</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={pool.available_count > 0 ? "default" : "destructive"}
                            className={cn(
                              pool.available_count > 0 && "bg-green-500"
                            )}
                          >
                            {pool.available_count}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{pool.assigned_count}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="w-[100px]">
                            <Progress 
                              value={usagePercent} 
                              className={cn(
                                "h-2",
                                usagePercent >= 90 && "[&>div]:bg-amber-500",
                                usagePercent === 100 && "[&>div]:bg-destructive"
                              )}
                            />
                            <p className="text-xs text-muted-foreground mt-1">{usagePercent}%</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          {isEditing ? (
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => setEditingPool(null)}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-green-600 hover:text-green-700"
                                onClick={async () => {
                                  try {
                                    await onSavePool();
                                    // Refetch to show updated data
                                    await refetch();
                                  } catch (error) {
                                    // Error is handled by mutation's onError
                                    console.error("Failed to save pool:", error);
                                  }
                                }}
                                disabled={isPending || editingPool.totalCount < pool.assigned_count}
                              >
                                {isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Save className="h-4 w-4" />
                                )}
                              </Button>
                            </div>
                          ) : (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => setEditingPool({
                                tenantId: tenant.id,
                                tierId: tierId,
                                totalCount: pool.total_count
                              })}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            <Button onClick={onAddPool} variant="outline" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Pool
            </Button>
          </div>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}
