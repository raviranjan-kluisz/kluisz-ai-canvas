// TenantAdminPage - Tenant-level administration for managing tenant users and licenses

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  Users, 
  Plus, 
  CreditCard, 
  BarChart3, 
  AlertCircle, 
  ArrowLeft, 
  Settings,
  Search,
  MoreVertical,
  Loader2,
  Sparkles,
  UserPlus,
  UserMinus,
  ArrowUp,
  ArrowDown,
  Shield,
  ShieldOff,
  Check,
  X,
  RefreshCw,
  AlertTriangle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { useGetTenant, useGetTenantUsers, useGetTenantUserCount, useUpdateTenant, useCreateTenantUser, useUpdateTenantUser, useDeleteTenantUser } from "@/controllers/API/queries/tenants";
import { useGetActiveLicense, useUpdateLicense } from "@/controllers/API/queries/licenses";
import {
  useAssignLicense,
  useUnassignLicense,
  useUpgradeLicense,
  useGetMyTenantPools,
  useListLicenseTiers,
} from "@/controllers/API/queries/licensing";
import useAlertStore from "@/stores/alertStore";
import { useGetTenantUsageSummary } from "@/controllers/API/queries/billing";
import useAuthStore from "@/stores/authStore";
import PageLayout from "@/components/common/pageLayout";
import TenantUsageAnalytics from "./components/TenantUsageAnalytics";
import { cn } from "@/utils/utils";

const TIER_GRADIENTS = [
  "from-blue-500/20 to-blue-600/10 border-blue-500/20",
  "from-purple-500/20 to-purple-600/10 border-purple-500/20",
  "from-amber-500/20 to-amber-600/10 border-amber-500/20",
  "from-emerald-500/20 to-emerald-600/10 border-emerald-500/20",
  "from-rose-500/20 to-rose-600/10 border-rose-500/20",
];

