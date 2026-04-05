import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { Receipt } from "@src/app/api/receipts/schema";
import { formatMoney } from "@/lib/utils";

const COMMON_CURRENCY_CODES: Record<string, string> = {
  SGD: "Singapore Dollar",
  MYR: "Malaysian Ringgit",
  AUD: "Australian Dollar",
  THB: "Thai Baht",
  VND: "Vietnamese Dong",
  IDR: "Indonesian Rupiah",
  CNY: "Chinese Yuan",
  KRW: "Korean Won",
  JPY: "Japanese Yen",
  INR: "Indian Rupee",
  GBP: "British Pound",
  USD: "US Dollar",
  EUR: "Euro",
};

type ConfirmItemsProps = {
  receipt: Receipt;
  users: string[];
  expenseTitle: string;
  paidBy: string;
  step1GuardError: string | null;
  onUpdateExpenseTitle: (value: string) => void;
  onUpdatePaidBy: (value: string) => void;
  onUpdateItem: (
    index: number,
    field: "name" | "quantity" | "subtotal",
    value: string,
  ) => void;
  onUpdateMeta: (
    field: "currency" | "service_charge" | "gst",
    value: string,
  ) => void;
  onAddItem: () => void;
  onRemoveItems: (indices: number[]) => void;
  onNext: () => void;
};

