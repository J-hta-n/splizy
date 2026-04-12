import { NextRequest, NextResponse } from "next/server";
import { postExpenseSchema, PostExpenseSchema } from "./schema";
import { validationError } from "@/lib/errors";
import { updateElseCreateExpense } from "@/lib/db/service";

export const createExpense = async (req: NextRequest) => {
  const body: PostExpenseSchema = await req.json();
  const validation = postExpenseSchema.safeParse(body);
  if (!validation.success) {
    return validationError(validation.error.message);
  }

  const newExpense = await updateElseCreateExpense(body);
  return NextResponse.json({ expense: newExpense }, { status: 201 });
};
