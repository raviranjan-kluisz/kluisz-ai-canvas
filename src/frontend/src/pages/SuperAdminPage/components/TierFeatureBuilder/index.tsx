import { useEffect, useState, useMemo } from "react";
import {
  Check,
  ChevronDown,
  ChevronRight,
  Loader2,
  Save,
  Search,
  ToggleLeft,
  ToggleRight,
  Sparkles,
  X,
  Layers,
  Bot,
  Puzzle,
  Plug,
  Palette,
  Zap,
  Filter,
  CircleCheck,
  Circle,
  Cloud,
  Database,
  Eye,
  MessageSquare,
  Code,
  Settings,
  Share2,
  FlaskConical,
  LayoutTemplate,
  Store,
  Key,
  Webhook,
  Globe,
  Lock,
  Cpu,
  Brain,
  Sparkle,
  Box,
  FileCode,
  Gauge,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  FEATURE_CATEGORIES,
  TIER_BUILDER_CATEGORIES,
  useFeatureRegistry,
  useSetTierFeatures,
  useTierFeatures,
  type Feature,
} from "@/controllers/API/queries/features";
import { cn } from "@/utils/utils";

// Category icons mapping
const CATEGORY_ICONS = {
  models: Bot,
  components: Puzzle,
  integrations: Plug,
  ui: Palette,
  api: Zap,
} as const;

// Feature icons based on feature key patterns
const FEATURE_ICON_MAP: Record<string, typeof Bot> = {
  // Models
  "openai": Brain,
  "anthropic": Sparkle,
  "google": Cloud,
  "mistral": Cpu,
  "ollama": Box,
  "azure": Cloud,
  "aws": Cloud,
  "groq": Zap,
  "xai": Brain,
  // Components
  "agents": Bot,
  "chains": Puzzle,
  "prompts": MessageSquare,
  "tools": Settings,
  "memory": Database,
  "vectorstores": Database,
  "embeddings": Cpu,
  "llms": Brain,
  "custom": FileCode,
  // Integrations
  // NOTE: All observability (langfuse, langsmith, langwatch) is mandatory/always-on
  "chroma": Database,
  "pinecone": Database,
  "weaviate": Database,
  "qdrant": Database,
  "milvus": Database,
  "redis": Database,
  "postgres": Database,
  "supabase": Database,
  "mongodb": Database,
  "elasticsearch": Search,
  // UI
  "chat": MessageSquare,
  "playground": FlaskConical,
  "code": Code,
  "debug": Eye,
  "logs": Activity,
  "embed": Share2,
  "share": Share2,
  "templates": LayoutTemplate,
  "store": Store,
  "advanced": Settings,
  // API
  "api_access": Key,
  "webhooks": Webhook,
  "public": Globe,
};

// Get icon for a feature based on its key
function getFeatureIcon(featureKey: string): typeof Bot | null {
  const keyLower = featureKey.toLowerCase();
  for (const [pattern, icon] of Object.entries(FEATURE_ICON_MAP)) {
    if (keyLower.includes(pattern)) {
      return icon;
    }
  }
  return null;
}

// Subcategory icons
const SUBCATEGORY_ICONS: Record<string, typeof Bot> = {
  openai: Brain,
  anthropic: Sparkle,
  google: Cloud,
  mistral: Cpu,
  ollama: Box,
  azure: Cloud,
  aws: Cloud,
  groq: Zap,
  xai: Brain,
  categories: Puzzle,
  custom: FileCode,
  external: Plug,
  observability: Activity,
  vector_stores: Database,
  bundles_ai: Bot,
  bundles_cloud: Cloud,
  bundles_data: Database,
  bundles_observability: Gauge,
  bundles_services: Plug,
  bundles_specialized: Sparkles,
  flow_builder: Puzzle,
  code_view: Code,
  debug: Eye,
  advanced: Settings,
  sharing: Share2,
  chat: MessageSquare,
  testing: FlaskConical,
  templates: LayoutTemplate,
  store: Store,
  access: Key,
  general: Settings,
};

