// Billing & Usage API query hooks

import { useQuery } from "@tanstack/react-query";
import { api } from "@/controllers/API/api";

// Types
export interface DailyUsageStats {
  date: string;
  total_users?: number;
  active_users?: number;
  total_flows?: number;
  total_flow_runs: number;
  total_api_calls: number;
  total_storage_bytes: number;
  cost?: string;
  // User-specific fields
  flow_runs?: number;
  api_calls?: number;
  storage_bytes?: number;
  credits_used?: number;
  last_activity_at?: string;
}

export interface TenantUsageResponse {
  tenant_id: string;
  tenant_name: string;
  start_date: string;
  end_date: string;
  daily_stats: DailyUsageStats[];
}

export interface TenantUsageSummary {
  tenant_id: string;
  tenant_name: string;
  start_date: string;
  end_date: string;
  total_flow_runs: number;
  total_api_calls: number;
  total_storage_bytes: number;
  max_users: number;
  max_active_users: number;
  license?: {
    tier: string;
    credits: number;
    credits_used: number;
    credits_remaining: number;
    is_valid: boolean;
  };
}

export interface UserUsageResponse {
  user_id: string;
  username: string;
  start_date: string;
  end_date: string;
  daily_stats: DailyUsageStats[];
}

export interface UserUsageSummary {
  user_id: string;
  username: string;
  start_date: string;
  end_date: string;
  total_flow_runs: number;
  total_api_calls: number;
  total_storage_bytes: number;
  total_credits_used: number;
  days_active: number;
}

export interface AnalyticsOverview {
  role: "super_admin" | "tenant_admin" | "user";
  // Super admin fields
  total_tenants?: number;
  active_tenants?: number;
  total_users?: number;
  tenants?: Array<{
    id: string;
    name: string;
    slug: string;
    is_active: boolean;
    user_count: number;
    max_users: number;
    license?: {
      tier: string;
      credits_remaining: number;
      is_valid: boolean;
    };
  }>;
  // Tenant admin fields
  tenant?: {
    id: string;
    name: string;
    slug: string;
    is_active: boolean;
  };
  user_count?: number;
  max_users?: number;
  license?: {
    tier: string;
    credits: number;
    credits_used: number;
    credits_remaining: number;
    is_valid: boolean;
  };
  usage_summary?: TenantUsageSummary | UserUsageSummary;
  // Regular user fields
  user?: {
    id: string;
    username: string;
  };
}

// Query keys
export const billingKeys = {
  all: ["billing"] as const,
  tenantUsage: (tenantId: string, startDate?: string, endDate?: string) =>
    [...billingKeys.all, "tenant", tenantId, "usage", startDate, endDate] as const,
  tenantSummary: (tenantId: string, startDate?: string, endDate?: string) =>
    [...billingKeys.all, "tenant", tenantId, "summary", startDate, endDate] as const,
  userUsage: (userId: string, startDate?: string, endDate?: string) =>
    [...billingKeys.all, "user", userId, "usage", startDate, endDate] as const,
  userSummary: (userId: string, startDate?: string, endDate?: string) =>
    [...billingKeys.all, "user", userId, "summary", startDate, endDate] as const,
  overview: () => [...billingKeys.all, "overview"] as const,
};

// API functions
const getTenantUsage = async (
  tenantId: string,
  params?: { start_date?: string; end_date?: string }
): Promise<TenantUsageResponse> => {
  const response = await api.get(`/api/v1/billing/tenant/${tenantId}/usage`, { params });
  return response.data;
};

const getTenantUsageSummary = async (
  tenantId: string,
  params?: { start_date?: string; end_date?: string }
): Promise<TenantUsageSummary> => {
  const response = await api.get(`/api/v1/billing/tenant/${tenantId}/usage/summary`, { params });
  return response.data;
};

const getUserUsage = async (
  userId: string,
  params?: { start_date?: string; end_date?: string }
): Promise<UserUsageResponse> => {
  const response = await api.get(`/api/v1/billing/user/${userId}/usage`, { params });
  return response.data;
};

const getUserUsageSummary = async (
  userId: string,
  params?: { start_date?: string; end_date?: string }
): Promise<UserUsageSummary> => {
  const response = await api.get(`/api/v1/billing/user/${userId}/usage/summary`, { params });
  return response.data;
};

const getAnalyticsOverview = async (): Promise<AnalyticsOverview> => {
  const response = await api.get("/api/v1/billing/analytics/overview");
  return response.data;
};

// Query hooks
export const useGetTenantUsage = (
  tenantId: string,
  params?: { start_date?: string; end_date?: string }
) => {
  return useQuery({
    queryKey: billingKeys.tenantUsage(tenantId, params?.start_date, params?.end_date),
    queryFn: () => getTenantUsage(tenantId, params),
    enabled: !!tenantId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetTenantUsageSummary = (
  tenantId: string,
  params?: { start_date?: string; end_date?: string }
) => {
  return useQuery({
    queryKey: billingKeys.tenantSummary(tenantId, params?.start_date, params?.end_date),
    queryFn: () => getTenantUsageSummary(tenantId, params),
    enabled: !!tenantId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetUserUsage = (
  userId: string,
  params?: { start_date?: string; end_date?: string }
) => {
  return useQuery({
    queryKey: billingKeys.userUsage(userId, params?.start_date, params?.end_date),
    queryFn: () => getUserUsage(userId, params),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetUserUsageSummary = (
  userId: string,
  params?: { start_date?: string; end_date?: string }
) => {
  return useQuery({
    queryKey: billingKeys.userSummary(userId, params?.start_date, params?.end_date),
    queryFn: () => getUserUsageSummary(userId, params),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetAnalyticsOverview = (options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: billingKeys.overview(),
    queryFn: getAnalyticsOverview,
    enabled: options?.enabled ?? true,
    retry: false,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};
