import { supabase } from "@/lib/db";
import { env } from "@/lib/config";
import { NextRequest, NextResponse } from "next/server";
import { mockTempReceiptPayload } from "./mocks";
import {
  TempReceiptSubmitPayload,
  tempReceiptSubmitPayloadSchema,
} from "./schema";
import {
  getSpendingByUserIncludingCharges,
  normaliseSharedItems,
} from "@/lib/utils";

export const getTempReceiptByGroupId = async (req: NextRequest) => {
  const group_id = req.nextUrl.searchParams.get("group_id");
  if (!group_id) {
    return NextResponse.json({ error: "Missing group_id" }, { status: 400 });
  }

  const numericGroupId = Number(group_id);
  if (!Number.isFinite(numericGroupId)) {
    return NextResponse.json({ error: "Invalid group_id" }, { status: 400 });
  }

  const { data, error } = await supabase
    .from("temp_receipts")
    .select(
      "id, created_at, group_id, title, paid_by, expense_id, last_receipt",
    )
    .eq("group_id", numericGroupId)
    .order("created_at", { ascending: false })
    .limit(1);
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  if (!data || data.length === 0) {
    return NextResponse.json({ error: "Receipt not found" }, { status: 404 });
  }

  return NextResponse.json(data[0], { status: 200 });
};

export const patchTempReceiptByGroupId = async (req: NextRequest) => {
  const group_id = req.nextUrl.searchParams.get("group_id");
  if (!group_id) {
    return NextResponse.json({ error: "Missing group_id" }, { status: 400 });
  }

  const numericGroupId = Number(group_id);
  if (!Number.isFinite(numericGroupId)) {
    return NextResponse.json({ error: "Invalid group_id" }, { status: 400 });
  }

  const body: TempReceiptSubmitPayload = await req.json();
  const validation = tempReceiptSubmitPayloadSchema.safeParse(body);
  if (!validation.success) {
    return NextResponse.json(
      { error: validation.error.message },
      { status: 400 },
    );
  }

  const normalizedReceipt = {
    ...body.last_receipt.receipt,
    items: normaliseSharedItems(
      body.last_receipt.receipt,
      body.last_receipt.users,
    ),
  };

  const spendByUser = getSpendingByUserIncludingCharges(
    normalizedReceipt,
    body.last_receipt.users,
  );

  const { data: latestTempRows, error: latestTempError } = await supabase
    .from("temp_receipts")
    .select("id")
    .eq("group_id", numericGroupId)
    .order("created_at", { ascending: false })
    .limit(1);

  if (latestTempError) {
    return NextResponse.json(
      { error: latestTempError.message },
      { status: 500 },
    );
  }

  if (!latestTempRows || latestTempRows.length === 0) {
    return NextResponse.json({ error: "Receipt not found" }, { status: 404 });
  }

  const latestTempId = latestTempRows[0].id;

  const expenseEntry = {
    group_id: numericGroupId,
    title: body.title,
    amount: String(normalizedReceipt.total),
    paid_by: body.paid_by,
    currency: normalizedReceipt.currency,
    is_equal_split: false,
    multiplier: null,
  };

  const { data: expenseData, error: expenseError } = await supabase
    .from("expenses")
    .insert(expenseEntry)
    .select("id")
    .single();

  if (expenseError || !expenseData) {
    return NextResponse.json(
      { error: expenseError?.message || "Failed to create expense" },
      { status: 500 },
    );
  }

  const expenseId = expenseData.id;

  const userExpenses = body.last_receipt.users.map((username) => ({
    username,
    group_id: numericGroupId,
    expense_id: expenseId,
    amount: String(spendByUser[username] ?? 0),
  }));

  const { error: userExpensesError } = await supabase
    .from("user_expenses")
    .insert(userExpenses);

  if (userExpensesError) {
    await supabase.from("expenses").delete().eq("id", expenseId);
    return NextResponse.json(
      { error: userExpensesError.message },
      { status: 500 },
    );
  }

  const { data, error } = await supabase
    .from("temp_receipts")
    .update({
      title: body.title,
      paid_by: body.paid_by,
      expense_id: expenseId,
      last_receipt: {
        users: body.last_receipt.users,
        receipt: normalizedReceipt,
      },
    })
    .eq("id", latestTempId)
    .select()
    .single();
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data, { status: 200 });
};

export const GET = env.MOCK_RECEIPTS_API
  ? () => {
      return NextResponse.json(mockTempReceiptPayload, { status: 200 });
    }
  : getTempReceiptByGroupId;

export const PATCH = env.MOCK_RECEIPTS_API
  ? () => {
      return NextResponse.json(mockTempReceiptPayload, { status: 200 });
    }
  : patchTempReceiptByGroupId;