// Subcategory labels for better display
const SUBCATEGORY_LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google AI",
  mistral: "Mistral",
  ollama: "Ollama (Local)",
  azure: "Azure",
  aws: "AWS",
  ibm: "IBM",
  groq: "Groq",
  xai: "xAI",
  categories: "Component Categories",
  custom: "Custom Components",
  external: "External Services",
  observability: "Observability",
  vector_stores: "Vector Stores",
  bundles_ai: "AI Provider Bundles",
  bundles_cloud: "Cloud Provider Bundles",
  bundles_data: "Data & Vector Store Bundles",
  bundles_observability: "Observability Bundles",
  bundles_services: "External Service Bundles",
  bundles_specialized: "Specialized Bundles",
  flow_builder: "Flow Builder",
  code_view: "Code View",
  debug: "Debug & Logs",
  advanced: "Advanced Settings",
  sharing: "Sharing & Embed",
  chat: "Chat & Messages",
  testing: "Testing & Playground",
  templates: "Templates",
  store: "Store",
  access: "API Access",
  general: "General",
};

function getSubcategoryLabel(subcategory: string): string {
  return SUBCATEGORY_LABELS[subcategory] || subcategory.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
}

interface TierFeatureBuilderProps {
  tierId: string;
  tierName: string;
  tiers?: Array<{ id: string; name: string; is_active: boolean }>;
  onTierChange?: (tierId: string) => void;
  onSave?: () => void;
}

