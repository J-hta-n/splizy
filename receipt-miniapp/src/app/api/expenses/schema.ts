import { z } from "zod";

// DTOs
export type { ReceiptItem } from "@/lib/db/model";
export type { Receipt } from "@/lib/db/model";
export type { Expense } from "@/lib/db/model";

// Post/patch schemas
const receiptItemSchema = z.object({
  name: z.string(),
  quantity: z.number(),
  subtotal: z.number(),
  indiv: z.array(z.object({ username: z.string(), quantity: z.number() })),
  shared: z.array(z.string()),
});

export const receiptSchema = z.object({
  items: z.array(receiptItemSchema),
  subtotal: z.number(),
  service_charge: z.number(),
  gst: z.number(),
  total: z.number(),
  currency: z.string(),
});

export const postExpenseSchema = z.object({
  group_id: z.number(),
  title: z.string(),
  paid_by: z.string(),
  users: z.array(z.string()),
  receipt: receiptSchema,
});

export type PostExpenseSchema = z.infer<typeof postExpenseSchema>;
