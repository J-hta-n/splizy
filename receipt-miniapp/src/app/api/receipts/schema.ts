import { z } from "zod";

export const itemSchema = z.object({
  name: z.string(),
  quantity: z.number(),
  subtotal: z.number(),
  indiv: z.array(z.object({ username: z.string(), quantity: z.number() })),
  shared: z.array(z.string()),
});

export const receiptSchema = z.object({
  items: z.array(itemSchema),
  subtotal: z.number(),
  service_charge: z.number(),
  gst: z.number(),
  total: z.number(),
  currency: z.string(),
});

export const lastReceiptSchema = z.object({
  users: z.array(z.string()),
  receipt: receiptSchema,
});

export const tempReceiptSubmitPayloadSchema = z.object({
  title: z.string(),
  paid_by: z.string(),
  last_receipt: lastReceiptSchema,
});

export const tempReceiptRowSchema = z.object({
  id: z.number().optional(),
  created_at: z.string().optional(),
  group_id: z.union([z.number(), z.string()]).nullable().optional(),
  title: z.string().nullable().optional(),
  paid_by: z.string().nullable().optional(),
  expense_id: z.string().uuid().nullable().optional(),
  last_receipt: lastReceiptSchema.nullable().optional(),
});

export type ReceiptItem = z.infer<typeof itemSchema>;
export type Receipt = z.infer<typeof receiptSchema>;
export type LastReceipt = z.infer<typeof lastReceiptSchema>;
export type TempReceiptSubmitPayload = z.infer<
  typeof tempReceiptSubmitPayloadSchema
>;
export type TempReceiptRow = z.infer<typeof tempReceiptRowSchema>;
