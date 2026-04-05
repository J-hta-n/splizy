import { Receipt } from "@/app/api/receipts/schema";
import { UserIndivSplit } from "./types";

export const formatMoney = (value: number) => {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00";
};

export const clamp = (value: number, min: number, max: number) => {
  return Math.max(min, Math.min(max, value));
};

export const unique = (values: string[]) => {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
};

export const getUserIndivSplits = (
  receipt: Receipt,
  users: string[],
): UserIndivSplit[] => {
  return users.map((username) => {
    const indivSplit: Map<number, number> = new Map();

    for (const [idx, item] of receipt.items.entries()) {
      for (const entry of item.indiv) {
        if (entry.username !== username) continue;
        indivSplit.set(idx, entry.quantity);
      }
    }

    return {
      username,
      indivSplit,
    };
  });
};
