import { NextRequest, NextResponse } from "next/server";
import { ParamsProps } from "./route";
import { PostExpenseSchema, postExpenseSchema } from "../schema";
import { updateElseCreateExpense } from "@/lib/db/service";
import { validationError } from "@/lib/errors";

export const patchExpense = async (
  req: NextRequest,
  { params }: ParamsProps,
) => {
  const { id } = await params;
  const body: PostExpenseSchema = await req.json();
  const validation = postExpenseSchema.safeParse(body);
  if (!validation.success) {
    return validationError(validation.error.message);
  }

  const updatedExpense = await updateElseCreateExpense(body, id);
  return NextResponse.json(updatedExpense, { status: 200 });
};
