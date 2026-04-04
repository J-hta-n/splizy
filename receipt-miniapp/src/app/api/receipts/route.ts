import { supabase } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";
import { receiptBillSplitSchema } from "./schema";

const isMockReceiptsApiEnabled = () => {
  const value = process.env.MOCK_RECEIPTS_API?.toLowerCase();
  return value === "1" || value === "true" || value === "yes" || value === "on";
};

let mockGroupReceipt = {
  id: 1,
  created_at: "2026-04-04T00:00:00.000Z",
  group_id: 123,
  last_receipt: {
    items: [
      {
        name: "Hong Kong Milk Tea (Cold)",
        quantity: 4,
        subtotal: 14.0,
      },
      {
        name: "Honey Sea Coconut with Longan",
        quantity: 1,
        subtotal: 3.5,
      },
      { name: "BBQ Pork Rice", quantity: 1, subtotal: 3.5 },
      { name: "Char Siew Bao", quantity: 1, subtotal: 2.9 },
      { name: "Red Bean Paste Bao", quantity: 1, subtotal: 2.1 },
      { name: "Mango with Pomelo & Sago", quantity: 1, subtotal: 4.8 },
      { name: "Hong Kong Style Milk Tea", quantity: 1, subtotal: 6.8 },
      { name: "Red Bean Paste Pancake", quantity: 1, subtotal: 4.8 },
      { name: "Grass Jelly Drink", quantity: 1, subtotal: 2.7 },
      { name: "Yam Paste w/ Ginkgo Nut", quantity: 1, subtotal: 4.5 },
      {
        name: "Sweet Potato Salted Egg Custard Ball",
        quantity: 1,
        subtotal: 3.8,
      },
      { name: "Siew Mai", quantity: 3, subtotal: 8.7 },
      { name: "Har Gow", quantity: 3, subtotal: 12.6 },
      { name: "Rice Roll with Prawn", quantity: 1, subtotal: 5.0 },
      {
        name: "Bean Curd Prawn Roll",
        quantity: 3,
        subtotal: 12.6,
      },
      { name: "Fried Prawn Dumpling", quantity: 1, subtotal: 5.4 },
      { name: "Water Chestnut Drink", quantity: 1, subtotal: 2.7 },
      { name: "Xiao Long Bao", quantity: 1, subtotal: 5.9 },
      { name: "Spring Roll", quantity: 1, subtotal: 2.8 },
      {
        name: "Salted Egg Yolk Custard Bao (Fried)",
        quantity: 1,
        subtotal: 6.0,
      },
      { name: "Glutinous Rice with Chicken", quantity: 1, subtotal: 3.5 },
      { name: "Portuguese Egg Tart", quantity: 1, subtotal: 4.4 },
      {
        name: "Prawn Hor Fun in Creamy Egg Sauce",
        quantity: 1,
        subtotal: 8.8,
      },
      { name: "Barley Drink", quantity: 1, subtotal: 2.7 },
    ],
    subtotal: 134.5,
    service_charge: 13.45,
    gst: 13.32,
    total: 161.27,
    currency: "SGD",
  },
  last_indiv: [
    { user: "User 1", quantities: {} },
    { user: "User 2", quantities: {} },
    { user: "User 3", quantities: {} },
    { user: "User 4", quantities: {} },
    { user: "User 5", quantities: {} },
    { user: "User 6", quantities: {} },
  ],
  last_shared: [
    { user: "User 1", quantities: {} },
    { user: "User 2", quantities: {} },
    { user: "User 3", quantities: {} },
    { user: "User 4", quantities: {} },
    { user: "User 5", quantities: {} },
    { user: "User 6", quantities: {} },
  ],
  last_confirmation: false,
};

export const GET = async (req: NextRequest) => {
  const group_id = req.nextUrl.searchParams.get("group_id");
  if (!group_id) {
    return NextResponse.json({ error: "Missing group_id" }, { status: 400 });
  }

  if (isMockReceiptsApiEnabled()) {
    return NextResponse.json(
      {
        ...mockGroupReceipt,
        group_id: Number.isFinite(Number(group_id))
          ? Number(group_id)
          : mockGroupReceipt.group_id,
      },
      { status: 200 },
    );
  }

  if (!supabase) {
    return NextResponse.json(
      {
        error: "Database is not configured. Set SUPABASE_URL and SUPABASE_KEY.",
      },
      { status: 500 },
    );
  }

  const { data, error } = await supabase
    .from("group_receipts")
    .select(
      "id, created_at, group_id, last_receipt, last_indiv, last_shared, last_confirmation",
    )
    .eq("group_id", group_id)
    .single();
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data, { status: 200 });
};

export const PATCH = async (req: NextRequest) => {
  const group_id = req.nextUrl.searchParams.get("group_id");
  if (!group_id) {
    return NextResponse.json({ error: "Missing group_id" }, { status: 400 });
  }

  const body = await req.json();
  const validation = receiptBillSplitSchema.safeParse(body);
  if (!validation.success) {
    return NextResponse.json(
      { error: validation.error.message },
      { status: 400 },
    );
  }

  const updatePayload: Record<string, unknown> = {};
  if (body.last_receipt !== undefined)
    updatePayload.last_receipt = body.last_receipt;
  if (body.last_indiv !== undefined) updatePayload.last_indiv = body.last_indiv;
  if (body.last_shared !== undefined)
    updatePayload.last_shared = body.last_shared;

  if (Object.keys(updatePayload).length === 0) {
    return NextResponse.json(
      { error: "No valid update fields provided" },
      { status: 400 },
    );
  }

  if (isMockReceiptsApiEnabled()) {
    mockGroupReceipt = {
      ...mockGroupReceipt,
      ...updatePayload,
      group_id: Number.isFinite(Number(group_id))
        ? Number(group_id)
        : mockGroupReceipt.group_id,
    };
    return NextResponse.json(mockGroupReceipt, { status: 200 });
  }

  if (!supabase) {
    return NextResponse.json(
      {
        error: "Database is not configured. Set SUPABASE_URL and SUPABASE_KEY.",
      },
      { status: 500 },
    );
  }

  const { data, error } = await supabase
    .from("group_receipts")
    .update(updatePayload)
    .eq("group_id", group_id)
    .select()
    .single();
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data, { status: 200 });
};
