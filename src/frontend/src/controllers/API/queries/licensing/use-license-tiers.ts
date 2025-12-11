import type { UseQueryResult } from "@tanstack/react-query";
import type { useQueryFunctionType, useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface LicenseTier {
  id: string;
  name: string;
  description?: string;
  token_price_per_1000: number;
  credits_per_usd: number;
  pricing_multiplier: number;
  default_credits: number;
  default_credits_per_month?: number;
  max_users?: number;
  max_flows?: number;
  max_api_calls?: number;
  features: Record<string, any>;
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface LicenseTierCreate {
  name: string;
  description?: string;
  token_price_per_1000?: number;
  credits_per_usd?: number;
  pricing_multiplier?: number;
  default_credits?: number;
  default_credits_per_month?: number;
  max_users?: number;
  max_flows?: number;
  max_api_calls?: number;
  features?: Record<string, any>;
  is_active?: boolean;
}

export interface LicenseTierUpdate extends Partial<LicenseTierCreate> {}

export const useListLicenseTiers: useQueryFunctionType<
  { enabled?: boolean },
  LicenseTier[]
> = (options?) => {
  const { query } = UseRequestProcessor();

  const getLicenseTiersFn = async (): Promise<LicenseTier[]> => {
    const res = await api.get(getURL("LICENSE_TIERS", {}, true));
    return res.data;
  };

  const queryResult: UseQueryResult<LicenseTier[], Error> = query(
    ["useListLicenseTiers"],
    getLicenseTiersFn,
    {
      refetchOnWindowFocus: false,
      retry: false, // Don't retry on 403 errors
      staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
      enabled: options?.enabled ?? true,
      ...options,
    },
  );

  return queryResult;
};

export const useGetLicenseTier: useQueryFunctionType<
  { tierId: string },
  LicenseTier
> = (options?) => {
  const { query } = UseRequestProcessor();

  const getLicenseTierFn = async ({
    tierId,
  }: {
    tierId: string;
  }): Promise<LicenseTier> => {
    const res = await api.get(getURL("LICENSE_TIERS", { tierId }, true));
    return res.data;
  };

  const queryResult: UseQueryResult<LicenseTier, Error> = query(
    ["useGetLicenseTier", options?.tierId],
    () => getLicenseTierFn({ tierId: options?.tierId! }),
    {
      refetchOnWindowFocus: false,
      enabled: !!options?.tierId,
      ...options,
    },
  );

  return queryResult;
};

export const useCreateLicenseTier: useMutationFunctionType<
  undefined,
  LicenseTierCreate
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  const createLicenseTierFn = async (
    data: LicenseTierCreate,
  ): Promise<LicenseTier> => {
    const res = await api.post(getURL("LICENSE_TIERS", {}, true), data);
    return res.data;
  };

  return mutate(
    ["useCreateLicenseTier"],
    createLicenseTierFn,
    options,
  );
};

export const useUpdateLicenseTier: useMutationFunctionType<
  undefined,
  { tierId: string; data: LicenseTierUpdate }
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  const updateLicenseTierFn = async ({
    tierId,
    data,
  }: {
    tierId: string;
    data: LicenseTierUpdate;
  }): Promise<LicenseTier> => {
    const res = await api.put(
      getURL("LICENSE_TIERS", { tierId }, true),
      data,
    );
    return res.data;
  };

  return mutate(
    ["useUpdateLicenseTier"],
    updateLicenseTierFn,
    options,
  );
};

export const useDeleteLicenseTier: useMutationFunctionType<
  undefined,
  string
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  const deleteLicenseTierFn = async (tierId: string): Promise<void> => {
    await api.delete(getURL("LICENSE_TIERS", { tierId }, true));
  };

  return mutate(
    ["useDeleteLicenseTier"],
    deleteLicenseTierFn,
    options,
  );
};

