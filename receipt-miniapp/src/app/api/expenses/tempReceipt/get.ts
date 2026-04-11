import { splizyRepo } from "@/lib/db/repo";
import { validationError } from "@/lib/errors";
import { NextRequest, NextResponse } from "next/server";

export const getTempReceipt = async (req: NextRequest) => {
  const group_id = req.nextUrl.searchParams.get("group_id");
  if (!group_id) {
    return validationError("group_id is required");
  }

  const data = await splizyRepo.getTempReceiptByGroupId(group_id);
  return NextResponse.json(data, { status: 200 });
};
