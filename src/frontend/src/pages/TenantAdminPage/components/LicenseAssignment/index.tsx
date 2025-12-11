import { useState } from "react";
import { 
  UserPlus, 
  UserMinus, 
  ArrowUp, 
  ArrowDown,
  Search,
  CreditCard,
  MoreVertical,
  Loader2,
  AlertCircle,
  Sparkles
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  useAssignLicense,
  useUnassignLicense,
  useUpgradeLicense,
  useGetMyTenantPools,
  useListLicenseTiers,
} from "@/controllers/API/queries/licensing";
import { useGetTenantUsers } from "@/controllers/API/queries/tenants";
import useAlertStore from "@/stores/alertStore";
import useAuthStore from "@/stores/authStore";
import { cn } from "@/utils/utils";

export default function LicenseAssignment() {
  const { tenantId, isTenantAdmin, isSuperAdmin } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [isAssignDialogOpen, setIsAssignDialogOpen] = useState(false);
  const [isUpgradeDialogOpen, setIsUpgradeDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [selectedTier, setSelectedTier] = useState<string>("");
  const [preserveCredits, setPreserveCredits] = useState(true);

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const canAccessLicenseData = isTenantAdmin || isSuperAdmin;
  const { data: users, isLoading: usersLoading, refetch: refetchUsers } = useGetTenantUsers(tenantId || "");
  const { data: pools, refetch: refetchPools } = useGetMyTenantPools({ enabled: canAccessLicenseData });
  const { data: tiers } = useListLicenseTiers({ enabled: canAccessLicenseData });

  const assignLicense = useAssignLicense({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License assigned successfully"] });
      setIsAssignDialogOpen(false);
      setSelectedUser(null);
      setSelectedTier("");
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to assign license"],
      });
    },
  });

  const unassignLicense = useUnassignLicense({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License unassigned successfully"] });
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to unassign license"],
      });
    },
  });

  const upgradeLicense = useUpgradeLicense({
    onSuccess: () => {
      setSuccessData({ title: "Success", list: ["License upgraded successfully"] });
      setIsUpgradeDialogOpen(false);
      setSelectedUser(null);
      setSelectedTier("");
      refetchUsers();
      refetchPools();
    },
    onError: (error: any) => {
      setErrorData({
        title: "Error",
        list: [error?.response?.data?.detail || "Failed to upgrade license"],
      });
    },
  });

  const handleAssign = () => {
    if (!selectedUser || !selectedTier) {
      setErrorData({ title: "Error", list: ["Please select both user and tier"] });
      return;
    }
    assignLicense.mutate({ user_id: selectedUser.id, tier_id: selectedTier });
  };

  const handleUnassign = (user: any) => {
    if (window.confirm(`Remove license from "${user.username}"? They will lose access to licensed features.`)) {
      unassignLicense.mutate(user.id);
    }
  };

  const handleUpgrade = () => {
    if (!selectedUser || !selectedTier) {
      setErrorData({ title: "Error", list: ["Please select both user and tier"] });
      return;
    }
    upgradeLicense.mutate({
      user_id: selectedUser.id,
      new_tier_id: selectedTier,
      preserve_credits: preserveCredits,
    });
  };

  const getTierName = (tierId?: string) => {
    if (!tierId) return "No License";
    return tiers?.find((t) => t.id === tierId)?.name || tierId;
  };

  const getTierInfo = (tierId?: string) => {
    if (!tierId) return null;
    return tiers?.find((t) => t.id === tierId);
  };

  const getAvailableCount = (tierId: string) => {
    return pools?.[tierId]?.available_count || 0;
  };

  const getCreditsPercentage = (user: any) => {
    if (!user.credits_allocated || user.credits_allocated === 0) return 0;
    return Math.round(((user.credits_allocated - user.credits_used) / user.credits_allocated) * 100);
  };

  const filteredUsers = users?.filter(
    (user: any) => user.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const usersWithLicense = users?.filter((u: any) => u.license_is_active) || [];
  const usersWithoutLicense = users?.filter((u: any) => !u.license_is_active) || [];

  return (
    <div className="space-y-6">
      {/* Header with Search and Action */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" />
                User License Management
              </CardTitle>
              <CardDescription>
                Assign, upgrade, or remove licenses for users in your organization
              </CardDescription>
            </div>
            <Button 
              onClick={() => setIsAssignDialogOpen(true)}
              disabled={usersWithoutLicense.length === 0}
            >
              <UserPlus className="h-4 w-4 mr-2" />
              Assign License
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardContent className="pt-6">
          {usersLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredUsers?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                {searchQuery ? "No users match your search" : "No users found"}
              </p>
            </div>
          ) : (
            <div className="rounded-lg border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead className="w-[250px]">User</TableHead>
                    <TableHead>License Tier</TableHead>
                    <TableHead>Credits</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers?.map((user: any) => (
                    <TableRow key={user.id} className="group hover:bg-muted/30">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "h-9 w-9 rounded-full flex items-center justify-center text-sm font-medium",
                            user.license_is_active 
                              ? "bg-primary/10 text-primary" 
                              : "bg-muted text-muted-foreground"
                          )}>
                            {user.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{user.username}</p>
                            <div className="flex items-center gap-1">
                              {user.is_tenant_admin && (
                                <Badge variant="secondary" className="text-xs py-0 px-1">
                                  Admin
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {user.license_is_active ? (
                          <div className="flex items-center gap-2">
                            <Sparkles className="h-4 w-4 text-amber-500" />
                            <span className="font-medium">{getTierName(user.license_tier_id)}</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {user.license_is_active ? (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="w-[140px]">
                                  <div className="flex items-center justify-between text-xs mb-1">
                                    <span className="font-medium">
                                      {(user.credits_allocated - user.credits_used).toLocaleString()}
                                    </span>
                                    <span className="text-muted-foreground">
                                      / {user.credits_allocated.toLocaleString()}
                                    </span>
                                  </div>
                                  <Progress 
                                    value={getCreditsPercentage(user)} 
                                    className={cn(
                                      "h-2",
                                      getCreditsPercentage(user) < 20 && "[&>div]:bg-amber-500",
                                      getCreditsPercentage(user) < 10 && "[&>div]:bg-destructive"
                                    )}
                                  />
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <div className="space-y-1">
                                  <p>{getCreditsPercentage(user)}% remaining</p>
                                  {user.credits_per_month && (
                                    <p className="text-xs text-muted-foreground">
                                      +{user.credits_per_month.toLocaleString()}/month
                                    </p>
                                  )}
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={user.license_is_active ? "default" : "secondary"}>
                          {user.license_is_active ? "Licensed" : "Unlicensed"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {user.license_is_active ? (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-[180px]">
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedUser(user);
                                  setIsUpgradeDialogOpen(true);
                                }}
                              >
                                <ArrowUp className="h-4 w-4 mr-2" />
                                Upgrade License
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedUser(user);
                                  setIsUpgradeDialogOpen(true);
                                }}
                              >
                                <ArrowDown className="h-4 w-4 mr-2" />
                                Downgrade License
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleUnassign(user)}
                                className="text-destructive focus:text-destructive"
                              >
                                <UserMinus className="h-4 w-4 mr-2" />
                                Remove License
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedUser(user);
                              setIsAssignDialogOpen(true);
                            }}
                          >
                            <UserPlus className="h-3.5 w-3.5 mr-1" />
                            Assign
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Assign License Dialog */}
      <Dialog open={isAssignDialogOpen} onOpenChange={setIsAssignDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Assign License</DialogTitle>
            <DialogDescription>
              {selectedUser 
                ? `Assign a license to ${selectedUser.username}`
                : "Select a user and license tier to assign"
              }
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {!selectedUser && (
              <div className="grid gap-2">
                <Label>User *</Label>
                <Select 
                  value={selectedUser?.id || ""} 
                  onValueChange={(value) => setSelectedUser(usersWithoutLicense.find((u: any) => u.id === value))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a user" />
                  </SelectTrigger>
                  <SelectContent>
                    {usersWithoutLicense.map((user: any) => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="grid gap-2">
              <Label>License Tier *</Label>
              <Select value={selectedTier} onValueChange={setSelectedTier}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a tier" />
                </SelectTrigger>
                <SelectContent>
                  {tiers?.filter((t) => t.is_active).map((tier) => {
                    const available = getAvailableCount(tier.id);
                    return (
                      <SelectItem 
                        key={tier.id} 
                        value={tier.id}
                        disabled={available === 0}
                      >
                        <div className="flex items-center justify-between w-full gap-2">
                          <span>{tier.name}</span>
                          <Badge 
                            variant={available > 0 ? "secondary" : "destructive"}
                            className="text-xs"
                          >
                            {available} available
                          </Badge>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
            {selectedTier && (
              <div className="rounded-lg border p-4 bg-muted/50 space-y-2">
                <h4 className="font-medium text-sm">Tier Benefits</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Initial Credits</span>
                    <span className="font-medium">
                      {getTierInfo(selectedTier)?.default_credits?.toLocaleString()}
                    </span>
                  </div>
                  {getTierInfo(selectedTier)?.default_credits_per_month && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Monthly Credits</span>
                      <span className="font-medium">
                        +{getTierInfo(selectedTier)?.default_credits_per_month?.toLocaleString()}/mo
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsAssignDialogOpen(false);
              setSelectedUser(null);
              setSelectedTier("");
            }}>
              Cancel
            </Button>
            <Button 
              onClick={handleAssign}
              disabled={!selectedTier || assignLicense.isPending}
            >
              {assignLicense.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Assigning...
                </>
              ) : (
                "Assign License"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upgrade/Downgrade Dialog */}
      <Dialog open={isUpgradeDialogOpen} onOpenChange={setIsUpgradeDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Change License Tier</DialogTitle>
            <DialogDescription>
              Update {selectedUser?.username}'s license tier
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {selectedUser && (
              <div className="rounded-lg border p-4 bg-blue-500/5 border-blue-500/20">
                <h4 className="font-medium text-blue-600 mb-2">Current License</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tier</span>
                    <span className="font-medium">{getTierName(selectedUser.license_tier_id)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Credits Remaining</span>
                    <span className="font-medium">
                      {(selectedUser.credits_allocated - selectedUser.credits_used).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div className="grid gap-2">
              <Label>New License Tier *</Label>
              <Select value={selectedTier} onValueChange={setSelectedTier}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a tier" />
                </SelectTrigger>
                <SelectContent>
                  {tiers?.filter((t) => t.is_active && t.id !== selectedUser?.license_tier_id).map((tier) => {
                    const available = getAvailableCount(tier.id);
                    return (
                      <SelectItem 
                        key={tier.id} 
                        value={tier.id}
                        disabled={available === 0}
                      >
                        <div className="flex items-center justify-between w-full gap-2">
                          <span>{tier.name}</span>
                          <Badge 
                            variant={available > 0 ? "secondary" : "destructive"}
                            className="text-xs"
                          >
                            {available} available
                          </Badge>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <Label htmlFor="preserve-credits">Preserve Credits</Label>
                <p className="text-xs text-muted-foreground">
                  Add remaining credits to the new tier's allocation
                </p>
              </div>
              <Switch
                id="preserve-credits"
                checked={preserveCredits}
                onCheckedChange={setPreserveCredits}
              />
            </div>
            {selectedTier && (
              <div className="rounded-lg border p-4 bg-green-500/5 border-green-500/20">
                <h4 className="font-medium text-green-600 mb-2">New License</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">New Tier</span>
                    <span className="font-medium">{getTierInfo(selectedTier)?.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">New Credits</span>
                    <span className="font-medium">
                      {preserveCredits && selectedUser
                        ? `${selectedUser.credits_allocated - selectedUser.credits_used} + ${getTierInfo(selectedTier)?.default_credits}`
                        : getTierInfo(selectedTier)?.default_credits?.toLocaleString()
                      }
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsUpgradeDialogOpen(false);
              setSelectedUser(null);
              setSelectedTier("");
            }}>
              Cancel
            </Button>
            <Button 
              onClick={handleUpgrade}
              disabled={!selectedTier || upgradeLicense.isPending}
            >
              {upgradeLicense.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                "Update License"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
