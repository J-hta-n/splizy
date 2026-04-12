import { patchTempReceipt } from "@/app/api/expenses/tempReceipt/patch";
import { supabase } from "./db";
import {
  Expense,
  PatchTempReceiptPayload,
  PostExpensePayload,
  TempReceiptRow,
} from "./model";

export const splizyRepo = {
  getExpenseById: async (expenseId: string): Promise<Expense> => {
    const { data, error } = await supabase
      .from("expenses")
      .select("*")
      .eq("id", expenseId)
      .single();

    if (error || !data) {
      throw new Error(error?.message || "Expense not found");
    }

    return data as Expense;
  },
  postExpense: async (expense: PostExpensePayload): Promise<Expense> => {
    const { data, error } = await supabase
      .from("expenses")
      .insert(expense)
      .select()
      .single();

    if (error || !data) {
      throw new Error(error?.message || "Failed to create expense");
    }

    return data as Expense;
  },
  patchExpenseById: async (
    expenseId: string,
    expense: PostExpensePayload,
  ): Promise<Expense> => {
    const { data, error } = await supabase
      .from("expenses")
      .update(expense)
      .eq("id", expenseId)
      .select()
      .single();

    if (error || !data) {
      throw new Error(error?.message || "Failed to update expense");
    }

    return data as Expense;
  },
  getTempReceiptByGroupId: async (groupId: string): Promise<TempReceiptRow> => {
    const { data, error } = await supabase
      .from("temp_receipts")
      .select("*")
      .eq("group_id", groupId)
      .single();

    if (error || !data) {
      throw new Error(error?.message || "Temp receipt not found");
    }

    return data as TempReceiptRow;
  },
  patchTempReceiptByGroupId: async (
    groupId: string,
    payload: PatchTempReceiptPayload,
  ): Promise<TempReceiptRow> => {
    const { data, error } = await supabase
      .from("temp_receipts")
      .update(payload)
      .eq("group_id", groupId)
      .select()
      .single();

    if (error || !data) {
      throw new Error(error?.message || "Failed to update temp receipt");
    }

    return data as TempReceiptRow;
  },
};
