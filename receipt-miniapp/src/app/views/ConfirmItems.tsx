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
import { Receipt } from "../api/receipts/schema";

type ConfirmItemsProps = {
  receipt: Receipt;
  saving: boolean;
  formatMoney: (value: number) => string;
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
  onSave: () => void;
};

export function ConfirmItems({
  receipt,
  saving,
  formatMoney,
  onUpdateItem,
  onUpdateMeta,
  onAddItem,
  onRemoveItems,
  onSave,
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

  const changeQtyBy = (index: number, currentQty: number, delta: number) => {
    const nextQty = Math.max(0, currentQty + delta);
    onUpdateItem(index, "quantity", String(nextQty));
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

  return (
    <>
      <Stack spacing={2.5}>
        <Card sx={{ backgroundColor: "#e8f5e9" }}>
          <CardContent>
            <Typography variant="h6" fontWeight={700}>
              Step 1/3: Confirm receipt items
            </Typography>
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

            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              mt={1}
            >
              Currency: {receipt.currency}
            </Typography>

            <Stack spacing={1.5} mt={2}>
              <TextField
                value={receipt.currency}
                onChange={(event) =>
                  onUpdateMeta("currency", event.target.value)
                }
                label="Currency"
                size="small"
              />
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

            <Box mt={2}>
              <Typography variant="body2" color="text.secondary">
                Subtotal: {formatMoney(receipt.subtotal)} {receipt.currency}
              </Typography>
              <Typography variant="body2" color="text.secondary">
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
              <Button variant="contained" onClick={onSave} disabled={saving}>
                {saving ? "Saving..." : "Save step 1"}
              </Button>
            </Stack>
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
