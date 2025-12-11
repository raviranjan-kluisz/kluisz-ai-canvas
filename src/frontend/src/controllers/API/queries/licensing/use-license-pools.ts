import type { UseQueryResult } from "@tanstack/react-query";
import type { useQueryFunctionType, useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface LicensePool {
  total_count: number;
  available_count: number;
  assigned_count: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface TenantLicensePools {
  [tierId: string]: LicensePool;
}

export interface CreatePoolRequest {
  tier_id: string;
  total_count: number;
}

export const useGetTenantLicensePools: useQueryFunctionType<
  { tenantId?: string; enabled?: boolean },
  TenantLicensePools
> = (options?) => {
  const { query } = UseRequestProcessor();

  const getTenantLicensePoolsFn = async ({
    tenantId,
  }: {
    tenantId: string;
  }): Promise<TenantLicensePools> => {
    const res = await api.get(
      getURL("LICENSE_POOLS", {}, true) + `tenant/${tenantId}`,
    );
    return res.data;
  };

  const queryResult: UseQueryResult<TenantLicensePools, Error> = query(
    ["useGetTenantLicensePools", options?.tenantId],
    () => getTenantLicensePoolsFn({ tenantId: options?.tenantId! }),
    {
      refetchOnWindowFocus: false,
      refetchOnMount: "always" as const, // Refetch when component mounts
      retry: false,
      staleTime: 60000, // 1 minute staleTime for better caching
      enabled: !!options?.tenantId && (options?.enabled ?? true),
      ...options,
    },
  );

  return queryResult;
};

export const useGetMyTenantPools: useQueryFunctionType<
  { enabled?: boolean },
  TenantLicensePools
> = (options?) => {
  const { query } = UseRequestProcessor();

  const getMyTenantPoolsFn = async (): Promise<TenantLicensePools> => {
    const res = await api.get(getURL("LICENSE_POOLS", {}, true) + "my-tenant");
    return res.data;
  };

  const queryResult: UseQueryResult<TenantLicensePools, Error> = query(
    ["useGetMyTenantPools"],
    getMyTenantPoolsFn,
    {
      refetchOnWindowFocus: false,
      retry: false,
      staleTime: 30000,
      enabled: options?.enabled ?? true,
      ...options,
    },
  );

  return queryResult;
};

export const useCreateOrUpdatePool: useMutationFunctionType<
  undefined,
  { tenantId: string; data: CreatePoolRequest }
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  const createOrUpdatePoolFn = async ({
    tenantId,
    data,
  }: {
    tenantId: string;
    data: CreatePoolRequest;
  }): Promise<LicensePool> => {
    const res = await api.post(
      getURL("LICENSE_POOLS", {}, true) + `tenant/${tenantId}`,
      data,
    );
    return res.data;
  };

  return mutate(
    ["useCreateOrUpdatePool"],
    createOrUpdatePoolFn,
    options,
  );
};