export function ConfirmItems({
  receipt,
  users,
  expenseTitle,
  paidBy,
  step1GuardError,
  onUpdateExpenseTitle,
  onUpdatePaidBy,
  onUpdateItem,
  onUpdateMeta,
  onAddItem,
  onRemoveItems,
  onNext,
}: ConfirmItemsProps) {
  const [deleteMode, setDeleteMode] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<number[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [draftName, setDraftName] = useState("");
  const [draftQty, setDraftQty] = useState(0);
  const [draftSubtotal, setDraftSubtotal] = useState("");

  const toggleDeleteChoice = (index: number) => {
    setPendingDelete((current) =>
      current.includes(index)
        ? current.filter((entry) => entry !== index)
        : [...current, index],
    );
  };

  const handleDeleteAction = () => {
    if (!deleteMode) {
      setDeleteMode(true);
      return;
    }
    if (pendingDelete.length > 0) {
      onRemoveItems(pendingDelete);
    }
    setPendingDelete([]);
    setDeleteMode(false);
  };

  const openEditModal = (index: number) => {
    const item = receipt.items[index];
    setEditingIndex(index);
    setDraftName(item.name ?? "");
    setDraftQty(item.quantity ?? 0);
    setDraftSubtotal(item.subtotal === null ? "" : String(item.subtotal));
  };

  const closeEditModal = () => {
    setEditingIndex(null);
  };

  const saveEditModal = () => {
    if (editingIndex === null) return;
    onUpdateItem(editingIndex, "name", draftName);
    onUpdateItem(editingIndex, "quantity", String(Math.max(0, draftQty)));
    onUpdateItem(editingIndex, "subtotal", draftSubtotal);
    closeEditModal();
  };

  const missingFields: string[] = [];
  if (!expenseTitle.trim()) {
    missingFields.push("expense title");
  }
  if (!paidBy.trim() || !users.includes(paidBy)) {
    missingFields.push("paid by");
  }
  if (!receipt.currency || !(receipt.currency in COMMON_CURRENCY_CODES)) {
    missingFields.push("currency");
  }

  const isStep1Valid = missingFields.length === 0;
  const validationMessage = `please fill in the following fields: ${missingFields.join(", ")}`;

  return (
    <>
      <Stack spacing={2.5}>
        <Card sx={{ backgroundColor: "#e8f5e9" }}>
          <CardContent>
            <Typography fontWeight={700}>
              Step 1/3: Confirm receipt details
            </Typography>
            <Typography variant="body2" mt={1}>
              Please double check the payer and total cost for this bill
            </Typography>
          </CardContent>
        </Card>

        {step1GuardError ? (
          <Typography color="error.main" variant="body2">
            {step1GuardError}
          </Typography>
        ) : null}

        <Card variant="outlined">
          <CardContent>
            <Stack spacing={1.5}>
              <TextField
                value={expenseTitle}
                onChange={(event) => onUpdateExpenseTitle(event.target.value)}
                label="Please enter a title for this expense"
                placeholder="Dinner at XYZ"
                size="small"
                fullWidth
              />
              <TextField
                select
                value={paidBy}
                onChange={(event) => onUpdatePaidBy(event.target.value)}
                label="Paid by"
                size="small"
                fullWidth
              >
                <MenuItem value="" disabled>
                  Select payer
                </MenuItem>
                {users.map((user) => (
                  <MenuItem key={user} value={user}>
                    {user}
                  </MenuItem>
                ))}
              </TextField>
            </Stack>
          </CardContent>
        </Card>

        <Card elevation={1}>
          <CardContent>
            <Table size="small" sx={{ tableLayout: "fixed", width: "100%" }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, width: "50%" }}>
                    Item
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: 700, width: "10%" }}
                    align="center"
                  >
                    Qty
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: 700, width: "20%" }}
                    align="right"
                  >
                    Subtotal
                  </TableCell>
                  <TableCell
                    sx={{ fontWeight: 700, width: "10%" }}
                    align="center"
                  >
                    {deleteMode ? "Delete" : "Edit"}
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {receipt.items.map((item, index) => {
                  const marked = pendingDelete.includes(index);
                  return (
                    <TableRow key={String(index)} selected={marked}>
                      <TableCell
                        sx={{
                          whiteSpace: "normal",
                          overflowWrap: "anywhere",
                        }}
                      >
                        {item.name || "Untitled item"}
                      </TableCell>
                      <TableCell align="center">
                        <Typography fontWeight={700}>
                          {item.quantity}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography>
                          {formatMoney(item.subtotal ?? 0)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        {deleteMode ? (
                          <IconButton
                            color={marked ? "error" : "default"}
                            onClick={() => toggleDeleteChoice(index)}
                          >
                            <DeleteOutlineIcon />
                          </IconButton>
                        ) : (
                          <IconButton onClick={() => openEditModal(index)}>
                            <EditOutlinedIcon />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>

            <Stack spacing={1.5} mt={2}>
              <TextField
                select
                value={receipt.currency}
                onChange={(event) =>
                  onUpdateMeta("currency", event.target.value)
                }
                label="Currency"
                size="small"
              >
                {Object.entries(COMMON_CURRENCY_CODES).map(([code, name]) => (
                  <MenuItem key={code} value={code}>
                    {code} ({name})
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                value={receipt.service_charge}
                onChange={(event) =>
                  onUpdateMeta("service_charge", event.target.value)
                }
                label="Service charge"
                type="number"
                size="small"
                slotProps={{
                  input: { inputProps: { min: 0, step: "0.01" } },
                }}
              />
              <TextField
                value={receipt.gst}
                onChange={(event) => onUpdateMeta("gst", event.target.value)}
                label="GST / tax"
                type="number"
                size="small"
                slotProps={{
                  input: { inputProps: { min: 0, step: "0.01" } },
                }}
              />
            </Stack>

            <Box
              mt={2}
              sx={{
                backgroundColor: "#fff3e0",
                border: "1px solid #f0c48a",
                borderRadius: 2,
                px: 1.5,
                py: 1.25,
              }}
            >
              <Typography
                variant="body2"
                color="#ad5a00"
                fontWeight={700}
                fontSize={18}
              >
                Subtotal: {formatMoney(receipt.subtotal)} {receipt.currency}
              </Typography>
              <Typography
                variant="body2"
                color="#ad5a00"
                fontWeight={700}
                fontSize={18}
              >
                Total: {formatMoney(receipt.total)} {receipt.currency}
              </Typography>
            </Box>

            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={1.5}
              mt={2.5}
              justifyContent="space-between"
            >
              <Button variant="outlined" onClick={onAddItem}>
                Add new entry
              </Button>
              <Button
                color={deleteMode ? "error" : "inherit"}
                variant="outlined"
                onClick={handleDeleteAction}
              >
                {deleteMode ? "Confirm deletion" : "Delete entry"}
              </Button>
              <Button
                variant="contained"
                onClick={onNext}
                disabled={!isStep1Valid}
              >
                Proceed to step 2
              </Button>
            </Stack>
            {!isStep1Valid ? (
              <Typography color="error.main" variant="body2" mt={1.25}>
                {validationMessage}
              </Typography>
            ) : null}
          </CardContent>
        </Card>
      </Stack>

      <Dialog
        open={editingIndex !== null}
        onClose={closeEditModal}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>Edit item</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={0.5}>
            <TextField
              label="Name"
              value={draftName}
              onChange={(event) => setDraftName(event.target.value)}
              size="small"
              fullWidth
            />

            <Box>
              <Typography variant="body2" color="text.secondary" mb={0.75}>
                Quantity
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center">
                <Button
                  variant="outlined"
                  onClick={() => setDraftQty((prev) => Math.max(0, prev - 1))}
                  sx={{ minWidth: 40 }}
                >
                  -
                </Button>
                <Typography
                  sx={{ minWidth: 26, textAlign: "center", fontWeight: 700 }}
                >
                  {draftQty}
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => setDraftQty((prev) => prev + 1)}
                  sx={{ minWidth: 40 }}
                >
                  +
                </Button>
              </Stack>
            </Box>

            <TextField
              label="Subtotal"
              value={draftSubtotal}
              onChange={(event) => setDraftSubtotal(event.target.value)}
              type="text"
              size="small"
              placeholder="0.00"
              slotProps={{
                input: {
                  inputProps: {
                    inputMode: "decimal",
                  },
                },
              }}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeEditModal}>Cancel</Button>
          <Button variant="contained" onClick={saveEditModal}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
