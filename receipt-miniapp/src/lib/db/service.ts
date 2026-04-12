import { PostExpenseSchema } from "@/app/api/expenses/schema";
import { splizyRepo } from "./repo";
import { PostExpensePayload } from "./model";
import { getPostExpensePayload } from "./utils";

export const updateElseCreateExpense = async (
  raw: PostExpenseSchema,
  id?: string,
) => {
  const payload: PostExpensePayload = getPostExpensePayload(raw);
  if (id) {
    return await splizyRepo.patchExpenseById(id, payload);
  } else {
    return await splizyRepo.postExpense(payload);
  }
};
