import { useState, useEffect } from "react";
import { 
  Plus, 
  Edit, 
  Trash2, 
  Sparkles,
  Coins,
  Users,
  Layers,
  Zap,
  MoreVertical,
  Power,
  PowerOff,
  Copy,
  Loader2,
  AlertCircle,
  CheckCircle
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
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  useListLicenseTiers,
  useCreateLicenseTier,
  useUpdateLicenseTier,
  useDeleteLicenseTier,
  type LicenseTier,
  type LicenseTierCreate,
} from "@/controllers/API/queries/licensing";
import {
  useFeatureRegistry,
  FEATURE_CATEGORIES,
  type Feature,
} from "@/controllers/API/queries/features";
import useAlertStore from "@/stores/alertStore";
import useAuthStore from "@/stores/authStore";
import { cn } from "@/utils/utils";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

const TIER_COLORS = [
  { bg: "from-slate-500/20 to-slate-600/10", border: "border-slate-500/30", text: "text-slate-600", badge: "bg-slate-500" },
  { bg: "from-blue-500/20 to-blue-600/10", border: "border-blue-500/30", text: "text-blue-600", badge: "bg-blue-500" },
  { bg: "from-purple-500/20 to-purple-600/10", border: "border-purple-500/30", text: "text-purple-600", badge: "bg-purple-500" },
  { bg: "from-amber-500/20 to-amber-600/10", border: "border-amber-500/30", text: "text-amber-600", badge: "bg-amber-500" },
  { bg: "from-emerald-500/20 to-emerald-600/10", border: "border-emerald-500/30", text: "text-emerald-600", badge: "bg-emerald-500" },
  { bg: "from-rose-500/20 to-rose-600/10", border: "border-rose-500/30", text: "text-rose-600", badge: "bg-rose-500" },
];

const DEFAULT_FORM_DATA: LicenseTierCreate = {
  name: "",
  description: "",
  token_price_per_1000: 0.002,
  credits_per_usd: 100,
  pricing_multiplier: 1.0,
  default_credits: 1000,
  default_credits_per_month: undefined,
  max_users: undefined,
  max_flows: undefined,
  max_api_calls: undefined,
  features: {},
  is_active: true,
};

