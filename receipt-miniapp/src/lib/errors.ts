import { NextResponse } from "next/server";

export const validationError = (message: string) => {
  return NextResponse.json({ error: message }, { status: 400 });
};
