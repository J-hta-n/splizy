import { ReceiptItem } from "@/app/api/expenses/schema";

export type ItemSummary = {
  item: ReceiptItem;
  index: number;
  indivsQty: number;
  sharedQty: number;
  unitPrice: number;
};

// Map of <item index : item quantity> assigned to a user
export type ItemAssignments = Map<number, number>;

export type UserIndivSplit = {
  username: string;
  indivSplit: ItemAssignments;
};
