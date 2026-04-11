import { validationError } from "@/lib/errors";
import { PatchTempReceiptSchema, patchTempReceiptSchema } from "./schema";
import { NextRequest, NextResponse } from "next/server";
import { splizyRepo } from "@/lib/db/repo";

export const patchTempReceipt = async (req: NextRequest) => {
  const group_id = req.nextUrl.searchParams.get("group_id");
  if (!group_id) {
    return validationError("group_id is required");
  }

  const body: PatchTempReceiptSchema = await req.json();
  const validation = patchTempReceiptSchema.safeParse(body);
  if (!validation.success) {
    return validationError(validation.error.message);
  }

  const data = await splizyRepo.patchTempReceiptByGroupId(group_id, body);
  return NextResponse.json(data, { status: 200 });
};
