import { NextRequest, NextResponse } from "next/server";
import { ParamsProps } from "./route";
import { splizyRepo } from "@/lib/db/repo";

export const getExpense = async (req: NextRequest, { params }: ParamsProps) => {
  const { id } = await params;
  const data = await splizyRepo.getExpenseById(id);
  return NextResponse.json(data, { status: 200 });
};
