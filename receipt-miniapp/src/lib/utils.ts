import {
  IndividualAssignment,
  SharedAssignment,
} from "@/app/api/receipts/schema";

export const formatMoney = (value: number) => {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00";
};

export const clamp = (value: number, min: number, max: number) => {
  return Math.max(min, Math.min(max, value));
};

export const unique = (values: string[]) => {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
};

export const normalizeAssignments = (
  users: string[],
  existing: IndividualAssignment[] | SharedAssignment[] | null | undefined,
) => {
  return users.map((user) => {
    const found = existing?.find((entry) => entry.user === user);
    return {
      user,
      quantities: { ...(found?.quantities ?? {}) },
    };
  });
};