export default function LicenseTierManagement() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [editingTier, setEditingTier] = useState<LicenseTier | null>(null);
  const [tierToDelete, setTierToDelete] = useState<LicenseTier | null>(null);
  const [formData, setFormData] = useState<LicenseTierCreate>(DEFAULT_FORM_DATA);

  const { isSuperAdmin } = useAuthStore();
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  // Only fetch tiers if user is a super admin
  const { data: tiers, isLoading, refetch } = useListLicenseTiers({ enabled: isSuperAdmin });
  
  const createTier = useCreateLicenseTier({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License tier created successfully"] });
      handleCloseDialog();
      refetch();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to create license tier"],
      });
    },
  });

  const updateTier = useUpdateLicenseTier({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License tier updated successfully"] });
      handleCloseDialog();
      refetch();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to update license tier"],
      });
    },
  });

  const deleteTier = useDeleteLicenseTier({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License tier deleted successfully"] });
      setIsDeleteDialogOpen(false);
      setTierToDelete(null);
      refetch();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to delete license tier"],
      });
    },
  });

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setEditingTier(null);
    setFormData(DEFAULT_FORM_DATA);
  };

  const handleEdit = (tier: LicenseTier) => {
    setEditingTier(tier);
    setFormData({
      name: tier.name,
      description: tier.description || "",
      token_price_per_1000: tier.token_price_per_1000,
      credits_per_usd: tier.credits_per_usd,
      pricing_multiplier: tier.pricing_multiplier,
      default_credits: tier.default_credits,
      default_credits_per_month: tier.default_credits_per_month,
      max_users: tier.max_users,
      max_flows: tier.max_flows,
      max_api_calls: tier.max_api_calls,
      features: tier.features,
      is_active: tier.is_active,
    });
    setIsDialogOpen(true);
  };

  const handleDuplicate = (tier: LicenseTier) => {
    setEditingTier(null);
    setFormData({
      name: `${tier.name} (Copy)`,
      description: tier.description || "",
      token_price_per_1000: tier.token_price_per_1000,
      credits_per_usd: tier.credits_per_usd,
      pricing_multiplier: tier.pricing_multiplier,
      default_credits: tier.default_credits,
      default_credits_per_month: tier.default_credits_per_month,
      max_users: tier.max_users,
      max_flows: tier.max_flows,
      max_api_calls: tier.max_api_calls,
      features: tier.features,
      is_active: false,
    });
    setIsDialogOpen(true);
  };

  const handleToggleActive = (tier: LicenseTier) => {
    updateTier.mutate({
      tierId: tier.id,
      data: { is_active: !tier.is_active },
    });
  };

  const handleSubmit = () => {
    if (editingTier) {
      updateTier.mutate({ tierId: editingTier.id, data: formData });
    } else {
      createTier.mutate(formData);
    }
  };

  const handleDelete = () => {
    if (tierToDelete) {
      deleteTier.mutate(tierToDelete.id);
    }
  };

  const getTierColor = (index: number) => {
    return TIER_COLORS[index % TIER_COLORS.length];
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">License Tiers</h2>
          <p className="text-muted-foreground">
            Create and manage license tiers with custom pricing, credits, and limits
          </p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Create Tier
        </Button>
      </div>

      {/* Tier Cards */}
      {tiers?.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Layers className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold">No License Tiers</h3>
            <p className="text-muted-foreground max-w-sm mt-1">
              Create your first license tier to start managing licenses for your tenants.
            </p>
            <Button onClick={() => setIsDialogOpen(true)} className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              Create First Tier
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {tiers?.map((tier, index) => {
            const colors = getTierColor(index);
            return (
              <Card 
                key={tier.id} 
                className={cn(
                  "relative overflow-hidden transition-all hover:shadow-lg",
                  `bg-gradient-to-br ${colors.bg} ${colors.border}`,
                  !tier.is_active && "opacity-60"
                )}
              >
                {/* Status Indicator */}
                <div className="absolute top-4 right-4">
                  <Badge 
                    variant={tier.is_active ? "default" : "secondary"}
                    className={cn(
                      "gap-1",
                      tier.is_active && colors.badge
                    )}
                  >
                    {tier.is_active ? (
                      <>
                        <CheckCircle className="h-3 w-3" />
                        Active
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-3 w-3" />
                        Inactive
                      </>
                    )}
                  </Badge>
                </div>

                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className={cn(
                        "h-10 w-10 rounded-lg flex items-center justify-center mb-3",
                        colors.badge
                      )}>
                        <Sparkles className="h-5 w-5 text-white" />
                      </div>
                      <CardTitle className={cn("text-xl", colors.text)}>{tier.name}</CardTitle>
                      {tier.description && (
                        <CardDescription className="mt-1 line-clamp-2">
                          {tier.description}
                        </CardDescription>
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Credits Info */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-background/60 backdrop-blur">
                      <p className="text-xs text-muted-foreground">Default Credits</p>
                      <p className="text-lg font-bold">{tier.default_credits.toLocaleString()}</p>
                    </div>
                    {tier.default_credits_per_month && (
                      <div className="p-3 rounded-lg bg-background/60 backdrop-blur">
                        <p className="text-xs text-muted-foreground">Monthly Credits</p>
                        <p className="text-lg font-bold">{tier.default_credits_per_month.toLocaleString()}</p>
                      </div>
                    )}
                  </div>

                  {/* Pricing Info */}
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <Coins className="h-4 w-4 text-amber-500" />
                      <span>{tier.credits_per_usd} credits/$</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Zap className="h-4 w-4 text-muted-foreground" />
                      <span>{tier.pricing_multiplier}x multiplier</span>
                    </div>
                  </div>

                  {/* Limits */}
                  {(tier.max_users || tier.max_flows || tier.max_api_calls) && (
                    <div className="flex flex-wrap gap-2 text-xs">
                      {tier.max_users && (
                        <Badge variant="outline" className="gap-1">
                          <Users className="h-3 w-3" />
                          {tier.max_users} users
                        </Badge>
                      )}
                      {tier.max_flows && (
                        <Badge variant="outline" className="gap-1">
                          <Layers className="h-3 w-3" />
                          {tier.max_flows} flows
                        </Badge>
                      )}
                      {tier.max_api_calls && (
                        <Badge variant="outline" className="gap-1">
                          <Zap className="h-3 w-3" />
                          {tier.max_api_calls.toLocaleString()} API calls
                        </Badge>
                      )}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-2">
                    <Button variant="outline" size="sm" onClick={() => handleEdit(tier)}>
                      <Edit className="h-3.5 w-3.5 mr-1" />
                      Edit
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleDuplicate(tier)}>
                          <Copy className="h-4 w-4 mr-2" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleToggleActive(tier)}>
                          {tier.is_active ? (
                            <>
                              <PowerOff className="h-4 w-4 mr-2" />
                              Deactivate
                            </>
                          ) : (
                            <>
                              <Power className="h-4 w-4 mr-2" />
                              Activate
                            </>
                          )}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => {
                            setTierToDelete(tier);
                            setIsDeleteDialogOpen(true);
                          }}
                          className="text-destructive focus:text-destructive"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={(open) => !open && handleCloseDialog()}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingTier ? "Edit License Tier" : "Create License Tier"}
            </DialogTitle>
            <DialogDescription>
              {editingTier 
                ? "Update the tier configuration below"
                : "Configure a new license tier with pricing, credits, and limits"
              }
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="basic" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="basic">Basic Info</TabsTrigger>
              <TabsTrigger value="pricing">Pricing & Credits</TabsTrigger>
              <TabsTrigger value="limits">Limits</TabsTrigger>
              <TabsTrigger value="features">Features</TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="space-y-4 mt-4">
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Tier Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Professional, Enterprise, Starter"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Describe this tier's target audience and key features..."
                    rows={3}
                  />
                </div>
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <Label>Active Status</Label>
                    <p className="text-sm text-muted-foreground">
                      Active tiers can be assigned to users
                    </p>
                  </div>
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                  />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="pricing" className="space-y-4 mt-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="grid gap-2">
                  <Label htmlFor="default_credits">Default Credits *</Label>
                  <Input
                    id="default_credits"
                    type="number"
                    min="0"
                    value={formData.default_credits}
                    onChange={(e) => setFormData({ ...formData, default_credits: parseInt(e.target.value) || 0 })}
                  />
                  <p className="text-xs text-muted-foreground">Initial credits when license is assigned</p>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="monthly_credits">Monthly Credits</Label>
                  <Input
                    id="monthly_credits"
                    type="number"
                    min="0"
                    value={formData.default_credits_per_month || ""}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      default_credits_per_month: e.target.value ? parseInt(e.target.value) : undefined 
                    })}
                    placeholder="Leave empty for one-time"
                  />
                  <p className="text-xs text-muted-foreground">Recurring credits per month (for subscriptions)</p>
                </div>
              </div>

              <Separator />

              <div className="grid gap-4 md:grid-cols-3">
                <div className="grid gap-2">
                  <Label htmlFor="credits_per_usd">Credits per USD</Label>
                  <Input
                    id="credits_per_usd"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.credits_per_usd}
                    onChange={(e) => setFormData({ ...formData, credits_per_usd: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="token_price">Token Price per 1K</Label>
                  <Input
                    id="token_price"
                    type="number"
                    step="0.0001"
                    min="0"
                    value={formData.token_price_per_1000}
                    onChange={(e) => setFormData({ ...formData, token_price_per_1000: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="multiplier">Pricing Multiplier</Label>
                  <Input
                    id="multiplier"
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.pricing_multiplier}
                    onChange={(e) => setFormData({ ...formData, pricing_multiplier: parseFloat(e.target.value) || 1 })}
                  />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="limits" className="space-y-4 mt-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="grid gap-2">
                  <Label htmlFor="max_users">Max Users</Label>
                  <Input
                    id="max_users"
                    type="number"
                    min="0"
                    value={formData.max_users || ""}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      max_users: e.target.value ? parseInt(e.target.value) : undefined 
                    })}
                    placeholder="Unlimited"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="max_flows">Max Flows</Label>
                  <Input
                    id="max_flows"
                    type="number"
                    min="0"
                    value={formData.max_flows || ""}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      max_flows: e.target.value ? parseInt(e.target.value) : undefined 
                    })}
                    placeholder="Unlimited"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="max_api_calls">Max API Calls</Label>
                  <Input
                    id="max_api_calls"
                    type="number"
                    min="0"
                    value={formData.max_api_calls || ""}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      max_api_calls: e.target.value ? parseInt(e.target.value) : undefined 
                    })}
                    placeholder="Unlimited"
                  />
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                Leave fields empty for unlimited. These limits help manage resource usage per license.
              </p>
            </TabsContent>

            <TabsContent value="features" className="space-y-4 mt-4">
              <FeatureSelectionTab
                features={formData.features}
                onFeaturesChange={(features) => setFormData({ ...formData, features })}
              />
            </TabsContent>
          </Tabs>

          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={handleCloseDialog}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit}
              disabled={!formData.name || createTier.isPending || updateTier.isPending}
            >
              {(createTier.isPending || updateTier.isPending) ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {editingTier ? "Updating..." : "Creating..."}
                </>
              ) : (
                editingTier ? "Update Tier" : "Create Tier"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete License Tier</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{tierToDelete?.name}"? This action cannot be undone.
              {tierToDelete && (
                <span className="block mt-2 text-destructive">
                  Warning: This will fail if any pools or users are using this tier.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDelete}
              disabled={deleteTier.isPending}
            >
              {deleteTier.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete Tier"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Feature Selection Component
function FeatureSelectionTab({
  features,
  onFeaturesChange,
}: {
  features: Record<string, unknown>;
  onFeaturesChange: (features: Record<string, unknown>) => void;
}) {
  const { data: registry, isLoading } = useFeatureRegistry();
  const [initialized, setInitialized] = useState(false);

  // Initialize all features from registry when component mounts
  // This ensures ALL features are saved, not just explicitly toggled ones
  useEffect(() => {
    if (registry && !initialized) {
      const hasExistingFeatures = Object.keys(features).length > 0;
      
      // Only auto-initialize if features is empty (new tier)
      if (!hasExistingFeatures) {
        const initialFeatures: Record<string, unknown> = {};
        for (const feature of registry) {
          // Start with all features DISABLED for new tiers (restrictive default)
          initialFeatures[feature.feature_key] = { enabled: false };
        }
        onFeaturesChange(initialFeatures);
      }
      setInitialized(true);
    }
  }, [registry, features, onFeaturesChange, initialized]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Group features by category
  const featuresByCategory =
    registry?.reduce(
      (acc, feature) => {
        if (!acc[feature.category]) acc[feature.category] = [];
        acc[feature.category].push(feature);
        return acc;
      },
      {} as Record<string, Feature[]>
    ) ?? {};

  const handleFeatureToggle = (featureKey: string, enabled: boolean) => {
    const currentFeature = features[featureKey] as Record<string, unknown> | undefined;
    onFeaturesChange({
      ...features,
      [featureKey]: {
        ...currentFeature,
        enabled,
      },
    });
  };

  const handleValueChange = (featureKey: string, value: number | null) => {
    onFeaturesChange({
      ...features,
      [featureKey]: {
        enabled: true,
        value,
      },
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm text-muted-foreground mb-4">
          Select which features are enabled for this license tier. Users assigned to this tier will have access to these features.
        </p>
      </div>

      <Accordion type="multiple" defaultValue={Object.keys(FEATURE_CATEGORIES)}>
        {Object.entries(FEATURE_CATEGORIES).map(([category, config]) => {
          const categoryFeatures = featuresByCategory[category] || [];
          if (categoryFeatures.length === 0) return null;

          return (
            <AccordionItem key={category} value={category}>
              <AccordionTrigger className="text-lg font-semibold">
                <span className="flex items-center gap-2">
                  <span>{config.icon}</span>
                  <span>{config.title}</span>
                  <span className="text-sm text-muted-foreground font-normal">
                    ({categoryFeatures.length})
                  </span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <Card>
                  <CardContent className="pt-6">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {categoryFeatures.map((feature) => {
                        const featureValue = features[feature.feature_key] as Record<string, unknown> | undefined;
                        const isEnabled =
                          featureValue?.enabled ??
                          (feature.default_value as Record<string, unknown>)?.enabled ??
                          false;

                        if (feature.feature_type === "boolean") {
                          return (
                            <div
                              key={feature.feature_key}
                              className="flex items-center justify-between p-3 rounded-lg border"
                            >
                              <div className="flex-1">
                                <label className="text-sm font-medium">{feature.feature_name}</label>
                                {feature.description && (
                                  <p className="text-xs text-muted-foreground mt-1">
                                    {feature.description}
                                  </p>
                                )}
                              </div>
                              <Switch
                                checked={isEnabled as boolean}
                                onCheckedChange={(checked) =>
                                  handleFeatureToggle(feature.feature_key, checked)
                                }
                              />
                            </div>
                          );
                        }

                        if (feature.feature_type === "integer") {
                          return (
                            <div
                              key={feature.feature_key}
                              className="p-3 rounded-lg border space-y-2"
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <label className="text-sm font-medium">{feature.feature_name}</label>
                                  {feature.description && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                      {feature.description}
                                    </p>
                                  )}
                                </div>
                                <Switch
                                  checked={isEnabled as boolean}
                                  onCheckedChange={(checked) => {
                                    handleFeatureToggle(feature.feature_key, checked);
                                    if (!checked) {
                                      handleValueChange(feature.feature_key, null);
                                    }
                                  }}
                                />
                              </div>
                              {isEnabled && (
                                <div className="pt-2">
                                  <label className="text-xs text-muted-foreground">Limit</label>
                                  <input
                                    type="number"
                                    min="0"
                                    value={(featureValue?.value as number) || ""}
                                    onChange={(e) =>
                                      handleValueChange(
                                        feature.feature_key,
                                        e.target.value ? parseInt(e.target.value) : null
                                      )
                                    }
                                    placeholder="Unlimited"
                                    className="w-full mt-1 px-2 py-1 text-sm border rounded"
                                  />
                                </div>
                              )}
                            </div>
                          );
                        }

                        return null;
                      })}
                    </div>
                  </CardContent>
                </Card>
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>
    </div>
  );
}
