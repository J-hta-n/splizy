export type ReceiptItem = {
  name: string;
  quantity: number;
  subtotal: number | null;
};

export type LastReceipt = {
  items: ReceiptItem[];
  subtotal: number;
  service_charge: number;
  gst: number;
  total: number;
  currency: string;
};

export type IndividualAssignment = {
  user: string;
  quantities: Record<string, number>;
};

export type SharedAssignment = {
  user: string;
  quantities: Record<string, number>;
};

export type ItemSummary = {
  item: ReceiptItem;
  index: number;
  key: string;
  indivTotal: number;
  leftover: number;
  unitPrice: number;
};

export type ReceiptRow = {
  id: number;
  created_at: string;
  group_id: number | null;
  last_receipt: LastReceipt | null;
  last_indiv: IndividualAssignment[] | null;
  last_shared: SharedAssignment[] | null;
  last_confirmation: boolean | null;
};
