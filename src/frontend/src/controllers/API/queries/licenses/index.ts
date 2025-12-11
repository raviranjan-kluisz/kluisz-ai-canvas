// License API query hooks

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/controllers/API/api";
import { tenantKeys } from "../tenants";

// Types
export type LicenseTier = "BASIC" | "PRO" | "ENTERPRISE";

export interface License {
  id?: string;
  tenant_id: string;
  license_type?: string;
  tier?: LicenseTier | string | {
    id: string;
    name: string;
    default_credits: number;
    credits_per_usd: number | null;
  };
  max_users?: number;
  max_flows?: number;
  max_api_calls?: number;
  credits?: number;
  credits_per_month?: number;
  credits_used?: number;
  credits_remaining?: number;
  features?: Record<string, unknown>;
  billing_cycle?: string;
  price?: string;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
  is_expired?: boolean;
  is_valid?: boolean;
  created_at?: string;
  updated_at?: string;
  // New subscription fields (from tenant)
  subscription_tier_id?: string;
  subscription_status?: string;
  subscription_license_count?: number;
  subscription_start_date?: string;
  subscription_end_date?: string;
  subscription_renewal_date?: string;
  subscription_amount?: number;
  subscription_currency?: string;
}

export interface LicenseCreate {
  tenant_id: string;
  tier: LicenseTier;
  license_type?: string;
  max_users?: number;
  max_flows?: number;
  max_api_calls?: number;
  credits?: number;
  credits_per_month?: number;
  features?: Record<string, unknown>;
  billing_cycle?: string;
  price?: string;
  end_date?: string;
  is_active?: boolean;
}

export interface LicenseUpdate {
  tier?: LicenseTier;
  max_users?: number;
  max_flows?: number;
  max_api_calls?: number;
  credits?: number;
  credits_per_month?: number;
  credits_used?: number;
  features?: Record<string, unknown>;
  billing_cycle?: string;
  price?: string;
  end_date?: string;
  is_active?: boolean;
}

export interface TierInfo {
  tier: LicenseTier;
  max_users: number;
  max_flows: number;
  max_api_calls: number;
  credits: number;
  credits_per_month: number;
  price: string;
  features: string[];
}

// Query keys
export const licenseKeys = {
  all: ["licenses"] as const,
  lists: () => [...licenseKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) => [...licenseKeys.lists(), filters] as const,
  details: () => [...licenseKeys.all, "detail"] as const,
  detail: (id: string) => [...licenseKeys.details(), id] as const,
  active: (tenantId: string) => [...licenseKeys.all, "active", tenantId] as const,
  tiers: () => [...licenseKeys.all, "tiers"] as const,
};

// API functions
const getLicenses = async (params?: { skip?: number; limit?: number; tenant_id?: string }): Promise<License[]> => {
  const response = await api.get("/api/v1/licenses/", { params });
  return response.data;
};

const getLicense = async (id: string): Promise<License> => {
  const response = await api.get(`/api/v1/licenses/${id}`);
  return response.data;
};

const getActiveLicense = async (tenantId: string): Promise<License | null> => {
  try {
    const response = await api.get(`/api/v1/licenses/tenant/${tenantId}/active`);
    // Backend now returns subscription info, map it to License format for compatibility
    const data = response.data;
    return {
      tenant_id: data.tenant_id || tenantId,
      subscription_tier_id: data.subscription_tier_id,
      subscription_status: data.subscription_status,
      subscription_license_count: data.subscription_license_count || 0,
      subscription_start_date: data.subscription_start_date,
      subscription_end_date: data.subscription_end_date,
      subscription_renewal_date: data.subscription_renewal_date,
      subscription_amount: data.subscription_amount,
      subscription_currency: data.subscription_currency || "USD",
      // Tier is an object from backend, store it as-is
      tier: data.tier,
      credits: data.tier?.default_credits || 0,
      credits_per_month: data.tier?.default_credits || 0,
      credits_used: 0, // Will be calculated from user stats
      credits_remaining: data.tier?.default_credits || 0,
      is_active: data.subscription_status === "active",
      is_valid: data.subscription_status === "active",
      is_expired: data.subscription_status === "expired" || data.subscription_status === "cancelled",
    } as License;
  } catch (error: any) {
    // If endpoint returns 404, return null (no active license)
    if (error.response?.status === 404) {
      return null;
    }
    throw error;
  }
};

const createLicense = async (data: LicenseCreate): Promise<License> => {
  const response = await api.post("/api/v1/licenses/", data);
  return response.data;
};

const createLicenseFromTier = async ({ tenantId, tier }: { tenantId: string; tier: LicenseTier }): Promise<License> => {
  const response = await api.post("/api/v1/licenses/from-tier", null, {
    params: { tenant_id: tenantId, tier },
  });
  return response.data;
};

const updateLicense = async ({ id, data }: { id: string; data: LicenseUpdate }): Promise<License> => {
  const response = await api.patch(`/api/v1/licenses/${id}`, data);
  return response.data;
};

const deleteLicense = async (id: string): Promise<void> => {
  await api.delete(`/api/v1/licenses/${id}`);
};

const getTierInfo = async (): Promise<{ tiers: TierInfo[] }> => {
  const response = await api.get("/api/v1/licenses/tiers/info");
  return response.data;
};

// Query hooks
export const useGetLicenses = (params?: { skip?: number; limit?: number; tenant_id?: string }) => {
  return useQuery({
    queryKey: licenseKeys.list(params ?? {}),
    queryFn: () => getLicenses(params),
  });
};

export const useGetLicense = (id: string) => {
  return useQuery({
    queryKey: licenseKeys.detail(id),
    queryFn: () => getLicense(id),
    enabled: !!id,
  });
};

export const useGetActiveLicense = (tenantId: string) => {
  return useQuery({
    queryKey: licenseKeys.active(tenantId),
    queryFn: () => getActiveLicense(tenantId),
    enabled: !!tenantId,
    retry: false, // Don't retry on 404
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetTierInfo = () => {
  return useQuery({
    queryKey: licenseKeys.tiers(),
    queryFn: getTierInfo,
  });
};

// Mutation hooks
export const useCreateLicense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createLicense,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: licenseKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tenantKeys.detail(data.tenant_id) });
    },
  });
};

export const useCreateLicenseFromTier = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createLicenseFromTier,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: licenseKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tenantKeys.detail(data.tenant_id) });
    },
  });
};

export const useUpdateLicense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateLicense,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: licenseKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: licenseKeys.lists() });
    },
  });
};

export const useDeleteLicense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteLicense,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: licenseKeys.lists() });
    },
  });
};
