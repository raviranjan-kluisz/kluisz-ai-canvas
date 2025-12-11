import { useState } from "react";
import { 
  Users, 
  UserPlus, 
  UserMinus, 
  Shield, 
  ShieldOff, 
  CreditCard, 
  ArrowUp, 
  ArrowDown,
  Search,
  MoreVertical,
  RefreshCw,
  AlertCircle,
  Check,
  X,
  Loader2
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
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { 
  useListLicenseTiers, 
  useGetTenantLicensePools,
  useAssignLicense,
  useUnassignLicense,
  useUpgradeLicense,
  type LicenseTier,
} from "@/controllers/API/queries/licensing";
import { useGetTenantUsers, useCreateTenantUser, useUpdateTenantUser, useDeleteTenantUser, type Tenant } from "@/controllers/API/queries/tenants";
import useAlertStore from "@/stores/alertStore";
import { cn } from "@/utils/utils";

interface TenantUserManagementProps {
  tenant: Tenant;
  onClose?: () => void;
}

export default function TenantUserManagement({ tenant, onClose }: TenantUserManagementProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddUserDialogOpen, setIsAddUserDialogOpen] = useState(false);
  const [isAssignLicenseDialogOpen, setIsAssignLicenseDialogOpen] = useState(false);
  const [isUpgradeDialogOpen, setIsUpgradeDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [selectedTier, setSelectedTier] = useState("");
  const [preserveCredits, setPreserveCredits] = useState(true);
  const [newUserData, setNewUserData] = useState({
    username: "",
    password: "",
    is_tenant_admin: false,
    license_tier_id: "" as string | undefined,
  });

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  // Queries
  const { data: users, isLoading: usersLoading, refetch: refetchUsers } = useGetTenantUsers(tenant.id);
  const { data: pools, refetch: refetchPools } = useGetTenantLicensePools({ tenantId: tenant.id, enabled: true });
  const { data: tiers } = useListLicenseTiers();

  // Mutations
  const createUser = useCreateTenantUser();
  const updateUser = useUpdateTenantUser();
  const deleteUser = useDeleteTenantUser();
  
  const assignLicense = useAssignLicense({
    onSuccess: () => {
      setSuccessData({ title: "License Assigned", list: ["License has been assigned to the user"] });
      setIsAssignLicenseDialogOpen(false);
      setSelectedUser(null);
      setSelectedTier("");
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to assign license"] });
    },
  });

  const unassignLicense = useUnassignLicense({
    onSuccess: () => {
      setSuccessData({ title: "License Unassigned", list: ["License has been removed from the user"] });
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to unassign license"] });
    },
  });

  const upgradeLicense = useUpgradeLicense({
    onSuccess: () => {
      setSuccessData({ title: "License Upgraded", list: ["User's license has been upgraded"] });
      setIsUpgradeDialogOpen(false);
      setSelectedUser(null);
      setSelectedTier("");
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to upgrade license"] });
    },
  });

  const handleCreateUser = async () => {
    try {
      const userData: any = {
        username: newUserData.username,
        password: newUserData.password,
        is_tenant_admin: newUserData.is_tenant_admin,
      };
      
      // Only include license_tier_id if one is selected
      if (newUserData.license_tier_id) {
        userData.license_tier_id = newUserData.license_tier_id;
      }
      
      await createUser.mutateAsync({
        tenantId: tenant.id,
        data: userData,
      });
      setSuccessData({ title: "User Created", list: [`User ${newUserData.username} has been created${newUserData.license_tier_id ? ' with license' : ''}`] });
      setIsAddUserDialogOpen(false);
      setNewUserData({ username: "", password: "", is_tenant_admin: false, license_tier_id: "" });
      refetchUsers();
      refetchPools();
    } catch (error: any) {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to create user"] });
    }
  };

  const handleToggleUserActive = async (user: any) => {
    try {
      await updateUser.mutateAsync({
        tenantId: tenant.id,
        userId: user.id,
        data: { is_active: !user.is_active },
      });
      setSuccessData({ title: "User Updated", list: [`User ${user.username} is now ${user.is_active ? 'inactive' : 'active'}`] });
      refetchUsers();
    } catch (error: any) {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to update user"] });
    }
  };

  const handleToggleAdmin = async (user: any) => {
    try {
      await updateUser.mutateAsync({
        tenantId: tenant.id,
        userId: user.id,
        data: { is_tenant_admin: !user.is_tenant_admin },
      });
      setSuccessData({ title: "User Updated", list: [`User ${user.username} admin status changed`] });
      refetchUsers();
    } catch (error: any) {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to update user"] });
    }
  };

  const handleDeleteUser = async (user: any) => {
    if (!window.confirm(`Delete user "${user.username}"? This action cannot be undone.`)) return;
    try {
      await deleteUser.mutateAsync({ tenantId: tenant.id, userId: user.id });
      setSuccessData({ title: "User Deleted", list: [`User ${user.username} has been deleted`] });
      refetchUsers();
    } catch (error: any) {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to delete user"] });
    }
  };

  const handleAssignLicense = () => {
    if (!selectedUser || !selectedTier) return;
    assignLicense.mutate({ user_id: selectedUser.id, tier_id: selectedTier });
  };

  const handleUpgradeLicense = () => {
    if (!selectedUser || !selectedTier) return;
    upgradeLicense.mutate({
      user_id: selectedUser.id,
      new_tier_id: selectedTier,
      preserve_credits: preserveCredits,
    });
  };

  const handleUnassignLicense = (user: any) => {
    if (!window.confirm(`Remove license from "${user.username}"? They will lose access to licensed features.`)) return;
    unassignLicense.mutate(user.id);
  };

  const getTierName = (tierId?: string) => {
    if (!tierId) return null;
    return tiers?.find((t) => t.id === tierId)?.name || "Unknown Tier";
  };

  const getTierInfo = (tierId?: string): LicenseTier | undefined => {
    if (!tierId) return undefined;
    return tiers?.find((t) => t.id === tierId);
  };

  const getAvailableCount = (tierId: string) => {
    return pools?.[tierId]?.available_count || 0;
  };

  const getCreditsPercentage = (user: any) => {
    if (!user.credits_allocated || user.credits_allocated === 0) return 0;
    return Math.round(((user.credits_allocated - user.credits_used) / user.credits_allocated) * 100);
  };

  const filteredUsers = users?.filter(
    (user: any) => user.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate stats
  const totalUsers = users?.length || 0;
  const activeUsers = users?.filter((u: any) => u.is_active)?.length || 0;
  const licensedUsers = users?.filter((u: any) => u.license_is_active)?.length || 0;
  const totalCreditsUsed = users?.reduce((acc: number, u: any) => acc + (u.credits_used || 0), 0) || 0;

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Users</p>
                <p className="text-3xl font-bold text-blue-600">{totalUsers}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Users</p>
                <p className="text-3xl font-bold text-green-600">{activeUsers}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center">
                <Check className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Licensed Users</p>
                <p className="text-3xl font-bold text-purple-600">{licensedUsers}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                <CreditCard className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Credits Used</p>
                <p className="text-3xl font-bold text-amber-600">{totalCreditsUsed.toLocaleString()}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                <RefreshCw className="h-6 w-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* License Pools Summary */}
      {pools && Object.keys(pools).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">License Pool Availability</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              {Object.entries(pools).map(([tierId, pool]) => {
                const tierInfo = getTierInfo(tierId);
                const usagePercent = pool.total_count > 0 
                  ? Math.round((pool.assigned_count / pool.total_count) * 100) 
                  : 0;
                return (
                  <div key={tierId} className="p-4 rounded-lg border bg-card">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{tierInfo?.name || tierId}</span>
                      <Badge variant={pool.available_count > 0 ? "default" : "destructive"}>
                        {pool.available_count} available
                      </Badge>
                    </div>
                    <Progress value={usagePercent} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-1">
                      {pool.assigned_count} / {pool.total_count} assigned
                    </p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Users Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Users</CardTitle>
              <CardDescription>Manage users and their licenses for {tenant.name}</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-[250px]"
                />
              </div>
              <Button onClick={() => setIsAddUserDialogOpen(true)}>
                <UserPlus className="h-4 w-4 mr-2" />
                Add User
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {usersLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredUsers?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Users className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                {searchQuery ? "No users match your search" : "No users in this tenant yet"}
              </p>
              {!searchQuery && (
                <Button className="mt-4" onClick={() => setIsAddUserDialogOpen(true)}>
                  <UserPlus className="h-4 w-4 mr-2" />
                  Add First User
                </Button>
              )}
            </div>
          ) : (
            <div className="rounded-lg border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead className="w-[200px]">User</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>License</TableHead>
                    <TableHead>Credits</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers?.map((user: any) => (
                    <TableRow key={user.id} className="group hover:bg-muted/30">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "h-9 w-9 rounded-full flex items-center justify-center text-sm font-medium",
                            user.is_active 
                              ? "bg-primary/10 text-primary" 
                              : "bg-muted text-muted-foreground"
                          )}>
                            {user.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{user.username}</p>
                            <div className="flex items-center gap-1">
                              {user.is_tenant_admin && (
                                <Badge variant="secondary" className="text-xs py-0 px-1">
                                  <Shield className="h-3 w-3 mr-1" />
                                  Admin
                                </Badge>
                              )}
                              {user.is_platform_superadmin && (
                                <Badge variant="default" className="text-xs py-0 px-1">
                                  Super Admin
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={user.is_active ? "default" : "secondary"}>
                          {user.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {user.license_is_active ? (
                          <div className="flex flex-col gap-1">
                            <Badge variant="outline" className="w-fit">
                              {getTierName(user.license_tier_id) || "Licensed"}
                            </Badge>
                            {user.license_expires_at && (
                              <span className="text-xs text-muted-foreground">
                                Expires: {new Date(user.license_expires_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-sm">No license</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {user.license_is_active ? (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="w-[140px]">
                                  <div className="flex items-center justify-between text-xs mb-1">
                                    <span>{user.credits_allocated - user.credits_used}</span>
                                    <span className="text-muted-foreground">/ {user.credits_allocated}</span>
                                  </div>
                                  <Progress 
                                    value={getCreditsPercentage(user)} 
                                    className={cn(
                                      "h-2",
                                      getCreditsPercentage(user) < 20 && "bg-destructive/20"
                                    )}
                                  />
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{getCreditsPercentage(user)}% remaining</p>
                                {user.credits_per_month && (
                                  <p className="text-xs text-muted-foreground">
                                    +{user.credits_per_month}/month
                                  </p>
                                )}
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        ) : (
                          <span className="text-muted-foreground text-sm">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-[200px]">
                            {!user.license_is_active ? (
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedUser(user);
                                  setIsAssignLicenseDialogOpen(true);
                                }}
                              >
                                <CreditCard className="h-4 w-4 mr-2" />
                                Assign License
                              </DropdownMenuItem>
                            ) : (
                              <>
                                <DropdownMenuItem
                                  onClick={() => {
                                    setSelectedUser(user);
                                    setSelectedTier(""); // Reset selection
                                    setIsUpgradeDialogOpen(true);
                                  }}
                                >
                                  <ArrowUp className="h-4 w-4 mr-2" />
                                  Change License
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => handleUnassignLicense(user)}
                                  className="text-destructive"
                                >
                                  <UserMinus className="h-4 w-4 mr-2" />
                                  Unassign License
                                </DropdownMenuItem>
                              </>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleToggleAdmin(user)}>
                              {user.is_tenant_admin ? (
                                <>
                                  <ShieldOff className="h-4 w-4 mr-2" />
                                  Remove Admin
                                </>
                              ) : (
                                <>
                                  <Shield className="h-4 w-4 mr-2" />
                                  Make Admin
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleToggleUserActive(user)}>
                              {user.is_active ? (
                                <>
                                  <X className="h-4 w-4 mr-2" />
                                  Deactivate User
                                </>
                              ) : (
                                <>
                                  <Check className="h-4 w-4 mr-2" />
                                  Activate User
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDeleteUser(user)}
                              className="text-destructive focus:text-destructive"
                            >
                              <UserMinus className="h-4 w-4 mr-2" />
                              Delete User
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add User Dialog */}
      <Dialog open={isAddUserDialogOpen} onOpenChange={setIsAddUserDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Add New User</DialogTitle>
            <DialogDescription>
              Create a new user for {tenant.name}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={newUserData.username}
                onChange={(e) => setNewUserData({ ...newUserData, username: e.target.value })}
                placeholder="johndoe"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={newUserData.password}
                onChange={(e) => setNewUserData({ ...newUserData, password: e.target.value })}
                placeholder="••••••••"
              />
            </div>
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <Label htmlFor="admin-switch">Tenant Admin</Label>
                <p className="text-sm text-muted-foreground">
                  Can manage users and licenses for this tenant
                </p>
              </div>
              <Switch
                id="admin-switch"
                checked={newUserData.is_tenant_admin}
                onCheckedChange={(checked) => setNewUserData({ ...newUserData, is_tenant_admin: checked })}
              />
            </div>
            {pools && Object.keys(pools).length > 0 && (
              <div className="grid gap-2">
                <Label htmlFor="license-tier">Assign License (Optional)</Label>
                <Select
                  value={newUserData.license_tier_id || undefined}
                  onValueChange={(value) => setNewUserData({ ...newUserData, license_tier_id: value || undefined })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a license tier (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(pools).map(([tierId, pool]: [string, any]) => {
                      const tier = tiers?.find((t) => t.id === tierId);
                      const available = pool.available_count || 0;
                      if (!tier) return null;
                      return (
                        <SelectItem 
                          key={tierId} 
                          value={tierId}
                          disabled={available <= 0}
                        >
                          <div className="flex items-center justify-between w-full">
                            <span>{tier.name}</span>
                            <span className="text-xs text-muted-foreground ml-2">
                              {available} available
                            </span>
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Assign a license from the tenant's pool during user creation
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddUserDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateUser}
              disabled={!newUserData.username || !newUserData.password || createUser.isPending}
            >
              {createUser.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create User"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign License Dialog */}
      <Dialog open={isAssignLicenseDialogOpen} onOpenChange={setIsAssignLicenseDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Assign License</DialogTitle>
            <DialogDescription>
              Assign a license to {selectedUser?.username}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>License Tier</Label>
              <Select value={selectedTier} onValueChange={setSelectedTier}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a tier" />
                </SelectTrigger>
                <SelectContent>
                  {tiers?.filter((t) => t.is_active).map((tier) => {
                    const available = getAvailableCount(tier.id);
                    return (
                      <SelectItem 
                        key={tier.id} 
                        value={tier.id}
                        disabled={available === 0}
                      >
                        <div className="flex items-center justify-between w-full">
                          <span>{tier.name}</span>
                          <Badge variant={available > 0 ? "secondary" : "destructive"} className="ml-2">
                            {available} available
                          </Badge>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
            {selectedTier && (
              <div className="rounded-lg border p-4 bg-muted/50">
                <h4 className="font-medium mb-2">Tier Details</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Initial Credits</span>
                    <span>{getTierInfo(selectedTier)?.default_credits?.toLocaleString()}</span>
                  </div>
                  {getTierInfo(selectedTier)?.default_credits_per_month && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Monthly Credits</span>
                      <span>{getTierInfo(selectedTier)?.default_credits_per_month?.toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAssignLicenseDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleAssignLicense}
              disabled={!selectedTier || assignLicense.isPending}
            >
              {assignLicense.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Assigning...
                </>
              ) : (
                "Assign License"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upgrade/Downgrade License Dialog */}
      <Dialog open={isUpgradeDialogOpen} onOpenChange={setIsUpgradeDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Change License Tier</DialogTitle>
            <DialogDescription>
              Upgrade or downgrade {selectedUser?.username}'s license tier. Pool counts will update automatically.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {selectedUser && (
              <div className="rounded-lg border p-4 bg-blue-500/5 border-blue-500/20">
                <h4 className="font-medium text-blue-600 mb-2">Current License</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tier</span>
                    <span>{getTierName(selectedUser.license_tier_id)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Credits Remaining</span>
                    <span>{selectedUser.credits_allocated - selectedUser.credits_used}</span>
                  </div>
                </div>
              </div>
            )}
            <div className="grid gap-2">
              <Label>New License Tier</Label>
              <Select value={selectedTier} onValueChange={setSelectedTier}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a tier" />
                </SelectTrigger>
                <SelectContent>
                  {tiers?.filter((t) => t.is_active && t.id !== selectedUser?.license_tier_id).map((tier) => {
                    const available = getAvailableCount(tier.id);
                    return (
                      <SelectItem 
                        key={tier.id} 
                        value={tier.id}
                        disabled={available === 0}
                      >
                        <div className="flex items-center justify-between w-full">
                          <span>{tier.name}</span>
                          <Badge variant={available > 0 ? "secondary" : "destructive"} className="ml-2">
                            {available} available
                          </Badge>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <Label htmlFor="preserve-credits">Preserve Credits</Label>
                <p className="text-sm text-muted-foreground">
                  Add remaining credits to the new tier's default
                </p>
              </div>
              <Switch
                id="preserve-credits"
                checked={preserveCredits}
                onCheckedChange={setPreserveCredits}
              />
            </div>
            {selectedTier && selectedUser && (
              <>
                <div className="rounded-lg border p-4 bg-green-500/5 border-green-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium text-green-600">New License</h4>
                    {(() => {
                      const currentTier = getTierInfo(selectedUser.license_tier_id);
                      const newTier = getTierInfo(selectedTier);
                      const isUpgrade = (newTier?.default_credits || 0) > (currentTier?.default_credits || 0);
                      return (
                        <Badge variant={isUpgrade ? "default" : "secondary"}>
                          {isUpgrade ? (
                            <>
                              <ArrowUp className="h-3 w-3 mr-1" />
                              Upgrade
                            </>
                          ) : (
                            <>
                              <ArrowDown className="h-3 w-3 mr-1" />
                              Downgrade
                            </>
                          )}
                        </Badge>
                      );
                    })()}
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Tier</span>
                      <span>{getTierInfo(selectedTier)?.name}</span>
                    </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">New Credits</span>
                    <span>
                      {preserveCredits 
                        ? `${(selectedUser?.credits_allocated || 0) - (selectedUser?.credits_used || 0)} + ${getTierInfo(selectedTier)?.default_credits || 0} = ${((selectedUser?.credits_allocated || 0) - (selectedUser?.credits_used || 0)) + (getTierInfo(selectedTier)?.default_credits || 0)}`
                        : (getTierInfo(selectedTier)?.default_credits || 0).toLocaleString()
                      }
                    </span>
                  </div>
                  {getTierInfo(selectedTier)?.default_credits_per_month && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Monthly Credits</span>
                      <span>{getTierInfo(selectedTier)?.default_credits_per_month?.toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsUpgradeDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleUpgradeLicense}
              disabled={!selectedTier || upgradeLicense.isPending || selectedTier === selectedUser?.license_tier_id}
            >
              {upgradeLicense.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  {selectedTier && selectedUser && (() => {
                    const currentTier = getTierInfo(selectedUser.license_tier_id);
                    const newTier = getTierInfo(selectedTier);
                    const isUpgrade = (newTier?.default_credits || 0) > (currentTier?.default_credits || 0);
                    return isUpgrade ? (
                      <>
                        <ArrowUp className="h-4 w-4 mr-2" />
                        Upgrade License
                      </>
                    ) : (
                      <>
                        <ArrowDown className="h-4 w-4 mr-2" />
                        Downgrade License
                      </>
                    );
                  })()}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

