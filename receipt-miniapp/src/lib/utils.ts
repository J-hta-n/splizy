import { Receipt, ReceiptItem } from "@/app/api/receipts/schema";
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

export const getItemIndivsQty = (item: ReceiptItem) =>
  item.indiv.reduce((sum, entry) => sum + entry.quantity, 0);

export const normaliseSharedItems = (receipt: Receipt, users: string[]) => {
  return receipt.items.map((item) => {
    const indivsQty = getItemIndivsQty(item);
    const sharedQty = Math.max(0, item.quantity - indivsQty);
    const validSharedUsers = item.shared.filter((user) => users.includes(user));
    let normalizedShared: string[] = [];
    if (sharedQty > 0) {
      if (validSharedUsers.length === 0) {
        normalizedShared = [...users];
      } else if (validSharedUsers.length >= 2) {
        normalizedShared = validSharedUsers;
      }
    }

    return {
      ...item,
      shared: normalizedShared,
    };
  });
};

export const getSpendingByUserIncludingCharges = (
  receipt: Receipt,
  users: string[],
) => {
  const spendByUser: Record<string, number> = {};
  for (const user of users) {
    spendByUser[user] = 0;
  }

  for (const item of receipt.items) {
    if (item.quantity <= 0) continue;

    const unitPrice = item.subtotal / item.quantity;

    for (const entry of item.indiv) {
      if (!(entry.username in spendByUser)) continue;
      spendByUser[entry.username] += unitPrice * entry.quantity;
    }

    const indivsQty = getItemIndivsQty(item);
    const sharedQty = Math.max(0, item.quantity - indivsQty);
    const sharedUsers = item.shared.filter((user) => users.includes(user));
    if (sharedQty <= 0 || sharedUsers.length < 2) continue;

    const amountPerUser = (unitPrice * sharedQty) / sharedUsers.length;
    for (const user of sharedUsers) {
      spendByUser[user] += amountPerUser;
    }
  }

  const factor = receipt.subtotal > 0 ? receipt.total / receipt.subtotal : 0;
  for (const user of users) {
    spendByUser[user] *= factor;
  }

  return spendByUser;
};
