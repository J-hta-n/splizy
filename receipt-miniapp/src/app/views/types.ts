import { ReceiptItem } from "../api/receipts/schema";

export type ItemSummary = {
  item: ReceiptItem;
  index: number;
  key: string;
  indivTotal: number;
  leftover: number;
  unitPrice: number;
};
