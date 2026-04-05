import { ReceiptItem } from "@src/app/api/receipts/schema";

export type ItemSummary = {
  item: ReceiptItem;
  index: number;
  indivsQty: number;
  sharedQty: number;
  unitPrice: number;
};

export type ItemAssignments = Map<number, number>;

export type UserIndivSplit = {
  username: string;
  indivSplit: ItemAssignments;
};
