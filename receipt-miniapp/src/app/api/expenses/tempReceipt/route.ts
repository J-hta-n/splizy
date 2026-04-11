import { env } from "@/lib/config";
import { NextResponse } from "next/server";
import { mockTempReceiptPayload } from "./mocks";
import { getTempReceipt } from "./get";
import { patchTempReceipt } from "./patch";

export const GET = env.MOCK_RECEIPTS_API
  ? () => {
      return NextResponse.json(mockTempReceiptPayload, { status: 200 });
    }
  : getTempReceipt;

export const PATCH = patchTempReceipt;
