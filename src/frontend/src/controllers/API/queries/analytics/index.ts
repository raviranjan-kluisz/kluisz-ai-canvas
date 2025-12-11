/**
 * Analytics API query hooks
 * 
 * Provides hooks for fetching analytics data:
 * - Platform dashboard (super admin)
 * - Tenant dashboard (tenant admin)
 * - User dashboard (all users)
 * - Credit status
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../../api";
import { BASE_URL_API_V2 } from "../../../../constants/constants";

// Types
export interface AnalyticsSummary {
  total_traces: number;
  total_tokens: number;
  total_cost_usd: number;
  active_users_count?: number;
  total_active_users?: number;
  average_latency?: number;
  total_tenants?: number;
}

export interface TimeSeriesData {
  date: string;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
  trace_count: number;
  active_users_count?: number;
}

export interface TopUser {
  user_id: string;
  username: string;
  total_tokens: number;
  total_cost_usd: number;
  trace_count: number;
  credits_allocated: number;
  credits_used: number;
}

export interface TopFlow {
  flow_id: string;
  total_tokens: number;
  total_cost_usd: number;
  trace_count: number;
  kluisz_project_id?: string;
}

export interface TopTenant {
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
  total_tokens: number;
  total_cost_usd: number;
  trace_count: number;
  active_users_count: number;
}

export interface ModelUsage {
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
  trace_count: number;
}

export interface CreditStatus {
  user_id: string;
  credits_allocated: number;
  credits_used: number;
  credits_remaining: number;
  credits_per_month?: number;
  license_is_active: boolean;
  license_tier?: {
    id: string;
    name: string;
    credits_per_usd: number;
    default_credits: number;
  };
  can_execute: boolean;
}

export interface PlatformDashboard {
  time_series: TimeSeriesData[];
  summary: AnalyticsSummary;
  top_tenants: TopTenant[];
  by_model: Record<string, ModelUsage>;
  period_start: string;
  period_end: string;
  error?: string;
}

export interface TenantDashboard {
  time_series: TimeSeriesData[];
  summary: AnalyticsSummary;
  top_users: TopUser[];
  top_flows: TopFlow[];
  by_model: Record<string, ModelUsage>;
  period_start: string;
  period_end: string;
  error?: string;
}

export interface UserDashboard {
  time_series: TimeSeriesData[];
  summary: AnalyticsSummary;
  credits: CreditStatus;
  top_flows: TopFlow[];
  by_model?: Record<string, ModelUsage>;
  period_start: string;
  period_end: string;
  error?: string;
}

// API URL constants
const ANALYTICS_BASE = "analytics/";

// Query keys
export const analyticsQueryKeys = {
  platformDashboard: (params?: { startDate?: string; endDate?: string }) => 
    ["analytics", "platform", "dashboard", params],
  tenantDashboard: (tenantId: string, params?: { startDate?: string; endDate?: string }) => 
    ["analytics", "tenant", tenantId, "dashboard", params],
  userDashboard: (params?: { startDate?: string; endDate?: string }) => 
    ["analytics", "user", "dashboard", params],
  userDashboardById: (userId: string, params?: { startDate?: string; endDate?: string }) => 
    ["analytics", "user", userId, "dashboard", params],
  creditStatus: ["analytics", "credits", "status"],
  userCreditStatus: (userId: string) => ["analytics", "credits", userId, "status"],
};

// ==================== Platform Analytics (Super Admin) ====================

export const useGetPlatformDashboard = (
  options?: {
    startDate?: string;
    endDate?: string;
    enabled?: boolean;
  }
) => {
  const params = new URLSearchParams();
  if (options?.startDate) params.append("start_date", options.startDate);
  if (options?.endDate) params.append("end_date", options.endDate);
  
  const queryString = params.toString();
  const url = BASE_URL_API_V2 + ANALYTICS_BASE + "platform/dashboard" + (queryString ? `?${queryString}` : "");
  
  return useQuery<PlatformDashboard>({
    queryKey: analyticsQueryKeys.platformDashboard({ startDate: options?.startDate, endDate: options?.endDate }),
    queryFn: async () => {
      const response = await api.get<PlatformDashboard>(url);
      return response.data;
    },
    enabled: options?.enabled ?? true,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: false,
  });
};

// ==================== Tenant Analytics (Tenant Admin) ====================

export const useGetTenantDashboard = (
  tenantId: string,
  options?: {
    startDate?: string;
    endDate?: string;
    enabled?: boolean;
  }
) => {
  const params = new URLSearchParams();
  if (options?.startDate) params.append("start_date", options.startDate);
  if (options?.endDate) params.append("end_date", options.endDate);
  
  const queryString = params.toString();
  const url = BASE_URL_API_V2 + ANALYTICS_BASE + `tenant/${tenantId}/dashboard` + (queryString ? `?${queryString}` : "");
  
  return useQuery<TenantDashboard>({
    queryKey: analyticsQueryKeys.tenantDashboard(tenantId, { startDate: options?.startDate, endDate: options?.endDate }),
    queryFn: async () => {
      const response = await api.get<TenantDashboard>(url);
      return response.data;
    },
    enabled: !!tenantId && (options?.enabled ?? true),
    staleTime: 60000,
    retry: false,
  });
};

export const useGetTenantTimeSeries = (
  tenantId: string,
  options?: {
    startDate?: string;
    endDate?: string;
    enabled?: boolean;
  }
) => {
  const params = new URLSearchParams();
  if (options?.startDate) params.append("start_date", options.startDate);
  if (options?.endDate) params.append("end_date", options.endDate);
  
  const queryString = params.toString();
  const url = BASE_URL_API_V2 + ANALYTICS_BASE + `tenant/${tenantId}/time-series` + (queryString ? `?${queryString}` : "");
  
  return useQuery<TimeSeriesData[]>({
    queryKey: ["analytics", "tenant", tenantId, "time-series", options],
    queryFn: async () => {
      const response = await api.get<TimeSeriesData[]>(url);
      return response.data;
    },
    enabled: !!tenantId && (options?.enabled ?? true),
    staleTime: 60000,
    retry: false,
  });
};

// ==================== User Analytics ====================

export const useGetUserDashboard = (
  options?: {
    startDate?: string;
    endDate?: string;
    enabled?: boolean;
  }
) => {
  const params = new URLSearchParams();
  if (options?.startDate) params.append("start_date", options.startDate);
  if (options?.endDate) params.append("end_date", options.endDate);
  
  const queryString = params.toString();
  const url = BASE_URL_API_V2 + ANALYTICS_BASE + "user/dashboard" + (queryString ? `?${queryString}` : "");
  
  return useQuery<UserDashboard>({
    queryKey: analyticsQueryKeys.userDashboard({ startDate: options?.startDate, endDate: options?.endDate }),
    queryFn: async () => {
      const response = await api.get<UserDashboard>(url);
      return response.data;
    },
    enabled: options?.enabled ?? true,
    staleTime: 60000,
    retry: false,
  });
};

export const useGetUserDashboardById = (
  userId: string,
  options?: {
    startDate?: string;
    endDate?: string;
    enabled?: boolean;
  }
) => {
  const params = new URLSearchParams();
  if (options?.startDate) params.append("start_date", options.startDate);
  if (options?.endDate) params.append("end_date", options.endDate);
  
  const queryString = params.toString();
  const url = BASE_URL_API_V2 + ANALYTICS_BASE + `user/${userId}/dashboard` + (queryString ? `?${queryString}` : "");
  
  return useQuery<UserDashboard>({
    queryKey: analyticsQueryKeys.userDashboardById(userId, { startDate: options?.startDate, endDate: options?.endDate }),
    queryFn: async () => {
      const response = await api.get<UserDashboard>(url);
      return response.data;
    },
    enabled: !!userId && (options?.enabled ?? true),
    staleTime: 60000,
    retry: false,
  });
};

// ==================== Credits API ====================

export const useGetCreditStatus = (options?: { enabled?: boolean }) => {
  const url = BASE_URL_API_V2 + ANALYTICS_BASE + "credits/status";
  
  return useQuery<CreditStatus>({
    queryKey: analyticsQueryKeys.creditStatus,
    queryFn: async () => {
      const response = await api.get<CreditStatus>(url);
      return response.data;
    },
    enabled: options?.enabled ?? true,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
    retry: false,
  });
};

export const useGetUserCreditStatus = (userId: string, options?: { enabled?: boolean }) => {
  const url = BASE_URL_API_V2 + ANALYTICS_BASE + `credits/user/${userId}/status`;
  
  return useQuery<CreditStatus>({
    queryKey: analyticsQueryKeys.userCreditStatus(userId),
    queryFn: async () => {
      const response = await api.get<CreditStatus>(url);
      return response.data;
    },
    enabled: !!userId && (options?.enabled ?? true),
    staleTime: 30000,
    retry: false,
  });
};

// ==================== Admin: Sync Stats ====================

export const useSyncUsageStats = () => {
  const url = BASE_URL_API_V2 + ANALYTICS_BASE + "admin/sync-stats";
  
  return useMutation({
    mutationFn: async (params?: { tenantId?: string; startDate?: string; endDate?: string }) => {
      const queryParams = new URLSearchParams();
      if (params?.tenantId) queryParams.append("tenant_id", params.tenantId);
      if (params?.startDate) queryParams.append("start_date", params.startDate);
      if (params?.endDate) queryParams.append("end_date", params.endDate);
      
      const queryString = queryParams.toString();
      const response = await api.post(url + (queryString ? `?${queryString}` : ""));
      return response.data;
    },
  });
};

// Export all hooks
export default {
  useGetPlatformDashboard,
  useGetTenantDashboard,
  useGetTenantTimeSeries,
  useGetUserDashboard,
  useGetUserDashboardById,
  useGetCreditStatus,
  useGetUserCreditStatus,
  useSyncUsageStats,
};