export function TierFeatureBuilder({
  tierId,
  tierName,
  tiers,
  onTierChange,
  onSave,
}: TierFeatureBuilderProps) {
  const { data: registry, isLoading: registryLoading } = useFeatureRegistry();
  const { data: tierFeatures, isLoading: featuresLoading } = useTierFeatures(tierId);
  const setTierFeatures = useSetTierFeatures();

  const [features, setFeatures] = useState<Record<string, unknown>>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("models");
  const [expandedSubcategories, setExpandedSubcategories] = useState<Set<string>>(new Set());

  // Initialize features from registry with tier overrides
  useEffect(() => {
    if (registry && tierFeatures && !initialized) {
      const initialFeatures: Record<string, unknown> = {};
      for (const feature of registry) {
        initialFeatures[feature.feature_key] = feature.default_value;
      }
      for (const [key, value] of Object.entries(tierFeatures.features)) {
        initialFeatures[key] = value;
      }
      setFeatures(initialFeatures);
      setInitialized(true);
      
      const allSubcategories = new Set(registry.map(f => `${f.category}-${f.subcategory || 'general'}`));
      setExpandedSubcategories(allSubcategories);
    }
  }, [registry, tierFeatures, initialized]);

  useEffect(() => {
    setInitialized(false);
    setHasChanges(false);
  }, [tierId]);

  const featuresByCategory = useMemo(() => {
    if (!registry) return {};
    return registry.reduce((acc, feature) => {
      if (feature.category === "limits") return acc;
      if (!acc[feature.category]) acc[feature.category] = [];
      acc[feature.category].push(feature);
      return acc;
    }, {} as Record<string, Feature[]>);
  }, [registry]);

  const filteredFeatures = useMemo(() => {
    const categoryFeatures = featuresByCategory[activeCategory] || [];
    if (!searchQuery.trim()) return categoryFeatures;
    
    const query = searchQuery.toLowerCase();
    return categoryFeatures.filter(f => 
      f.feature_name.toLowerCase().includes(query) ||
      f.feature_key.toLowerCase().includes(query) ||
      (f.description && f.description.toLowerCase().includes(query))
    );
  }, [featuresByCategory, activeCategory, searchQuery]);

  const featuresBySubcategory = useMemo(() => {
    return filteredFeatures.reduce((acc, f) => {
      const sub = f.subcategory || "general";
      if (!acc[sub]) acc[sub] = [];
      acc[sub].push(f);
      return acc;
    }, {} as Record<string, Feature[]>);
  }, [filteredFeatures]);

  const categoryStats = useMemo(() => {
    const stats: Record<string, { total: number; enabled: number }> = {};
    for (const [category, categoryFeatures] of Object.entries(featuresByCategory)) {
      const enabled = categoryFeatures.filter(f => {
        const value = features[f.feature_key] as Record<string, unknown> | undefined;
        return value?.enabled ?? (f.default_value as Record<string, unknown>)?.enabled ?? false;
      }).length;
      stats[category] = { total: categoryFeatures.length, enabled };
    }
    return stats;
  }, [featuresByCategory, features]);

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

  const handleBulkToggle = (subcategory: string, enabled: boolean) => {
    const subcategoryFeatures = featuresBySubcategory[subcategory] || [];
    const updates: Record<string, unknown> = {};
    for (const feature of subcategoryFeatures) {
      if (feature.feature_type === "boolean") {
        updates[feature.feature_key] = { enabled };
      }
    }
    setFeatures(prev => ({ ...prev, ...updates }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    await setTierFeatures.mutateAsync({ tierId, features });
    setHasChanges(false);
    onSave?.();
  };

  const toggleSubcategory = (key: string) => {
    setExpandedSubcategories(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  if (registryLoading || featuresLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const sortedSubcategories = Object.keys(featuresBySubcategory).sort((a, b) => {
    const aIsBundle = a.startsWith("bundles_");
    const bIsBundle = b.startsWith("bundles_");
    if (aIsBundle && !bIsBundle) return -1;
    if (!aIsBundle && bIsBundle) return 1;
    return a.localeCompare(b);
  });

  return (
    <div className="space-y-5">
      {/* Header with Tier Selector */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          {tiers && tiers.length > 0 && onTierChange && (
            <Select value={tierId} onValueChange={onTierChange}>
              <SelectTrigger className="w-[200px] h-10 bg-gradient-to-r from-violet-500/10 to-purple-500/5 border-violet-500/30 hover:border-violet-500/50 transition-colors">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-violet-500" />
                  <SelectValue placeholder="Select tier" />
                </div>
              </SelectTrigger>
              <SelectContent>
                {tiers.map((tier, index) => (
                  <SelectItem key={tier.id} value={tier.id}>
                    <div className="flex items-center gap-2">
                      {tier.name}
                      {index === 0 && (
                        <Badge variant="secondary" className="text-[10px] h-4 px-1.5 bg-violet-500/20 text-violet-600">
                          Default
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <p className="text-sm text-muted-foreground">Configure features for this tier</p>
        </div>
        <Button
          onClick={handleSave}
          disabled={!hasChanges || setTierFeatures.isPending}
          className={cn(
            "min-w-[130px] h-10 transition-all font-medium",
            hasChanges 
              ? "bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600 shadow-lg shadow-emerald-500/25" 
              : "bg-muted text-muted-foreground"
          )}
        >
          {setTierFeatures.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : hasChanges ? (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </>
          ) : (
            <>
              <Check className="mr-2 h-4 w-4" />
              Saved
            </>
          )}
        </Button>
      </div>

      {/* Clean Category Tabs */}
      <Card className="p-2 bg-muted/30">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-1 flex-wrap">
            {TIER_BUILDER_CATEGORIES.map(category => {
              const config = FEATURE_CATEGORIES[category];
              const stats = categoryStats[category] || { total: 0, enabled: 0 };
              const Icon = CATEGORY_ICONS[category as keyof typeof CATEGORY_ICONS];
              const isActive = activeCategory === category;
              const allEnabled = stats.enabled === stats.total && stats.total > 0;
              const someEnabled = stats.enabled > 0 && !allEnabled;
              
              return (
                <Button
                  key={category}
                  variant={isActive ? "default" : "ghost"}
                  size="sm"
                  className={cn(
                    "h-9 gap-2 transition-all",
                    isActive 
                      ? "bg-violet-500 hover:bg-violet-600 text-white shadow-md" 
                      : "hover:bg-muted"
                  )}
                  onClick={() => setActiveCategory(category)}
                >
                  {Icon && <Icon className={cn("h-4 w-4", isActive ? "text-white" : "text-muted-foreground")} />}
                  <span className="font-medium">{config.title}</span>
                  <Badge 
                    variant="secondary"
                    className={cn(
                      "text-[10px] px-1.5 py-0 font-mono ml-1",
                      isActive 
                        ? "bg-white/20 text-white" 
                        : allEnabled 
                          ? "bg-emerald-500/20 text-emerald-600" 
                          : someEnabled 
                            ? "bg-violet-500/20 text-violet-600"
                            : "bg-muted-foreground/10 text-muted-foreground"
                    )}
                  >
                    {stats.enabled}/{stats.total}
                  </Badge>
                </Button>
              );
            })}
          </div>

          {/* Search */}
          <div className="relative w-full lg:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search features..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-8 h-9 bg-background"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6"
                onClick={() => setSearchQuery("")}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Features Grid */}
      <div className="space-y-3">
        {filteredFeatures.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center">
              <Filter className="h-10 w-10 mx-auto mb-3 text-muted-foreground/50" />
              <p className="text-muted-foreground">No features match your search</p>
            </CardContent>
          </Card>
        ) : activeCategory === "models" ? (
          /* Models: Flat 3x3 grid without subcategory grouping */
          <Card className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-violet-500" />
                <span className="font-medium">AI Model Providers</span>
                <Badge variant="secondary" className="text-xs font-mono bg-violet-500/20 text-violet-600">
                  {filteredFeatures.filter(f => {
                    const value = features[f.feature_key] as Record<string, unknown> | undefined;
                    return value?.enabled ?? (f.default_value as Record<string, unknown>)?.enabled ?? false;
                  }).length}/{filteredFeatures.length}
                </Badge>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs gap-1 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-500/10"
                  onClick={() => {
                    const updates: Record<string, unknown> = {};
                    filteredFeatures.forEach(f => {
                      if (f.feature_type === "boolean") updates[f.feature_key] = { enabled: true };
                    });
                    setFeatures(prev => ({ ...prev, ...updates }));
                    setHasChanges(true);
                  }}
                >
                  <ToggleRight className="h-3.5 w-3.5" />
                  Enable All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs gap-1 text-rose-600 hover:text-rose-700 hover:bg-rose-500/10"
                  onClick={() => {
                    const updates: Record<string, unknown> = {};
                    filteredFeatures.forEach(f => {
                      if (f.feature_type === "boolean") updates[f.feature_key] = { enabled: false };
                    });
                    setFeatures(prev => ({ ...prev, ...updates }));
                    setHasChanges(true);
                  }}
                >
                  <ToggleLeft className="h-3.5 w-3.5" />
                  Disable All
                </Button>
              </div>
            </div>
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {filteredFeatures.map(feature => (
                <FeatureToggleCard
                  key={feature.feature_key}
                  feature={feature}
                  value={features[feature.feature_key] as Record<string, unknown> | undefined}
                  onToggle={handleFeatureToggle}
                  onLimitChange={handleLimitChange}
                />
              ))}
            </div>
          </Card>
        ) : (
          /* Other categories: Grouped by subcategory with collapsibles */
          sortedSubcategories.map(subcategory => {
            const subcategoryFeatures = featuresBySubcategory[subcategory];
            const subcategoryKey = `${activeCategory}-${subcategory}`;
            const isExpanded = expandedSubcategories.has(subcategoryKey);
            const enabledCount = subcategoryFeatures.filter(f => {
              const value = features[f.feature_key] as Record<string, unknown> | undefined;
              return value?.enabled ?? (f.default_value as Record<string, unknown>)?.enabled ?? false;
            }).length;
            const allEnabled = enabledCount === subcategoryFeatures.length;
            const someEnabled = enabledCount > 0 && !allEnabled;
            const SubIcon = SUBCATEGORY_ICONS[subcategory] || Settings;

            return (
              <Collapsible
                key={subcategory}
                open={isExpanded}
                onOpenChange={() => toggleSubcategory(subcategoryKey)}
              >
                <Card className={cn(
                  "overflow-hidden transition-all border-2",
                  allEnabled 
                    ? "border-emerald-500/30 bg-gradient-to-r from-emerald-500/5 to-transparent" 
                    : someEnabled
                      ? "border-violet-500/30 bg-gradient-to-r from-violet-500/5 to-transparent"
                      : "border-transparent"
                )}>
                  <CollapsibleTrigger asChild>
                    <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors py-3 px-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                          )}
                          <div className={cn(
                            "h-8 w-8 rounded-lg flex items-center justify-center",
                            allEnabled 
                              ? "bg-emerald-500/20" 
                              : someEnabled 
                                ? "bg-violet-500/20"
                                : "bg-muted"
                          )}>
                            <SubIcon className={cn(
                              "h-4 w-4",
                              allEnabled 
                                ? "text-emerald-500" 
                                : someEnabled 
                                  ? "text-violet-500"
                                  : "text-muted-foreground"
                            )} />
                          </div>
                          <CardTitle className="text-sm font-medium">
                            {getSubcategoryLabel(subcategory)}
                          </CardTitle>
                          <Badge 
                            variant="secondary"
                            className={cn(
                              "text-xs font-mono",
                              allEnabled 
                                ? "bg-emerald-500/20 text-emerald-600" 
                                : someEnabled 
                                  ? "bg-violet-500/20 text-violet-600"
                                  : ""
                            )}
                          >
                            {allEnabled && <CircleCheck className="h-3 w-3 mr-1" />}
                            {enabledCount}/{subcategoryFeatures.length}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 px-2 text-xs gap-1 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-500/10"
                                  onClick={() => handleBulkToggle(subcategory, true)}
                                >
                                  <ToggleRight className="h-3.5 w-3.5" />
                                  <span className="hidden sm:inline">All</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Enable all</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 px-2 text-xs gap-1 text-rose-600 hover:text-rose-700 hover:bg-rose-500/10"
                                  onClick={() => handleBulkToggle(subcategory, false)}
                                >
                                  <ToggleLeft className="h-3.5 w-3.5" />
                                  <span className="hidden sm:inline">None</span>
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Disable all</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </div>
                    </CardHeader>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <CardContent className="pt-0 pb-4 px-4">
                      <div className="grid gap-2 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                        {subcategoryFeatures.map(feature => (
                          <FeatureToggleCard
                            key={feature.feature_key}
                            feature={feature}
                            value={features[feature.feature_key] as Record<string, unknown> | undefined}
                            onToggle={handleFeatureToggle}
                            onLimitChange={handleLimitChange}
                          />
                        ))}
                      </div>
                    </CardContent>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
            );
          })
        )}
      </div>
    </div>
  );
}

interface FeatureToggleCardProps {
  feature: Feature;
  value: Record<string, unknown> | undefined;
  onToggle: (key: string, enabled: boolean) => void;
  onLimitChange: (key: string, value: number | null) => void;
}

function FeatureToggleCard({ feature, value, onToggle, onLimitChange }: FeatureToggleCardProps) {
  const isEnabled = value?.enabled ?? (feature.default_value as Record<string, unknown>)?.enabled ?? false;
  const FeatureIcon = getFeatureIcon(feature.feature_key) || Lock;

  if (feature.feature_type === "boolean") {
    return (
      <div
        className={cn(
          "flex items-center justify-between gap-2 p-3 rounded-lg border transition-all cursor-pointer group",
          isEnabled 
            ? "bg-gradient-to-r from-emerald-500/10 to-green-500/5 border-emerald-500/30 shadow-sm" 
            : "bg-muted/30 border-transparent hover:border-muted-foreground/20 hover:bg-muted/50"
        )}
        onClick={() => onToggle(feature.feature_key, !isEnabled)}
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div className={cn(
            "h-7 w-7 rounded-md flex items-center justify-center shrink-0 transition-colors",
            isEnabled 
              ? "bg-emerald-500/20" 
              : "bg-muted group-hover:bg-muted-foreground/10"
          )}>
            <FeatureIcon className={cn(
              "h-3.5 w-3.5",
              isEnabled ? "text-emerald-500" : "text-muted-foreground"
            )} />
          </div>
          <span className={cn(
            "text-sm truncate",
            isEnabled ? "font-medium text-foreground" : "text-muted-foreground"
          )}>
            {feature.feature_name}
          </span>
          {feature.is_premium && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Sparkles className="h-3 w-3 text-violet-500 shrink-0" />
                </TooltipTrigger>
                <TooltipContent>Premium feature</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        <Switch
          checked={isEnabled as boolean}
          onCheckedChange={(checked) => onToggle(feature.feature_key, checked)}
          onClick={(e) => e.stopPropagation()}
          className="shrink-0 data-[state=checked]:bg-emerald-500"
        />
      </div>
    );
  }

  if (feature.feature_type === "integer") {
    return (
      <div
        className={cn(
          "flex items-center justify-between gap-2 p-3 rounded-lg border transition-all",
          isEnabled 
            ? "bg-gradient-to-r from-emerald-500/10 to-green-500/5 border-emerald-500/30 shadow-sm" 
            : "bg-muted/30 border-transparent hover:border-muted-foreground/20"
        )}
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div className={cn(
            "h-7 w-7 rounded-md flex items-center justify-center shrink-0",
            isEnabled ? "bg-emerald-500/20" : "bg-muted"
          )}>
            <FeatureIcon className={cn(
              "h-3.5 w-3.5",
              isEnabled ? "text-emerald-500" : "text-muted-foreground"
            )} />
          </div>
          <span className={cn(
            "text-sm truncate",
            isEnabled ? "font-medium text-foreground" : "text-muted-foreground"
          )}>
            {feature.feature_name}
          </span>
          {feature.is_premium && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Sparkles className="h-3 w-3 text-violet-500 shrink-0" />
                </TooltipTrigger>
                <TooltipContent>Premium feature</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        <Select
          value={value?.value?.toString() ?? "unlimited"}
          onValueChange={(v) =>
            onLimitChange(feature.feature_key, v === "unlimited" ? null : parseInt(v))
          }
        >
          <SelectTrigger className="w-16 h-7 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="unlimited">∞</SelectItem>
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
}

export default TierFeatureBuilder;