export default function TenantAdminPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const navigate = useNavigate();
  const { isSuperAdmin, isTenantAdmin, tenantId: userTenantId } = useAuthStore();
  
  // Use the route tenant ID or fall back to user's tenant
  const activeTenantId = tenantId || userTenantId;
  
  const [isAddUserDialogOpen, setIsAddUserDialogOpen] = useState(false);
  const [isAssignDialogOpen, setIsAssignDialogOpen] = useState(false);
  const [isUpgradeDialogOpen, setIsUpgradeDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [selectedTier, setSelectedTier] = useState<string>("");
  const [preserveCredits, setPreserveCredits] = useState(true);
  
  // Add User form state
  const [newUserData, setNewUserData] = useState({
    username: "",
    password: "",
    is_tenant_admin: false,
    license_tier_id: "" as string | undefined,
  });
  
  const [activeTab, setActiveTab] = useState("overview");
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  // Queries
  const { data: tenant, isLoading: tenantLoading } = useGetTenant(activeTenantId || "");
  const { data: users, isLoading: usersLoading, refetch: refetchUsers } = useGetTenantUsers(activeTenantId || "");
  const { data: userCount, refetch: refetchUserCount } = useGetTenantUserCount(activeTenantId || "");
  const { data: license, isLoading: licenseLoading } = useGetActiveLicense(activeTenantId || "");
  const { data: usageSummary } = useGetTenantUsageSummary(activeTenantId || "");
  
  // License data
  const canAccessLicenseData = isTenantAdmin || isSuperAdmin;
  const { data: pools, refetch: refetchPools } = useGetMyTenantPools({ enabled: canAccessLicenseData });
  const { data: tiers } = useListLicenseTiers({ enabled: canAccessLicenseData });

  // Mutations
  const updateTenant = useUpdateTenant();
  const updateLicense = useUpdateLicense();
  const createUser = useCreateTenantUser();
  const updateUser = useUpdateTenantUser();
  const deleteUser = useDeleteTenantUser();
  
  const assignLicense = useAssignLicense({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License assigned successfully"] });
      setIsAssignDialogOpen(false);
      setSelectedUser(null);
      setSelectedTier("");
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to assign license"],
      });
    },
  });

  const unassignLicense = useUnassignLicense({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License unassigned successfully"] });
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to unassign license"],
      });
    },
  });

  const upgradeLicense = useUpgradeLicense({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License updated successfully"] });
      setIsUpgradeDialogOpen(false);
      setSelectedUser(null);
      setSelectedTier("");
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to update license"],
      });
    },
  });

  const handleCreateUser = async () => {
    if (!activeTenantId || !newUserData.username || !newUserData.password) return;
    
    try {
      await createUser.mutateAsync({
        tenantId: activeTenantId,
        data: {
          username: newUserData.username,
          password: newUserData.password,
          is_tenant_admin: newUserData.is_tenant_admin,
          license_tier_id: newUserData.license_tier_id || undefined,
        },
      });
      setSuccessData({ 
        title: "User created successfully",
        list: newUserData.license_tier_id ? ["License has been assigned to the user"] : [],
      });
      setIsAddUserDialogOpen(false);
      setNewUserData({ username: "", password: "", is_tenant_admin: false, license_tier_id: "" });
      refetchUsers();
      refetchUserCount();
      if (newUserData.license_tier_id) {
        refetchPools();
      }
    } catch (error: any) {
      setErrorData({ 
        title: "Failed to create user", 
        list: [error?.response?.data?.detail || "An error occurred"],
      });
    }
  };

  const handleToggleUserActive = async (user: any) => {
    if (!activeTenantId) return;
    try {
      await updateUser.mutateAsync({
        tenantId: activeTenantId,
        userId: user.id,
        data: { is_active: !user.is_active },
      });
      setSuccessData({ title: `User ${user.is_active ? 'deactivated' : 'activated'}` });
      refetchUsers();
    } catch (error: any) {
      setErrorData({ 
        title: "Failed to update user", 
        list: [error?.response?.data?.detail || "An error occurred"],
      });
    }
  };

  const handleToggleAdmin = async (user: any) => {
    if (!activeTenantId) return;
    try {
      await updateUser.mutateAsync({
        tenantId: activeTenantId,
        userId: user.id,
        data: { is_tenant_admin: !user.is_tenant_admin },
      });
      setSuccessData({ title: `User ${user.username} admin status changed` });
      refetchUsers();
    } catch (error: any) {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to update user"] });
    }
  };

  const handleDeleteUser = async (user: any) => {
    if (!activeTenantId) return;
    if (!window.confirm(`Delete user "${user.username}"? This action cannot be undone.`)) return;
    try {
      await deleteUser.mutateAsync({ tenantId: activeTenantId, userId: user.id });
      setSuccessData({ title: "User Deleted", list: [`User ${user.username} has been deleted`] });
      refetchUsers();
      refetchUserCount();
      if (user.license_is_active) {
        refetchPools();
      }
    } catch (error: any) {
      setErrorData({ title: "Error", list: [error?.response?.data?.detail || "Failed to delete user"] });
    }
  };

  const handleAssignLicense = () => {
    if (!selectedUser || !selectedTier) {
      setErrorData({ title: "Error", list: ["Please select both user and tier"] });
      return;
    }
    assignLicense.mutate({ user_id: selectedUser.id, tier_id: selectedTier });
  };

  const handleUnassignLicense = (user: any) => {
    if (window.confirm(`Remove license from "${user.username}"? They will lose access to licensed features.`)) {
      unassignLicense.mutate(user.id);
    }
  };

  const handleUpgradeLicense = () => {
    if (!selectedUser || !selectedTier) {
      setErrorData({ title: "Error", list: ["Please select both user and tier"] });
      return;
    }
    upgradeLicense.mutate({
      user_id: selectedUser.id,
      new_tier_id: selectedTier,
      preserve_credits: preserveCredits,
    });
  };

  const getTierName = (tierId?: string) => {
    if (!tierId) return "No License";
    return tiers?.find((t) => t.id === tierId)?.name || tierId;
  };

  const getTierInfo = (tierId?: string) => {
    if (!tierId) return null;
    return tiers?.find((t) => t.id === tierId);
  };

  const getAvailableCount = (tierId: string) => {
    return pools?.[tierId]?.available_count || 0;
  };

  const getCreditsPercentage = (user: any) => {
    if (!user.credits_allocated || user.credits_allocated === 0) return 0;
    return Math.round(((user.credits_allocated - user.credits_used) / user.credits_allocated) * 100);
  };

  const getGradient = (index: number) => {
    return TIER_GRADIENTS[index % TIER_GRADIENTS.length];
  };

  if (!activeTenantId) {
    return (
      <PageLayout title="Tenant Admin" description="No tenant selected">
        <Card>
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No tenant selected or you don't belong to a tenant.</p>
            {isSuperAdmin && (
              <Button className="mt-4" onClick={() => navigate("/super-admin")}>
                Go to Super Admin
              </Button>
            )}
          </CardContent>
        </Card>
      </PageLayout>
    );
  }

  const filteredUsers = users?.filter(
    (user: any) => user.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const usersWithoutLicense = users?.filter((u: any) => !u.license_is_active) || [];
  
  const poolEntries = pools ? Object.entries(pools) : [];
  const totalLicenses = poolEntries.reduce((acc, [, pool]) => acc + pool.total_count, 0);
  const assignedLicenses = poolEntries.reduce((acc, [, pool]) => acc + pool.assigned_count, 0);
  const availableLicenses = poolEntries.reduce((acc, [, pool]) => acc + pool.available_count, 0);

  const userUsagePercent = userCount && tenant 
    ? Math.round((userCount.user_count / tenant.max_users) * 100) 
    : 0;

  return (
    <PageLayout
      title={tenant?.name || "Tenant Admin"}
      description="Manage your organization's users and settings"
    >
      {/* Back button for super admins viewing other tenants */}
      {isSuperAdmin && tenantId && (
        <Button variant="outline" className="mb-4" onClick={() => navigate("/super-admin")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to All Tenants
        </Button>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 lg:w-[500px]">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Users Card */}
            <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Users</CardTitle>
                <div className="h-8 w-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Users className="h-4 w-4 text-blue-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">
                  {userCount?.user_count ?? 0}
                </div>
                <Progress value={userUsagePercent} className="mt-2 h-1.5" />
                <p className="text-xs text-muted-foreground mt-1">
                  {userUsagePercent}% of {tenant?.max_users ?? 0} capacity
                </p>
              </CardContent>
            </Card>

            {/* License Status Card */}
            <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Licensed Users</CardTitle>
                <div className="h-8 w-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <CreditCard className="h-4 w-4 text-purple-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">
                  {assignedLicenses} / {totalLicenses}
                </div>
                <Badge 
                  variant={availableLicenses > 0 ? "default" : "secondary"} 
                  className="mt-2"
                >
                  {availableLicenses} available
                </Badge>
              </CardContent>
            </Card>

            {/* Executions Card */}
            <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Executions</CardTitle>
                <div className="h-8 w-8 rounded-full bg-green-500/20 flex items-center justify-center">
                  <BarChart3 className="h-4 w-4 text-green-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">
                  {usageSummary?.total_flow_runs ?? 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Last 30 days
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Usage Summary - Credits focused for Tenant Admins */}
          <Card>
            <CardHeader>
              <CardTitle>Credits Usage</CardTitle>
              <CardDescription>Your organization's credit consumption (last 30 days)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100/50 dark:from-blue-950/50 dark:to-blue-900/30 rounded-lg border border-blue-200/50 dark:border-blue-800/50">
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{usageSummary?.total_credits_used ?? 0}</p>
                  <p className="text-sm text-muted-foreground">Credits Used</p>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100/50 dark:from-green-950/50 dark:to-green-900/30 rounded-lg border border-green-200/50 dark:border-green-800/50">
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">{usageSummary?.total_flow_runs ?? 0}</p>
                  <p className="text-sm text-muted-foreground">Flow Runs</p>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100/50 dark:from-purple-950/50 dark:to-purple-900/30 rounded-lg border border-purple-200/50 dark:border-purple-800/50">
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {((usageSummary?.total_tokens ?? 0) / 1000).toFixed(1)}K
                  </p>
                  <p className="text-sm text-muted-foreground">Tokens</p>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-amber-50 to-amber-100/50 dark:from-amber-950/50 dark:to-amber-900/30 rounded-lg border border-amber-200/50 dark:border-amber-800/50">
                  <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{usageSummary?.active_users_count ?? 0}</p>
                  <p className="text-sm text-muted-foreground">Active Users</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Links */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="cursor-pointer hover:border-primary/50 transition-colors" onClick={() => setActiveTab("usage")}>
              <CardContent className="pt-6 flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                  <BarChart3 className="h-6 w-6 text-cyan-600" />
                </div>
                <div>
                  <p className="font-medium">View Detailed Analytics</p>
                  <p className="text-sm text-muted-foreground">See usage breakdown by user and flow</p>
                </div>
              </CardContent>
            </Card>
            <Card className="cursor-pointer hover:border-primary/50 transition-colors" onClick={() => setActiveTab("users")}>
              <CardContent className="pt-6 flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
                  <Users className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="font-medium">Manage Users & Licenses</p>
                  <p className="text-sm text-muted-foreground">Add users and assign licenses</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Usage Tab - Shows credits, NOT USD */}
        <TabsContent value="usage" className="space-y-4">
          <TenantUsageAnalytics tenantId={activeTenantId} />
        </TabsContent>

        {/* Users Tab - Combined with License Management */}
        <TabsContent value="users" className="space-y-6">
          {/* License Pool Summary Stats */}
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

          {/* License Pools */}
          {poolEntries.length > 0 && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div>
                  <CardTitle className="text-base">License Pools</CardTitle>
                  <CardDescription>Available license pools for your organization</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={() => refetchPools()}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </CardHeader>
              <CardContent>
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
                              className={cn(!isEmpty && !isLow && "bg-green-500")}
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
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* User Management Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-primary" />
                    User Management
                  </CardTitle>
                  <CardDescription>
                    {userCount?.user_count ?? 0} of {tenant?.max_users ?? 0} users • Add, manage, and assign licenses to users
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  {usersWithoutLicense.length > 0 && (
                    <Button 
                      variant="outline"
                      onClick={() => setIsAssignDialogOpen(true)}
                    >
                      <CreditCard className="h-4 w-4 mr-2" />
                      Assign License
                    </Button>
                  )}
                  <Dialog open={isAddUserDialogOpen} onOpenChange={setIsAddUserDialogOpen}>
                    <DialogTrigger asChild>
                      <Button disabled={(userCount?.user_count ?? 0) >= (tenant?.max_users ?? 0)}>
                        <Plus className="h-4 w-4 mr-2" />
                        Add User
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                      <DialogHeader>
                        <DialogTitle>Add New User</DialogTitle>
                        <DialogDescription>
                          Create a new user for {tenant?.name}. Optionally assign a license.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                          <Label htmlFor="username">Username *</Label>
                          <Input
                            id="username"
                            value={newUserData.username}
                            onChange={(e) => setNewUserData({ ...newUserData, username: e.target.value })}
                            placeholder="johndoe"
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor="password">Password *</Label>
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
                            <p className="text-xs text-muted-foreground">
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
                                        <Badge variant={available > 0 ? "secondary" : "destructive"} className="ml-2 text-xs">
                                          {available} available
                                        </Badge>
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
                        {newUserData.license_tier_id && (
                          <div className="rounded-lg border p-4 bg-muted/50 space-y-2">
                            <h4 className="font-medium text-sm">Selected Tier Benefits</h4>
                            <div className="space-y-1 text-sm">
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Initial Credits</span>
                                <span className="font-medium">
                                  {getTierInfo(newUserData.license_tier_id)?.default_credits?.toLocaleString()}
                                </span>
                              </div>
                              {getTierInfo(newUserData.license_tier_id)?.default_credits_per_month && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Monthly Credits</span>
                                  <span className="font-medium">
                                    +{getTierInfo(newUserData.license_tier_id)?.default_credits_per_month?.toLocaleString()}/mo
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setIsAddUserDialogOpen(false)}>
                          Cancel
                        </Button>
                        <Button 
                          onClick={handleCreateUser}
                          disabled={createUser.isPending || !newUserData.username || !newUserData.password}
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
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Search */}
              <div className="relative max-w-md mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>

              {/* User Limit Warning */}
              {(userCount?.user_count ?? 0) >= (tenant?.max_users ?? 0) && (
                <div className="mb-4 p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-600" />
                  <p className="text-sm">
                    You've reached your user limit. Upgrade your license to add more users.
                  </p>
                </div>
              )}

              {/* Users Table */}
              {usersLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : filteredUsers?.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    {searchQuery ? "No users match your search" : "No users found. Add your first user!"}
                  </p>
                </div>
              ) : (
                <div className="rounded-lg border overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-muted/50">
                        <TableHead className="w-[250px]">User</TableHead>
                        <TableHead>License Tier</TableHead>
                        <TableHead>Credits</TableHead>
                        <TableHead>Status</TableHead>
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
                                user.license_is_active 
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
                                      Admin
                                    </Badge>
                                  )}
                                  {user.is_platform_superadmin && (
                                    <Badge variant="default" className="text-xs py-0 px-1">
                                      Super Admin
                                    </Badge>
                                  )}
                                  <Badge variant={user.is_active ? "outline" : "secondary"} className="text-xs py-0 px-1">
                                    {user.is_active ? "Active" : "Inactive"}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            {user.license_is_active ? (
                              <div className="flex items-center gap-2">
                                <Sparkles className="h-4 w-4 text-amber-500" />
                                <span className="font-medium">{getTierName(user.license_tier_id)}</span>
                              </div>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {user.license_is_active ? (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <div className="w-[140px]">
                                      <div className="flex items-center justify-between text-xs mb-1">
                                        <span className="font-medium">
                                          {(user.credits_allocated - user.credits_used).toLocaleString()}
                                        </span>
                                        <span className="text-muted-foreground">
                                          / {user.credits_allocated.toLocaleString()}
                                        </span>
                                      </div>
                                      <Progress 
                                        value={getCreditsPercentage(user)} 
                                        className={cn(
                                          "h-2",
                                          getCreditsPercentage(user) < 20 && "[&>div]:bg-amber-500",
                                          getCreditsPercentage(user) < 10 && "[&>div]:bg-destructive"
                                        )}
                                      />
                                    </div>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <div className="space-y-1">
                                      <p>{getCreditsPercentage(user)}% remaining</p>
                                      {user.credits_per_month && (
                                        <p className="text-xs text-muted-foreground">
                                          +{user.credits_per_month.toLocaleString()}/month
                                        </p>
                                      )}
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge variant={user.license_is_active ? "default" : "secondary"}>
                              {user.license_is_active ? "Licensed" : "Unlicensed"}
                            </Badge>
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
                                      setIsAssignDialogOpen(true);
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
                                        setSelectedTier("");
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
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Organization Settings</CardTitle>
              <CardDescription>Manage your organization's configuration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {tenantLoading ? (
                <p className="text-muted-foreground">Loading...</p>
              ) : tenant ? (
                <>
                  <div className="grid gap-2">
                    <Label>Organization Name</Label>
                    <Input value={tenant.name} disabled />
                  </div>
                  <div className="grid gap-2">
                    <Label>Slug</Label>
                    <Input value={tenant.slug} disabled />
                  </div>
                  <div className="grid gap-2">
                    <Label>Description</Label>
                    <Input value={tenant.description || ""} disabled />
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div>
                      <Label>Organization Status</Label>
                      <p className="text-sm text-muted-foreground">
                        {tenant.is_active ? "Active and accepting new users" : "Inactive"}
                      </p>
                    </div>
                    <Badge variant={tenant.is_active ? "default" : "secondary"}>
                      {tenant.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  {isSuperAdmin && (
                    <Button variant="outline" className="w-full">
                      <Settings className="h-4 w-4 mr-2" />
                      Edit Organization Settings
                    </Button>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground">Unable to load organization settings.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Assign License Dialog */}
      <Dialog open={isAssignDialogOpen} onOpenChange={setIsAssignDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Assign License</DialogTitle>
            <DialogDescription>
              {selectedUser 
                ? `Assign a license to ${selectedUser.username}`
                : "Select a user and license tier to assign"
              }
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {!selectedUser && (
              <div className="grid gap-2">
                <Label>User *</Label>
                <Select 
                  value={selectedUser?.id || ""} 
                  onValueChange={(value) => setSelectedUser(usersWithoutLicense.find((u: any) => u.id === value))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a user" />
                  </SelectTrigger>
                  <SelectContent>
                    {usersWithoutLicense.map((user: any) => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="grid gap-2">
              <Label>License Tier *</Label>
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
                        <div className="flex items-center justify-between w-full gap-2">
                          <span>{tier.name}</span>
                          <Badge 
                            variant={available > 0 ? "secondary" : "destructive"}
                            className="text-xs"
                          >
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
              <div className="rounded-lg border p-4 bg-muted/50 space-y-2">
                <h4 className="font-medium text-sm">Tier Benefits</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Initial Credits</span>
                    <span className="font-medium">
                      {getTierInfo(selectedTier)?.default_credits?.toLocaleString()}
                    </span>
                  </div>
                  {getTierInfo(selectedTier)?.default_credits_per_month && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Monthly Credits</span>
                      <span className="font-medium">
                        +{getTierInfo(selectedTier)?.default_credits_per_month?.toLocaleString()}/mo
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsAssignDialogOpen(false);
              setSelectedUser(null);
              setSelectedTier("");
            }}>
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
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Change License Tier</DialogTitle>
            <DialogDescription>
              Update {selectedUser?.username}'s license tier
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {selectedUser && (
              <div className="rounded-lg border p-4 bg-blue-500/5 border-blue-500/20">
                <h4 className="font-medium text-blue-600 mb-2">Current License</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tier</span>
                    <span className="font-medium">{getTierName(selectedUser.license_tier_id)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Credits Remaining</span>
                    <span className="font-medium">
                      {(selectedUser.credits_allocated - selectedUser.credits_used).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div className="grid gap-2">
              <Label>New License Tier *</Label>
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
                        <div className="flex items-center justify-between w-full gap-2">
                          <span>{tier.name}</span>
                          <Badge 
                            variant={available > 0 ? "secondary" : "destructive"}
                            className="text-xs"
                          >
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
                <p className="text-xs text-muted-foreground">
                  Add remaining credits to the new tier's allocation
                </p>
              </div>
              <Switch
                id="preserve-credits"
                checked={preserveCredits}
                onCheckedChange={setPreserveCredits}
              />
            </div>
            {selectedTier && (
              <div className="rounded-lg border p-4 bg-green-500/5 border-green-500/20">
                <h4 className="font-medium text-green-600 mb-2">New License</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">New Tier</span>
                    <span className="font-medium">{getTierInfo(selectedTier)?.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">New Credits</span>
                    <span className="font-medium">
                      {preserveCredits && selectedUser
                        ? `${selectedUser.credits_allocated - selectedUser.credits_used} + ${getTierInfo(selectedTier)?.default_credits}`
                        : getTierInfo(selectedTier)?.default_credits?.toLocaleString()
                      }
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsUpgradeDialogOpen(false);
              setSelectedUser(null);
              setSelectedTier("");
            }}>
              Cancel
            </Button>
            <Button 
              onClick={handleUpgradeLicense}
              disabled={!selectedTier || upgradeLicense.isPending}
            >
              {upgradeLicense.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                "Update License"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PageLayout>
  );
}
