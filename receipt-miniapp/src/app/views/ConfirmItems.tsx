import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  Button,
  Card,
  CardContent,
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
import { LastReceipt } from "./types";

type ConfirmItemsProps = {
  receipt: LastReceipt;
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

  return (
    <Stack spacing={2.5}>
      <Card elevation={1}>
        <CardContent>
          <Typography variant="h6" fontWeight={700}>
            Step 1/3: Confirm receipt items
          </Typography>
        </CardContent>
      </Card>

      <Card elevation={1}>
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Item</TableCell>
                <TableCell sx={{ fontWeight: 700 }} align="center">
                  Qty
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }} align="right">
                  Subtotal
                </TableCell>
                {deleteMode ? (
                  <TableCell sx={{ fontWeight: 700 }} align="center">
                    Delete
                  </TableCell>
                ) : null}
              </TableRow>
            </TableHead>
            <TableBody>
              {receipt.items.map((item, index) => {
                const marked = pendingDelete.includes(index);
                return (
                  <TableRow key={String(index)} selected={marked}>
                    <TableCell>
                      <TextField
                        value={item.name}
                        onChange={(event) =>
                          onUpdateItem(index, "name", event.target.value)
                        }
                        placeholder="Item name"
                        size="small"
                        fullWidth
                      />
                    </TableCell>
                    <TableCell align="center" sx={{ minWidth: 130 }}>
                      <Stack
                        direction="row"
                        spacing={1}
                        justifyContent="center"
                        alignItems="center"
                      >
                        <Button
                          variant="outlined"
                          onClick={() => changeQtyBy(index, item.quantity, -1)}
                          sx={{ minWidth: 36, px: 0 }}
                        >
                          -
                        </Button>
                        <Typography
                          sx={{
                            minWidth: 24,
                            textAlign: "center",
                            fontWeight: 700,
                          }}
                        >
                          {item.quantity}
                        </Typography>
                        <Button
                          variant="outlined"
                          onClick={() => changeQtyBy(index, item.quantity, 1)}
                          sx={{ minWidth: 36, px: 0 }}
                        >
                          +
                        </Button>
                      </Stack>
                    </TableCell>
                    <TableCell align="right" sx={{ minWidth: 140 }}>
                      <TextField
                        value={item.subtotal ?? ""}
                        onChange={(event) =>
                          onUpdateItem(index, "subtotal", event.target.value)
                        }
                        type="number"
                        size="small"
                        slotProps={{
                          input: { inputProps: { min: 0, step: "0.01" } },
                        }}
                        sx={{ maxWidth: 120 }}
                      />
                    </TableCell>
                    {deleteMode ? (
                      <TableCell align="center">
                        <IconButton
                          color={marked ? "error" : "default"}
                          onClick={() => toggleDeleteChoice(index)}
                        >
                          <DeleteOutlineIcon />
                        </IconButton>
                      </TableCell>
                    ) : null}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>

          <Stack spacing={1.5} mt={2}>
            <TextField
              value={receipt.currency}
              onChange={(event) => onUpdateMeta("currency", event.target.value)}
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
  );
}
