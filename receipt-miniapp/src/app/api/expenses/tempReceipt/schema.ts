import { z } from "zod";
import { receiptSchema } from "../schema";

// DTOs
export type { TempReceiptRow } from "@/lib/db/model";

// Post/patch schemas
const lastReceiptSchema = z.object({
  users: z.array(z.string()),
  receipt: receiptSchema,
});

export const patchTempReceiptSchema = z.object({
  title: z.string(),
  paid_by: z.string(),
  expense_id: z.string(),
  last_receipt: lastReceiptSchema,
});

export type PatchTempReceiptSchema = z.infer<typeof patchTempReceiptSchema>;
