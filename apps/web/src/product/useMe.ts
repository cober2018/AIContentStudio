// 统一的当前用户查询：全站共享同一 queryKey，切面板/页面不再重复打 /users/me
import { useQuery } from "@tanstack/react-query";
import { api, currentUser } from "../api";

export interface Me {
  role: string;
  id?: number;
  email?: string;
}

export function useMe() {
  return useQuery({
    queryKey: ["users", "me", currentUser()],
    queryFn: () => api.get<Me>("/users/me"),
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000,
  });
}
