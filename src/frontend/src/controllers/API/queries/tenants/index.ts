// Tenant API query hooks

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/controllers/API/api";

// Types
export interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  max_users: number;
  description?: string;
  created_at: string;
  updated_at: string;
  license_pools?: Record<string, any>; // JSON field from backend
  subscription_tier_id?: string | null;
  subscription_license_count?: number;
  subscription_status?: string | null;
  subscription_start_date?: string | null;
  subscription_end_date?: string | null;
  subscription_renewal_date?: string | null;
  subscription_payment_method_id?: string | null;
  subscription_amount?: number | null;
  subscription_currency?: string;
}

export interface TenantCreate {
  name: string;
  slug: string;
  max_users?: number;
  description?: string;
  is_active?: boolean;
}

export interface TenantUpdate {
  name?: string;
  slug?: string;
  max_users?: number;
  description?: string;
  is_active?: boolean;
}

export interface TenantUserCount {
  tenant_id: string;
  user_count: number;
  max_users: number;
}

export interface TenantUserCreate {
  username: string;
  password: string;
  is_tenant_admin?: boolean;
}

export interface TenantUserUpdate {
  is_active?: boolean;
  is_tenant_admin?: boolean;
  password?: string;
}

// Query keys
export const tenantKeys = {
  all: ["tenants"] as const,
  lists: () => [...tenantKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) => [...tenantKeys.lists(), filters] as const,
  details: () => [...tenantKeys.all, "detail"] as const,
  detail: (id: string) => [...tenantKeys.details(), id] as const,
  bySlug: (slug: string) => [...tenantKeys.all, "slug", slug] as const,
  users: (id: string) => [...tenantKeys.all, id, "users"] as const,
  userCount: (id: string) => [...tenantKeys.all, id, "userCount"] as const,
};

// API functions
const getTenants = async (params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<Tenant[]> => {
  const response = await api.get("/api/v1/tenants/", { params });
  return response.data;
};

const getTenant = async (id: string): Promise<Tenant> => {
  const response = await api.get(`/api/v1/tenants/${id}`);
  return response.data;
};

const getTenantBySlug = async (slug: string): Promise<Tenant> => {
  const response = await api.get(`/api/v1/tenants/slug/${slug}`);
  return response.data;
};

const createTenant = async (data: TenantCreate): Promise<Tenant> => {
  const response = await api.post("/api/v1/tenants/", data);
  return response.data;
};

const updateTenant = async ({ id, data }: { id: string; data: TenantUpdate }): Promise<Tenant> => {
  const response = await api.patch(`/api/v1/tenants/${id}`, data);
  return response.data;
};

const deleteTenant = async (id: string): Promise<void> => {
  await api.delete(`/api/v1/tenants/${id}`);
};

const getTenantUsers = async (id: string, params?: { skip?: number; limit?: number }) => {
  const response = await api.get(`/api/v1/tenants/${id}/users`, { params });
  return response.data;
};

const getTenantUserCount = async (id: string): Promise<TenantUserCount> => {
  const response = await api.get(`/api/v1/tenants/${id}/users/count`);
  return response.data;
};

const createTenantUser = async ({ tenantId, data }: { tenantId: string; data: TenantUserCreate }) => {
  const response = await api.post(`/api/v1/tenants/${tenantId}/users`, data);
  return response.data;
};

const updateTenantUser = async ({ tenantId, userId, data }: { tenantId: string; userId: string; data: TenantUserUpdate }) => {
  const response = await api.patch(`/api/v1/tenants/${tenantId}/users/${userId}`, data);
  return response.data;
};

const deleteTenantUser = async ({ tenantId, userId }: { tenantId: string; userId: string }) => {
  await api.delete(`/api/v1/tenants/${tenantId}/users/${userId}`);
};

// Query hooks
export const useGetTenants = (params?: { skip?: number; limit?: number; is_active?: boolean }) => {
  return useQuery({
    queryKey: tenantKeys.list(params ?? {}),
    queryFn: () => getTenants(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetTenant = (id: string) => {
  return useQuery({
    queryKey: tenantKeys.detail(id),
    queryFn: () => getTenant(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetTenantBySlug = (slug: string) => {
  return useQuery({
    queryKey: tenantKeys.bySlug(slug),
    queryFn: () => getTenantBySlug(slug),
    enabled: !!slug,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetTenantUsers = (id: string, params?: { skip?: number; limit?: number }) => {
  return useQuery({
    queryKey: tenantKeys.users(id),
    queryFn: () => getTenantUsers(id, params),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useGetTenantUserCount = (id: string) => {
  return useQuery({
    queryKey: tenantKeys.userCount(id),
    queryFn: () => getTenantUserCount(id),
    enabled: !!id,
  });
};

// Mutation hooks
export const useCreateTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() });
    },
  });
};

export const useUpdateTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateTenant,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() });
    },
  });
};

export const useDeleteTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.lists() });
    },
  });
};

// Tenant user management hooks
export const useCreateTenantUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTenantUser,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.users(variables.tenantId) });
      queryClient.invalidateQueries({ queryKey: tenantKeys.userCount(variables.tenantId) });
    },
  });
};

export const useUpdateTenantUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateTenantUser,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.users(variables.tenantId) });
    },
  });
};

export const useDeleteTenantUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteTenantUser,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: tenantKeys.users(variables.tenantId) });
      queryClient.invalidateQueries({ queryKey: tenantKeys.userCount(variables.tenantId) });
    },
  });
};
