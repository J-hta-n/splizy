import { supabase } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";
import { payloadSchema } from "./schema";

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
      { name: "Burger", quantity: 2, subtotal: 18.0 },
      { name: "Fries", quantity: 1, subtotal: 5.0 },
      { name: "Iced Tea", quantity: 3, subtotal: 9.0 },
    ],
    subtotal: 32.0,
    service_charge: 3.2,
    gst: 2.24,
    total: 37.44,
    currency: "USD",
  },
  last_indiv: [
    { user: "Alice", quantities: { "0": 1, "1": 1, "2": 1 } },
    { user: "Bob", quantities: { "0": 1, "2": 1 } },
  ],
  last_shared: [{ user: "Alice", quantities: { "2": 1 } }],
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
  const validation = payloadSchema.safeParse(body);
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
