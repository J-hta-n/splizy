import { ReceiptItem } from "@src/app/api/receipts/schema";

export type ItemSummary = {
  item: ReceiptItem;
  index: number;
  key: string;
  indivTotal: number;
  leftover: number;
  unitPrice: number;
};

export type ItemAssignments = Record<string, number>;

export type UserIndivSplit = {
  username: string;
  indivSplit: ItemAssignments;
};
