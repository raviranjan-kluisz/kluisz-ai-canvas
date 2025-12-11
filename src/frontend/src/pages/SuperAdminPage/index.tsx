// SuperAdminPage - Platform-level administration for managing all tenants

import { useState, useEffect } from "react";
import { 
  Building2, 
  Plus, 
  Users, 
  CreditCard, 
  BarChart3, 
  AlertCircle, 
  Check, 
  X, 
  Trash2, 
  ChevronRight,
  Layers,
  TrendingUp,
  Activity,
  Shield,
  Search,
  ArrowLeft,
  Settings,
  ShieldAlert,
  Sliders
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useGetTenants, useCreateTenant, useUpdateTenant, useDeleteTenant, type Tenant, type TenantCreate } from "@/controllers/API/queries/tenants";
import { useListLicenseTiers } from "@/controllers/API/queries/licensing";
import { useGetAnalyticsOverview } from "@/controllers/API/queries/billing";
import PageLayout from "@/components/common/pageLayout";
import LicenseTierManagement from "./components/LicenseTierManagement";
import TenantPoolManagement from "./components/TenantPoolManagement";
import TenantUserManagement from "./components/TenantUserManagement";
import UsageAnalytics from "./components/UsageAnalytics";
import TierFeatureBuilder from "./components/TierFeatureBuilder";
import useAuthStore from "@/stores/authStore";
import useAlertStore from "@/stores/alertStore";
import { cn } from "@/utils/utils";

