import { getItemIndivsQty } from "../utils";
import { Payee, PostExpensePayload, Receipt } from "./model";
import { PostExpenseSchema } from "@/app/api/expenses/schema";

export const getPayeesFromReceipt = (
  users: string[],
  receipt: Receipt,
): Payee[] => {
  const spendByUser: Record<string, number> = {};
  for (const user of users) {
    spendByUser[user] = 0;
  }

  for (const item of receipt.items) {
    if (item.quantity <= 0) continue;

    const unitPrice = item.subtotal / item.quantity;

    for (const entry of item.indiv) {
      spendByUser[entry.username] += unitPrice * entry.quantity;
    }

    const indivsQty = getItemIndivsQty(item);
    const sharedQty = Math.max(0, item.quantity - indivsQty);
    const sharedUsers = item.shared;

    const amountPerUser = (unitPrice * sharedQty) / sharedUsers.length;
    for (const user of sharedUsers) {
      spendByUser[user] += amountPerUser;
    }
  }

  const factor = receipt.subtotal > 0 ? receipt.total / receipt.subtotal : 0;
  for (const user of users) {
    spendByUser[user] *= factor;
  }

  return Object.entries(spendByUser).map(([user, amount]) => ({
    user,
    amount,
  }));
};

export const getPostExpensePayload = (
  raw: PostExpenseSchema,
): PostExpensePayload => {
  return {
    title: raw.title,
    paid_by: raw.paid_by,
    group_id: raw.group_id,
    currency: raw.receipt.currency,
    amount: raw.receipt.total,
    is_equal_split: false,
    multiplier: undefined,
    payees: getPayeesFromReceipt(raw.users, raw.receipt),
    receipt: raw.receipt,
  };
};
