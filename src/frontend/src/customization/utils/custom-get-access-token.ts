import { KLUISZ_ACCESS_TOKEN } from "@/constants/constants";
import { cookieManager } from "@/utils/cookie-manager";

export const customGetAccessToken = () => {
  return cookieManager.get(KLUISZ_ACCESS_TOKEN);
};
