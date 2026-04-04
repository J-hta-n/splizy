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

export const indivAssignmentSchema = z.object({
  user: z.string(),
  quantities: z.record(z.string(), z.number()),
});

export const sharedAssignmentSchema = z.object({
  user: z.string(),
  quantities: z.record(z.string(), z.number()),
});

export const receiptBillSplitSchema = z.object({
  last_receipt: receiptSchema.optional(),
  last_indiv: z.array(indivAssignmentSchema).optional(),
  last_shared: z.array(sharedAssignmentSchema).optional(),
});

export type ReceiptItem = z.infer<typeof itemSchema>;
export type Receipt = z.infer<typeof receiptSchema>;
export type IndividualAssignment = z.infer<typeof indivAssignmentSchema>;
export type SharedAssignment = z.infer<typeof sharedAssignmentSchema>;
export type ReceiptBillSplit = z.infer<typeof receiptBillSplitSchema>;
