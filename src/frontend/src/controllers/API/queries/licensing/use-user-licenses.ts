import type { useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface User {
  id: string;
  username: string;
  license_pool_id?: string;
  license_tier_id?: string;
  credits_allocated: number;
  credits_used: number;
  credits_per_month?: number;
  license_is_active: boolean;
  license_assigned_at?: string;
  license_expires_at?: string;
  tenant_id?: string;
}

export interface AssignLicenseRequest {
  user_id: string;
  tier_id: string;
}

export interface UpgradeLicenseRequest {
  user_id: string;
  new_tier_id: string;
  preserve_credits?: boolean;
}

export const useAssignLicense: useMutationFunctionType<
  undefined,
  AssignLicenseRequest
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  const assignLicenseFn = async (
    data: AssignLicenseRequest,
  ): Promise<User> => {
    const res = await api.post(
      getURL("USER_LICENSES", {}, true) + "assign",
      data,
    );
    return res.data;
  };

  return mutate(
    ["useAssignLicense"],
    assignLicenseFn,
    options,
  );
};

export const useUnassignLicense: useMutationFunctionType<
  undefined,
  string
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  const unassignLicenseFn = async (userId: string): Promise<User> => {
    const res = await api.post(
      getURL("USER_LICENSES", {}, true) + `unassign/${userId}`,
    );
    return res.data;
  };

  return mutate(
    ["useUnassignLicense"],
    unassignLicenseFn,
    options,
  );
};

export const useUpgradeLicense: useMutationFunctionType<
  undefined,
  UpgradeLicenseRequest
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  const upgradeLicenseFn = async (
    data: UpgradeLicenseRequest,
  ): Promise<User> => {
    const res = await api.post(
      getURL("USER_LICENSES", {}, true) + "upgrade",
      data,
    );
    return res.data;
  };

  return mutate(
    ["useUpgradeLicense"],
    upgradeLicenseFn,
    options,
  );
};

