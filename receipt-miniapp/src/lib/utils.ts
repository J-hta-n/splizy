import { Receipt } from "@/app/api/receipts/schema";
import { UserIndivSplit } from "./types";

type UserAssignment = {
  user: string;
  quantities: Record<string, number>;
};

export const formatMoney = (value: number) => {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00";
};

export const clamp = (value: number, min: number, max: number) => {
  return Math.max(min, Math.min(max, value));
};

export const unique = (values: string[]) => {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
};

export const normalizeAssignments = (
  users: string[],
  existing: UserAssignment[] | null | undefined,
): UserAssignment[] => {
  return users.map((user) => {
    const found = existing?.find((entry) => entry.user === user);
    return {
      user,
      quantities: { ...(found?.quantities ?? {}) },
    };
  });
};

export const getUserIndivSplits = (
  receipt: Receipt,
  users: string[],
): UserIndivSplit[] => {
  return users.map((username) => {
    const indivSplit: Record<string, number> = {};

    for (const item of receipt.items) {
      for (const entry of item.indiv) {
        if (entry.username !== username) continue;
        indivSplit[item.name] = entry.quantity;
      }
    }

    return {
      username,
      indivSplit,
    };
  });
};
