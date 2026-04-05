import { supabase } from "@/lib/db";
import { env } from "@/lib/config";
import { NextRequest, NextResponse } from "next/server";
import { mockTempReceiptPayload } from "./mocks";
import { TempReceiptPayload, tempReceiptPayloadSchema } from "./schema";

export const getTempReceiptByGroupId = async (req: NextRequest) => {
  const group_id = req.nextUrl.searchParams.get("group_id");
  if (!group_id) {
    return NextResponse.json({ error: "Missing group_id" }, { status: 400 });
  }

  const { data, error } = await supabase
    .from("temp_receipts")
    .select("id, created_at, group_id, last_receipt, last_confirmation")
    .eq("group_id", group_id)
    .single();
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data, { status: 200 });
};

export const patchTempReceiptByGroupId = async (req: NextRequest) => {
  const group_id = req.nextUrl.searchParams.get("group_id");
  if (!group_id) {
    return NextResponse.json({ error: "Missing group_id" }, { status: 400 });
  }

  const body: TempReceiptPayload = await req.json();
  const validation = tempReceiptPayloadSchema.safeParse(body);
  if (!validation.success) {
    return NextResponse.json(
      { error: validation.error.message },
      { status: 400 },
    );
  }

  const { data, error } = await supabase
    .from("temp_receipts")
    .update(body)
    .eq("group_id", group_id)
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