export default function SuperAdminPage() {
  const { isSuperAdmin, userData } = useAuthStore();
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [managingTenant, setManagingTenant] = useState<Tenant | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const [newTenant, setNewTenant] = useState<TenantCreate>({
    name: "",
    slug: "",
    max_users: 10,
    description: "",
    is_active: true,
  });

  // Queries - only fetch when user is a super admin
  const { data: tenants, isLoading: tenantsLoading, refetch: refetchTenants } = useGetTenants();
  const { data: tiers } = useListLicenseTiers({ enabled: isSuperAdmin });
  const { data: overview, isLoading: overviewLoading } = useGetAnalyticsOverview({ enabled: isSuperAdmin });

  // Mutations
  const createTenant = useCreateTenant();
  const updateTenant = useUpdateTenant();
  const deleteTenant = useDeleteTenant();

  const handleCreateTenant = async () => {
    try {
      const createdTenant = await createTenant.mutateAsync(newTenant);
      setIsCreateDialogOpen(false);
      setNewTenant({ name: "", slug: "", max_users: 10, description: "", is_active: true });
      // Refetch tenants list to show the new tenant immediately
      await refetchTenants();
      setSuccessData({ 
        title: "Tenant Created", 
        list: [`Tenant "${createdTenant.name}" has been created successfully. You can now assign license pools to it.`] 
      });
      // Switch to tenants tab to show the new tenant
      setActiveTab("tenants");
    } catch (error: any) {
      setErrorData({ 
        title: "Failed to Create Tenant", 
        list: [error?.response?.data?.detail || "An error occurred while creating the tenant"] 
      });
    }
  };

  const handleToggleTenantActive = async (tenant: Tenant, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await updateTenant.mutateAsync({
        id: tenant.id,
        data: { is_active: !tenant.is_active },
      });
    } catch (error) {
      console.error("Failed to update tenant:", error);
    }
  };

  const handleDeleteTenant = async () => {
    if (!selectedTenant) return;
    try {
      await deleteTenant.mutateAsync(selectedTenant.id);
      setIsDeleteDialogOpen(false);
      setSelectedTenant(null);
    } catch (error) {
      console.error("Failed to delete tenant:", error);
    }
  };

  const generateSlug = (name: string) => {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  };

  const filteredTenants = tenants?.filter(
    (tenant) => 
      tenant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tenant.slug.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Show access denied if not a super admin
  if (!isSuperAdmin) {
    return (
      <PageLayout
        title="Super Admin"
        description="Platform-level administration"
      >
        <Alert variant="destructive" className="mb-6">
          <ShieldAlert className="h-5 w-5" />
          <AlertTitle>Access Denied</AlertTitle>
          <AlertDescription className="mt-2">
            <p>You don't have super admin privileges to access this page.</p>
            <p className="mt-2 text-sm">
              To access the Super Admin dashboard, you need to be logged in as a user with 
              <code className="mx-1 px-1.5 py-0.5 rounded bg-destructive/20">is_platform_superadmin = true</code>.
            </p>
            {userData && (
              <p className="mt-2 text-sm">
                Current user: <strong>{userData.username}</strong> 
                {userData.is_platform_superadmin ? " (Super Admin)" : " (Not a Super Admin)"}
              </p>
            )}
            <div className="mt-4 p-3 rounded-lg bg-background/50 border">
              <p className="font-medium text-sm">How to get Super Admin access:</p>
              <ul className="mt-2 text-sm space-y-1 list-disc list-inside">
                <li>If <code className="px-1 py-0.5 rounded bg-muted">AUTO_LOGIN=true</code>, log in with username: <strong>admin</strong>, password: <strong>admin</strong></li>
                <li>Or ask an existing Super Admin to grant you access</li>
                <li>Or use the CLI: <code className="px-1 py-0.5 rounded bg-muted">kluisz superadmin</code></li>
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      </PageLayout>
    );
  }

  // If managing a specific tenant, show the user management view
  if (managingTenant) {
    return (
      <PageLayout
        title={managingTenant.name}
        description="Manage users, licenses, and settings for this tenant"
      >
        <Button 
          variant="outline" 
          className="mb-6" 
          onClick={() => setManagingTenant(null)}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to All Tenants
        </Button>

        <div className="space-y-6">
          {/* Tenant Info Header */}
          <Card className="bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 rounded-xl bg-primary/20 flex items-center justify-center">
                    <Building2 className="h-8 w-8 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-2xl font-bold">{managingTenant.name}</h2>
                      <Badge variant={managingTenant.is_active ? "default" : "secondary"}>
                        {managingTenant.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground">@{managingTenant.slug}</p>
                    {managingTenant.description && (
                      <p className="text-sm text-muted-foreground mt-1">{managingTenant.description}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tenant User Management */}
          <TenantUserManagement tenant={managingTenant} />
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title="Super Admin"
      description="Platform-level administration for managing all tenants, licenses, and users"
    >
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6 lg:w-[720px] mb-6">
          <TabsTrigger value="overview" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="usage" className="gap-2">
            <Activity className="h-4 w-4" />
            Usage
          </TabsTrigger>
          <TabsTrigger value="tenants" className="gap-2">
            <Building2 className="h-4 w-4" />
            Tenants
          </TabsTrigger>
          <TabsTrigger value="license-tiers" className="gap-2">
            <Layers className="h-4 w-4" />
            Tiers
          </TabsTrigger>
          <TabsTrigger value="license-pools" className="gap-2">
            <CreditCard className="h-4 w-4" />
            Pools
          </TabsTrigger>
          <TabsTrigger value="features" className="gap-2">
            <Sliders className="h-4 w-4" />
            Features
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Stats Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Tenants</CardTitle>
                <div className="h-8 w-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Building2 className="h-4 w-4 text-blue-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">
                  {overviewLoading ? "..." : overview?.total_tenants ?? tenants?.length ?? 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {overview?.active_tenants ?? tenants?.filter(t => t.is_active).length ?? 0} active
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
                <div className="h-8 w-8 rounded-full bg-green-500/20 flex items-center justify-center">
                  <Users className="h-4 w-4 text-green-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">
                  {overviewLoading ? "..." : overview?.total_users ?? 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Across all tenants
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">License Tiers</CardTitle>
                <div className="h-8 w-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <Layers className="h-4 w-4 text-purple-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-purple-600">
                  {tiers?.length ?? 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {tiers?.filter(t => t.is_active).length ?? 0} active tiers
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Platform Health</CardTitle>
                <div className="h-8 w-8 rounded-full bg-amber-500/20 flex items-center justify-center">
                  <Activity className="h-4 w-4 text-amber-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">Healthy</div>
                <p className="text-xs text-muted-foreground mt-1">
                  All systems operational
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions & Recent Activity */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Quick Actions
                </CardTitle>
                <CardDescription>Common administrative tasks</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                <Button 
                  variant="outline" 
                  className="justify-start h-auto py-3"
                  onClick={() => setActiveTab("usage")}
                >
                  <div className="h-8 w-8 rounded-lg bg-cyan-500/10 flex items-center justify-center mr-3">
                    <Activity className="h-4 w-4 text-cyan-600" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">View Usage Analytics</p>
                    <p className="text-xs text-muted-foreground">Monitor costs, tokens, and credits</p>
                  </div>
                </Button>
                <Button 
                  variant="outline" 
                  className="justify-start h-auto py-3"
                  onClick={() => setActiveTab("license-tiers")}
                >
                  <div className="h-8 w-8 rounded-lg bg-purple-500/10 flex items-center justify-center mr-3">
                    <Layers className="h-4 w-4 text-purple-600" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Manage License Tiers</p>
                    <p className="text-xs text-muted-foreground">Configure pricing and limits</p>
                  </div>
                </Button>
                <Button 
                  variant="outline" 
                  className="justify-start h-auto py-3"
                  onClick={() => setActiveTab("license-pools")}
                >
                  <div className="h-8 w-8 rounded-lg bg-green-500/10 flex items-center justify-center mr-3">
                    <CreditCard className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">Allocate Licenses</p>
                    <p className="text-xs text-muted-foreground">Assign license pools to tenants</p>
                  </div>
                </Button>
                <Button 
                  variant="outline" 
                  className="justify-start h-auto py-3"
                  onClick={() => setActiveTab("tenants")}
                >
                  <div className="h-8 w-8 rounded-lg bg-orange-500/10 flex items-center justify-center mr-3">
                    <Users className="h-4 w-4 text-orange-600" />
                  </div>
                  <div className="text-left">
                    <p className="font-medium">View All Tenants</p>
                    <p className="text-xs text-muted-foreground">Browse and manage tenants</p>
                  </div>
                </Button>
              </CardContent>
            </Card>

            {/* Recent Tenants */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-primary" />
                  Recent Tenants
                </CardTitle>
                <CardDescription>Latest tenant organizations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {tenantsLoading ? (
                    <p className="text-muted-foreground text-sm">Loading...</p>
                  ) : tenants?.slice(0, 5).map((tenant) => (
                    <div 
                      key={tenant.id} 
                      className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                      onClick={() => setManagingTenant(tenant)}
                    >
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "h-9 w-9 rounded-lg flex items-center justify-center",
                          tenant.is_active ? "bg-primary/10" : "bg-muted"
                        )}>
                          <Building2 className={cn(
                            "h-4 w-4",
                            tenant.is_active ? "text-primary" : "text-muted-foreground"
                          )} />
                        </div>
                        <div>
                          <p className="font-medium text-sm">{tenant.name}</p>
                          <p className="text-xs text-muted-foreground">@{tenant.slug}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={tenant.is_active ? "default" : "secondary"} className="text-xs">
                          {tenant.is_active ? "Active" : "Inactive"}
                        </Badge>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                  ))}
                  {tenants?.length === 0 && (
                    <div className="text-center py-6">
                      <Building2 className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                      <p className="text-sm text-muted-foreground">No tenants yet</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Usage Analytics Tab */}
        <TabsContent value="usage" className="space-y-6">
          <UsageAnalytics />
        </TabsContent>

        {/* Tenants Tab */}
        <TabsContent value="tenants" className="space-y-6">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tenants..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Tenant
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Create New Tenant</DialogTitle>
                  <DialogDescription>
                    Create a new tenant organization. You can assign license pools after creation.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Organization Name</Label>
                    <Input
                      id="name"
                      value={newTenant.name}
                      onChange={(e) => {
                        const name = e.target.value;
                        setNewTenant({
                          ...newTenant,
                          name,
                          slug: generateSlug(name),
                        });
                      }}
                      placeholder="Acme Corp"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="slug">Slug (URL-friendly)</Label>
                    <Input
                      id="slug"
                      value={newTenant.slug}
                      onChange={(e) => setNewTenant({ ...newTenant, slug: e.target.value })}
                      placeholder="acme-corp"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={newTenant.description}
                      onChange={(e) => setNewTenant({ ...newTenant, description: e.target.value })}
                      placeholder="Organization description..."
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="max_users">Max Users</Label>
                    <Input
                      id="max_users"
                      type="number"
                      value={newTenant.max_users}
                      onChange={(e) => setNewTenant({ ...newTenant, max_users: parseInt(e.target.value) || 10 })}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateTenant} disabled={createTenant.isPending || !newTenant.name}>
                    {createTenant.isPending ? "Creating..." : "Create Tenant"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Tenants Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {tenantsLoading ? (
              <Card className="col-span-full">
                <CardContent className="py-8 text-center">
                  <p className="text-muted-foreground">Loading tenants...</p>
                </CardContent>
              </Card>
            ) : filteredTenants?.length === 0 ? (
              <Card className="col-span-full">
                <CardContent className="py-8 text-center">
                  <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    {searchQuery ? "No tenants match your search" : "No tenants yet. Create your first tenant!"}
                  </p>
                </CardContent>
              </Card>
            ) : (
              filteredTenants?.map((tenant) => (
                <Card 
                  key={tenant.id} 
                  className="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50 group overflow-hidden"
                  onClick={() => setManagingTenant(tenant)}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "h-12 w-12 rounded-xl flex items-center justify-center transition-colors",
                          tenant.is_active 
                            ? "bg-primary/10 group-hover:bg-primary/20" 
                            : "bg-muted"
                        )}>
                          <Building2 className={cn(
                            "h-6 w-6",
                            tenant.is_active ? "text-primary" : "text-muted-foreground"
                          )} />
                        </div>
                        <div>
                          <CardTitle className="text-lg group-hover:text-primary transition-colors">
                            {tenant.name}
                          </CardTitle>
                          <p className="text-sm text-muted-foreground">@{tenant.slug}</p>
                        </div>
                      </div>
                      <Badge variant={tenant.is_active ? "default" : "secondary"}>
                        {tenant.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {tenant.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                        {tenant.description}
                      </p>
                    )}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Users className="h-4 w-4" />
                          Max {tenant.max_users}
                        </span>
                        {tenant.license_pools && Object.keys(tenant.license_pools).length > 0 && (
                          <span className="flex items-center gap-1 text-primary">
                            <CreditCard className="h-4 w-4" />
                            {Object.keys(tenant.license_pools).length} pool(s)
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTenant(tenant);
                            setActiveTab("license-pools");
                            // Scroll to pools section after a brief delay
                            setTimeout(() => {
                              const poolsSection = document.querySelector('[value="license-pools"]');
                              poolsSection?.scrollIntoView({ behavior: "smooth", block: "start" });
                            }, 100);
                          }}
                          title="Manage License Pools"
                          className="h-8 text-xs"
                        >
                          <CreditCard className="h-3.5 w-3.5 mr-1" />
                          Pools
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => handleToggleTenantActive(tenant, e)}
                          title={tenant.is_active ? "Deactivate" : "Activate"}
                          className="h-8 w-8"
                        >
                          {tenant.is_active ? <X className="h-4 w-4" /> : <Check className="h-4 w-4" />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTenant(tenant);
                            setIsDeleteDialogOpen(true);
                          }}
                          title="Delete"
                          className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t flex items-center justify-between">
                      <span className="text-xs text-muted-foreground flex items-center gap-1 group-hover:text-primary transition-colors">
                        Click to manage users & licenses
                        <ChevronRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* Delete Confirmation Dialog */}
          <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete Tenant</DialogTitle>
                <DialogDescription>
                  Are you sure you want to delete "{selectedTenant?.name}"? This action cannot be undone and will delete all tenant data including users, flows, and files.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={handleDeleteTenant} disabled={deleteTenant.isPending}>
                  {deleteTenant.isPending ? "Deleting..." : "Delete Tenant"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        {/* License Tiers Tab */}
        <TabsContent value="license-tiers" className="space-y-4">
          <LicenseTierManagement />
        </TabsContent>

        {/* License Pools Tab */}
        <TabsContent value="license-pools" className="space-y-4">
          <TenantPoolManagement initialTenantId={selectedTenant?.id} />
        </TabsContent>

        {/* Features Tab */}
        <TabsContent value="features" className="space-y-6">
          <FeaturesManagementTab tiers={tiers} />
        </TabsContent>
      </Tabs>
    </PageLayout>
  );
}

// Features Management Tab Component
function FeaturesManagementTab({ tiers }: { tiers?: Array<{ id: string; name: string; is_active: boolean }> }) {
  const activeTiers = tiers?.filter(t => t.is_active) ?? [];
  const [selectedTierId, setSelectedTierId] = useState<string | null>(
    activeTiers.length > 0 ? activeTiers[0].id : null
  );

  // Update selection when tiers change
  useEffect(() => {
    if (activeTiers.length > 0 && !selectedTierId) {
      setSelectedTierId(activeTiers[0].id);
    }
  }, [activeTiers, selectedTierId]);

  const selectedTier = activeTiers.find(t => t.id === selectedTierId);

  if (activeTiers.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-16 text-center">
          <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center">
            <Layers className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium mb-2">No License Tiers Found</h3>
          <p className="text-muted-foreground max-w-md mx-auto">
            Create a license tier first to configure its features. 
            Features determine what models, components, and capabilities users can access.
          </p>
          <Button 
            className="mt-6" 
            onClick={() => {
              // Navigate to tiers tab
              const tiersTab = document.querySelector('[value="license-tiers"]') as HTMLButtonElement;
              tiersTab?.click();
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Create License Tier
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Feature Builder with tier selector passed in */}
      <TierFeatureBuilder 
        key={selectedTierId}
        tierId={selectedTierId || activeTiers[0].id} 
        tierName={selectedTier?.name || activeTiers[0].name}
        tiers={activeTiers}
        onTierChange={setSelectedTierId}
      />
    </div>
  );
}
