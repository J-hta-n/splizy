import { z } from "zod";

export const itemSchema = z.object({
  name: z.string(),
  quantity: z.number(),
  subtotal: z.number().nullable(),
});

export const receiptSchema = z.object({
  items: z.array(itemSchema),
  subtotal: z.number(),
  service_charge: z.number(),
  gst: z.number(),
  total: z.number(),
  currency: z.string(),
});

export const indivAssignmentSchema = z.array(
  z.object({
    user: z.string(),
    quantities: z.record(z.string(), z.number()),
  }),
);

export const sharedAssignmentSchema = z.array(
  z.object({
    user: z.string(),
    quantities: z.record(z.string(), z.number()),
  }),
);

export const payloadSchema = z.object({
  last_receipt: receiptSchema.optional(),
  last_indiv: indivAssignmentSchema.optional(),
  last_shared: sharedAssignmentSchema.optional(),
});

export type TReceipt = z.infer<typeof receiptSchema>;
export type TPayload = z.infer<typeof payloadSchema>;
