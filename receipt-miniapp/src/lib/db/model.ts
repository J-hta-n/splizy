// Db schema DTOs

export type ReceiptItem = {
  name: string;
  quantity: number;
  subtotal: number;
  indiv: { username: string; quantity: number }[];
  shared: string[];
};

export type Payee = {
  user: string;
  amount: number;
};

export type Receipt = {
  items: ReceiptItem[];
  subtotal: number;
  service_charge: number;
  gst: number;
  total: number;
  currency: string;
};

export type Expense = {
  id: string;
  paid_by: string;
  group_id: number;
  created_at: string;
  title: string;
  amount: number;
  is_equal_split: boolean;
  currency: string;
  multiplier?: number;
  payees: Payee[];
  receipt: Receipt;
};

export type TempReceiptRow = {
  id: number;
  created_at: string;
  group_id: number;
  title?: string;
  paid_by?: string;
  expense_id?: string;
  last_receipt: {
    users: string[];
    receipt: Receipt;
  };
};

// Payload schema DTOs
export type PostExpensePayload = Omit<Expense, "id" | "created_at">;
export type PatchTempReceiptPayload = Omit<
  TempReceiptRow,
  "id" | "created_at" | "group_id"
>;
