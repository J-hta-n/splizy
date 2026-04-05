import { z } from "zod";

export const itemSchema = z.object({
  name: z.string(),
  quantity: z.number(),
  subtotal: z.number().nullable(),
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

export const tempReceiptPayloadSchema = z.object({
  last_confirmation: z.boolean(),
  last_receipt: z.object({
    users: z.array(z.string()),
    receipt: receiptSchema,
  }),
});

export type ReceiptItem = z.infer<typeof itemSchema>;
export type Receipt = z.infer<typeof receiptSchema>;
export type TempReceiptPayload = z.infer<typeof tempReceiptPayloadSchema>;
