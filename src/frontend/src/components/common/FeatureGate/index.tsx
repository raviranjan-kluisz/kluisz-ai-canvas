import { ReactNode } from "react";
import { Lock } from "lucide-react";
import { useFeatureFlags } from "@/contexts/featureContext";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface FeatureGateProps {
  // Feature to check
  feature: string;

  // Children to render if enabled
  children: ReactNode;

  // Optional: what to render if disabled
  fallback?: ReactNode;

  // Optional: show locked indicator instead of hiding
  showLocked?: boolean;
  lockedMessage?: string;

  // Optional: require multiple features (AND logic)
  requireAll?: string[];

  // Optional: require any of features (OR logic)
  requireAny?: string[];
}

export function FeatureGate({
  feature,
  children,
  fallback = null,
  showLocked = false,
  lockedMessage = "This feature is not available in your plan",
  requireAll,
  requireAny,
}: FeatureGateProps) {
  const { isFeatureEnabled, tierName } = useFeatureFlags();

  // Check main feature
  let enabled = isFeatureEnabled(feature);

  // Check requireAll (AND logic)
  if (enabled && requireAll?.length) {
    enabled = requireAll.every((f) => isFeatureEnabled(f));
  }

  // Check requireAny (OR logic)
  if (!enabled && requireAny?.length) {
    enabled = requireAny.some((f) => isFeatureEnabled(f));
  }

  if (enabled) {
    return <>{children}</>;
  }

  if (showLocked) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="relative inline-block cursor-not-allowed opacity-50">
            {children}
            <div className="absolute inset-0 flex items-center justify-center rounded bg-background/50">
              <Lock className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{lockedMessage}</p>
          {tierName && (
            <p className="text-xs text-muted-foreground">
              Current plan: {tierName}
            </p>
          )}
        </TooltipContent>
      </Tooltip>
    );
  }

  return <>{fallback}</>;
}

// Convenience wrapper for model features
export function ModelGate({
  provider,
  children,
  fallback,
  showLocked,
}: {
  provider: string;
  children: ReactNode;
  fallback?: ReactNode;
  showLocked?: boolean;
}) {
  const featureKey = `models.${provider.toLowerCase()}`;
  return (
    <FeatureGate
      feature={featureKey}
      fallback={fallback}
      showLocked={showLocked}
      lockedMessage={`${provider} models are not available in your plan`}
    >
      {children}
    </FeatureGate>
  );
}

// Convenience wrapper for integration features
export function IntegrationGate({
  integration,
  children,
  fallback,
  showLocked,
}: {
  integration: string;
  children: ReactNode;
  fallback?: ReactNode;
  showLocked?: boolean;
}) {
  const featureKey = `integrations.${integration.toLowerCase()}`;
  return (
    <FeatureGate
      feature={featureKey}
      fallback={fallback}
      showLocked={showLocked}
      lockedMessage={`${integration} integration is not available in your plan`}
    >
      {children}
    </FeatureGate>
  );
}

// Convenience wrapper for UI features
export function UIFeatureGate({
  uiFeature,
  children,
  fallback,
  showLocked,
}: {
  uiFeature: string;
  children: ReactNode;
  fallback?: ReactNode;
  showLocked?: boolean;
}) {
  return (
    <FeatureGate
      feature={`ui.${uiFeature}`}
      fallback={fallback}
      showLocked={showLocked}
    >
      {children}
    </FeatureGate>
  );
}

// Convenience wrapper for component features
export function ComponentGate({
  componentCategory,
  children,
  fallback,
  showLocked,
}: {
  componentCategory: string;
  children: ReactNode;
  fallback?: ReactNode;
  showLocked?: boolean;
}) {
  const featureKey = `components.${componentCategory.toLowerCase()}`;
  return (
    <FeatureGate
      feature={featureKey}
      fallback={fallback}
      showLocked={showLocked}
      lockedMessage={`${componentCategory} components are not available in your plan`}
    >
      {children}
    </FeatureGate>
  );
}

export default FeatureGate;




