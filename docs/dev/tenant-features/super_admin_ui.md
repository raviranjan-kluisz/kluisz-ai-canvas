# Super Admin Feature Management UI

## 1. Overview

The Super Admin UI provides comprehensive control over tenant features through:

1. **License Tier Feature Builder** - Define what features each tier includes
2. **Tier Management** - View and edit features for any license tier
3. **Tenant Assignment** - Assign tenants to tiers to control their features
4. **Feature Registry Browser** - View and manage all available features

---

## 2. UI Components

### 2.1 License Tier Feature Builder

**Location:** `src/frontend/src/pages/SuperAdminPage/components/TierFeatureBuilder/`

```
┌─────────────────────────────────────────────────────────────────────────┐
│ License Tier: Enterprise                                          Save │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ ┌─ Models ──────────────────────────────────────────────────────────┐  │
│ │                                                                    │  │
│ │  ☑ OpenAI                    ☑ Anthropic                          │  │
│ │    ☑ GPT-4                     ☑ Claude 3 Opus                    │  │
│ │    ☑ GPT-4 Turbo               ☑ Claude 3 Sonnet                  │  │
│ │    ☑ GPT-4o                    ☑ Claude 3 Haiku                   │  │
│ │    ☑ GPT-4o Mini               ☑ Claude 3.5 Sonnet                │  │
│ │    ☑ GPT-3.5 Turbo                                                │  │
│ │    ☑ O1 Preview              ☑ Google                             │  │
│ │    ☑ O1 Mini                   ☑ Gemini Pro                       │  │
│ │                                ☑ Gemini 1.5 Pro                   │  │
│ │  ☑ Mistral                     ☑ Gemini 1.5 Flash                 │  │
│ │    ☑ Mistral Large                                                │  │
│ │    ☑ Mistral Medium          ☑ Ollama (Local Models)              │  │
│ │    ☑ Mistral Small           ☑ Azure OpenAI                       │  │
│ │                              ☐ AWS Bedrock                        │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│ ┌─ Components ──────────────────────────────────────────────────────┐  │
│ │                                                                    │  │
│ │  Categories                    Custom Components                   │  │
│ │  ☑ Models & Agents            ☑ Create Custom                     │  │
│ │  ☑ Helpers                    ☑ Edit Component Code               │  │
│ │  ☑ Data I/O                   ☐ Import External                   │  │
│ │  ☑ Logic                                                          │  │
│ │  ☑ Embeddings                                                     │  │
│ │  ☑ Memories                                                       │  │
│ │  ☑ Tools                                                          │  │
│ │  ☑ Prototypes (Beta)                                              │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│ ┌─ Integrations ────────────────────────────────────────────────────┐  │
│ │                                                                    │  │
│ │  Observability                 Vector Stores                       │  │
│ │  ☑ MCP Server                  ☑ Chroma                           │  │
│ │  ☑ Langfuse                    ☑ Pinecone                         │  │
│ │  ☐ LangSmith                   ☑ Qdrant                           │  │
│ │  ☐ LangWatch                   ☐ Weaviate                         │  │
│ │                                ☐ Milvus                           │  │
│ │  Databases                                                        │  │
│ │  ☑ PostgreSQL                  ☐ AirTable                         │  │
│ │  ☑ MongoDB                     ☐ Notion                           │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│ ┌─ UI Features ─────────────────────────────────────────────────────┐  │
│ │                                                                    │  │
│ │  Flow Builder                  Advanced                            │  │
│ │  ☑ Export Flow                 ☑ Global Variables                 │  │
│ │  ☑ Import Flow                 ☑ API Keys Management              │  │
│ │  ☑ Share Flow                  ☑ MCP Server Config                │  │
│ │  ☑ Version Control                                                │  │
│ │                                Debug                               │  │
│ │  Code View                     ☑ Debug Mode                       │  │
│ │  ☑ View Code                   ☑ Step Execution                   │  │
│ │  ☑ Edit Code                   ☑ Logs Access                      │  │
│ │  ☑ Python API                                                     │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│ ┌─ API & Limits ────────────────────────────────────────────────────┐  │
│ │                                                                    │  │
│ │  API Features                  Resource Limits                     │  │
│ │  ☑ Public Endpoints            Max Flows: [unlimited ▼]           │  │
│ │  ☑ Webhooks                    Max API Calls/Month: [unlimited ▼] │  │
│ │  ☑ Streaming Responses         Max Concurrent Exec: [10 ▼]        │  │
│ │  ☑ Batch Execution             Max Tokens/Request: [unlimited ▼]  │  │
│ │                                Max File Upload: [100 MB ▼]        │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│                                              [Cancel]  [Save Changes]   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Tenant Tier Assignment (Removed - Features controlled via tier assignment)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Tenant: Acme Corp                                    Tier: Professional │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Feature Overrides                                      [+ Add Override] │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Feature             │ Tier Default │ Override │ Expires │ Actions   │ │
│ ├─────────────────────┼──────────────┼──────────┼─────────┼───────────┤ │
│ │ models.anthropic    │ ✓ Enabled    │ ✗ Disabled│ —      │ [Remove]  │ │
│ │ ui.debug_mode       │ ✗ Disabled   │ ✓ Enabled │ 30 days│ [Remove]  │ │
│ │ api.batch_execution │ ✗ Disabled   │ ✓ Enabled │ —      │ [Remove]  │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ Pending Upgrade Requests                                                │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Feature             │ Requested    │ Notes        │ Actions         │ │
│ ├─────────────────────┼──────────────┼──────────────┼─────────────────┤ │
│ │ models.aws_bedrock  │ 2 days ago   │ Need for AWS │ [Approve][Deny] │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ All Features (Resolved)                              [Show inherited]   │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                         │
│ ▼ Models                                                                │
│   ☑ OpenAI (Tier)          ☑ Google (Tier)         ✗ AWS Bedrock       │
│   ✗ Anthropic (Override)   ☑ Mistral (Tier)        ☑ Ollama (Tier)     │
│                                                                         │
│ ▼ Integrations                                                          │
│   ☑ MCP (Tier)             ☑ Langfuse (Tier)       ✗ LangSmith         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Add Override Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│ Add Feature Override                                      [X]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Feature                                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Search features...                                      [▼] │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Override Type                                                   │
│ ○ Enable (grant access beyond tier)                             │
│ ● Disable (restrict from tier default)                          │
│                                                                 │
│ Expiration                                                      │
│ ○ Permanent                                                     │
│ ● Temporary    Until: [2024-03-01    ] (30 days)               │
│                                                                 │
│ Reason (optional)                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Customer requested trial of Anthropic models               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│                              [Cancel]  [Add Override]           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Implementation

### 3.1 TierFeatureBuilder Component

```typescript
// src/frontend/src/pages/SuperAdminPage/components/TierFeatureBuilder/index.tsx

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { useFeatureRegistry, useTierFeatures, useSetTierFeatures } from "@/controllers/API/queries/features";
import { Loader2, Save, Check } from "lucide-react";

