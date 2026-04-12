import { getExpense } from "./get";
import { patchExpense } from "./patch";

export interface ParamsProps {
  params: Promise<{ id: string }>;
}

export const GET = getExpense;
export const PATCH = patchExpense;