interface TierFeatureBuilderProps {
  tierId: string;
  tierName: string;
  onSave?: () => void;
}

export function TierFeatureBuilder({ tierId, tierName, onSave }: TierFeatureBuilderProps) {
  const { data: registry, isLoading: registryLoading } = useFeatureRegistry();
  const { data: tierFeatures, isLoading: featuresLoading } = useTierFeatures(tierId);
  const setTierFeatures = useSetTierFeatures();
  
  const [features, setFeatures] = useState<Record<string, any>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize features from tier
  useEffect(() => {
    if (tierFeatures) {
      setFeatures(tierFeatures.features);
    }
  }, [tierFeatures]);

  const handleFeatureToggle = (featureKey: string, enabled: boolean) => {
    setFeatures(prev => ({
      ...prev,
      [featureKey]: { enabled },
    }));
    setHasChanges(true);
  };

  const handleLimitChange = (featureKey: string, value: number | null) => {
    setFeatures(prev => ({
      ...prev,
      [featureKey]: { enabled: true, value },
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    await setTierFeatures.mutateAsync({
      tierId,
      features,
    });
    setHasChanges(false);
    onSave?.();
  };

  if (registryLoading || featuresLoading) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Group features by category
  const featuresByCategory = registry?.reduce((acc, feature) => {
    if (!acc[feature.category]) acc[feature.category] = [];
    acc[feature.category].push(feature);
    return acc;
  }, {} as Record<string, typeof registry>) ?? {};

  const categoryConfig = {
    models: { title: "Models", icon: "🤖" },
    components: { title: "Components", icon: "🧩" },
    integrations: { title: "Integrations", icon: "🔌" },
    ui: { title: "UI Features", icon: "🎨" },
    api: { title: "API & Limits", icon: "⚡" },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">License Tier: {tierName}</h2>
          <p className="text-muted-foreground">Configure features included in this tier</p>
        </div>
        <Button 
          onClick={handleSave} 
          disabled={!hasChanges || setTierFeatures.isPending}
        >
          {setTierFeatures.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : hasChanges ? (
            <Save className="h-4 w-4 mr-2" />
          ) : (
            <Check className="h-4 w-4 mr-2" />
          )}
          {hasChanges ? "Save Changes" : "Saved"}
        </Button>
      </div>

      <Accordion type="multiple" defaultValue={Object.keys(categoryConfig)}>
        {Object.entries(categoryConfig).map(([category, config]) => (
          <AccordionItem key={category} value={category}>
            <AccordionTrigger className="text-lg font-semibold">
              <span className="flex items-center gap-2">
                <span>{config.icon}</span>
                <span>{config.title}</span>
              </span>
            </AccordionTrigger>
            <AccordionContent>
              <Card>
                <CardContent className="pt-6">
                  <FeatureCategoryGrid
                    features={featuresByCategory[category] || []}
                    values={features}
                    onToggle={handleFeatureToggle}
                    onLimitChange={handleLimitChange}
                  />
                </CardContent>
              </Card>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}

function FeatureCategoryGrid({
  features,
  values,
  onToggle,
  onLimitChange,
}: {
  features: any[];
  values: Record<string, any>;
  onToggle: (key: string, enabled: boolean) => void;
  onLimitChange: (key: string, value: number | null) => void;
}) {
  // Group by subcategory
  const bySubcategory = features.reduce((acc, f) => {
    const sub = f.subcategory || "general";
    if (!acc[sub]) acc[sub] = [];
    acc[sub].push(f);
    return acc;
  }, {} as Record<string, typeof features>);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Object.entries(bySubcategory).map(([subcategory, subFeatures]) => (
        <div key={subcategory} className="space-y-3">
          <h4 className="font-medium capitalize text-sm text-muted-foreground">
            {subcategory.replace(/_/g, " ")}
          </h4>
          <div className="space-y-2">
            {subFeatures.map(feature => {
              const value = values[feature.feature_key];
              const isEnabled = value?.enabled ?? feature.default_value?.enabled ?? false;

              if (feature.feature_type === "boolean") {
                return (
                  <div key={feature.feature_key} className="flex items-center justify-between">
                    <label className="text-sm">{feature.feature_name}</label>
                    <Switch
                      checked={isEnabled}
                      onCheckedChange={(checked) => onToggle(feature.feature_key, checked)}
                    />
                  </div>
                );
              }

              if (feature.feature_type === "integer") {
                return (
                  <div key={feature.feature_key} className="flex items-center justify-between">
                    <label className="text-sm">{feature.feature_name}</label>
                    <Select
                      value={value?.value?.toString() ?? "unlimited"}
                      onValueChange={(v) => onLimitChange(
                        feature.feature_key, 
                        v === "unlimited" ? null : parseInt(v)
                      )}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unlimited">Unlimited</SelectItem>
                        <SelectItem value="1">1</SelectItem>
                        <SelectItem value="5">5</SelectItem>
                        <SelectItem value="10">10</SelectItem>
                        <SelectItem value="25">25</SelectItem>
                        <SelectItem value="50">50</SelectItem>
                        <SelectItem value="100">100</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                );
              }

              return null;
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
```

### 3.2 Tenant Features View (Read-Only)

Tenants inherit features from their assigned license tier. To change a tenant's features, assign them to a different tier via the tenant management interface.

```typescript
// Note: No separate component needed - features are controlled via tier assignment

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  useTenantFeatures, 
  useSetTenantOverride, 
  useRemoveTenantOverride,
  useApproveUpgrade,
  useRejectUpgrade,
} from "@/controllers/API/queries/features";
import { Plus, Trash2, Check, X } from "lucide-react";
import { AddOverrideDialog } from "./AddOverrideDialog";

interface TenantFeatureOverridesProps {
  tenantId: string;
  tenantName: string;
}

export function TenantFeatureOverrides({ tenantId, tenantName }: TenantFeatureOverridesProps) {
  const { data: tenantFeatures, isLoading } = useTenantFeatures(tenantId);
  const removeTenantOverride = useRemoveTenantOverride();
  const approveUpgrade = useApproveUpgrade();
  const rejectUpgrade = useRejectUpgrade();
  
  const [addDialogOpen, setAddDialogOpen] = useState(false);

  // Extract overrides (features with source === "tenant_override")
  const overrides = Object.entries(tenantFeatures?.features ?? {})
    .filter(([_, value]) => value.source === "tenant_override")
    .map(([key, value]) => ({ key, ...value }));

  const handleRemoveOverride = async (featureKey: string) => {
    await removeTenantOverride.mutateAsync({ tenantId, featureKey });
  };

  const handleApprove = async (featureKey: string) => {
    await approveUpgrade.mutateAsync({ tenantId, featureKey });
  };

  const handleReject = async (featureKey: string, reason?: string) => {
    await rejectUpgrade.mutateAsync({ tenantId, featureKey, reason });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{tenantName}</h2>
          <p className="text-muted-foreground">
            Tier: <Badge variant="secondary">{tenantFeatures?.tier_name ?? "No tier"}</Badge>
          </p>
        </div>
        <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Override
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Feature Override</DialogTitle>
            </DialogHeader>
            <AddOverrideDialog
              tenantId={tenantId}
              onSuccess={() => setAddDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Current Overrides */}
      <Card>
        <CardHeader>
          <CardTitle>Feature Overrides</CardTitle>
        </CardHeader>
        <CardContent>
          {overrides.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">
              No overrides configured. Using tier defaults.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Feature</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Expires</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {overrides.map(override => (
                  <TableRow key={override.key}>
                    <TableCell className="font-mono text-sm">{override.key}</TableCell>
                    <TableCell>
                      <Badge variant={override.enabled ? "default" : "destructive"}>
                        {override.enabled ? "Enabled" : "Disabled"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {override.expires_at 
                        ? new Date(override.expires_at).toLocaleDateString()
                        : "—"
                      }
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveOverride(override.key)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* All Features View */}
      <Card>
        <CardHeader>
          <CardTitle>All Features (Resolved)</CardTitle>
        </CardHeader>
        <CardContent>
          <AllFeaturesView features={tenantFeatures?.features ?? {}} />
        </CardContent>
      </Card>
    </div>
  );
}

function AllFeaturesView({ features }: { features: Record<string, any> }) {
  // Group by category (extracted from feature key)
  const byCategory = Object.entries(features).reduce((acc, [key, value]) => {
    const category = key.split(".")[0];
    if (!acc[category]) acc[category] = [];
    acc[category].push({ key, ...value });
    return acc;
  }, {} as Record<string, any[]>);

  return (
    <div className="space-y-4">
      {Object.entries(byCategory).map(([category, categoryFeatures]) => (
        <div key={category}>
          <h4 className="font-semibold capitalize mb-2">{category}</h4>
          <div className="flex flex-wrap gap-2">
            {categoryFeatures.map(f => (
              <Badge
                key={f.key}
                variant={f.enabled ? "default" : "secondary"}
                className="text-xs"
              >
                {f.enabled ? "✓" : "✗"} {f.key.replace(`${category}.`, "")}
                {f.source === "tenant_override" && (
                  <span className="ml-1 text-amber-500">*</span>
                )}
              </Badge>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## 4. Integration with Super Admin Page

Add a new tab to the existing SuperAdminPage:

```typescript
// In src/frontend/src/pages/SuperAdminPage/index.tsx

import { TierFeatureBuilder } from "./components/TierFeatureBuilder";

// Add to tabs
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="tenants">Tenants</TabsTrigger>
    <TabsTrigger value="tiers">License Tiers</TabsTrigger>
    <TabsTrigger value="features">Features</TabsTrigger>  {/* NEW */}
    <TabsTrigger value="analytics">Analytics</TabsTrigger>
  </TabsList>

  {/* ... existing tabs ... */}

  <TabsContent value="features">
    <FeaturesManagementTab />
  </TabsContent>
</Tabs>

function FeaturesManagementTab() {
  const [selectedTier, setSelectedTier] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left sidebar: Tier selector */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Select Tier</CardTitle>
          </CardHeader>
          <CardContent>
            <TierSelector value={selectedTier} onChange={setSelectedTier} />
          </CardContent>
        </Card>

        {/* Main content */}
        <div className="lg:col-span-3">
          {selectedTier ? (
            <TierFeatureBuilder tierId={selectedTier} tierName="..." />
          ) : (
            <Card>
              <CardContent className="py-10 text-center text-muted-foreground">
                Select a license tier to configure its features.
                Tenants inherit features from their assigned tier.
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## 5. Tenant Admin View (Read-Only)

Tenant admins can view their features but cannot modify them:

```typescript
// src/frontend/src/pages/TenantAdminPage/components/TenantFeatures.tsx

import { useFeatureFlags } from "@/contexts/featureContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageSquare } from "lucide-react";

export function TenantFeaturesView() {
  const { features, tierName, isLoading } = useFeatureFlags();

  if (isLoading) return <div>Loading...</div>;

  const byCategory = groupByCategory(features);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Available Features</h2>
          <p className="text-muted-foreground">
            Your plan: <Badge>{tierName}</Badge>
          </p>
        </div>
      </div>

      {Object.entries(byCategory).map(([category, categoryFeatures]) => (
        <Card key={category}>
          <CardHeader>
            <CardTitle className="capitalize">{category}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {categoryFeatures.map(f => (
                <Badge
                  key={f.key}
                  variant={f.enabled ? "default" : "outline"}
                >
                  {f.enabled ? "✓" : "✗"} {f.name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```




