import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { IndivSplit, ItemSummary } from "@src/lib/types";

type IndividualItemsProps = {
  users: string[];
  selectedUser: string | null;
  selectedUserIndiv: IndivSplit | null;
  itemSummaries: ItemSummary[];
  currency: string;
  saving: boolean;
  formatMoney: (value: number) => string;
  onSelectUser: (user: string) => void;
  onAdjustQuantity: (itemIndex: number, delta: number) => void;
  onBack: () => void;
  onSave: () => void;
};

const UserCards = ({
  users,
  selectedUser,
  onSelectUser,
}: {
  users: string[];
  selectedUser: string | null;
  onSelectUser: (user: string) => void;
}) => {
  if (users.length === 0) {
    return (
      <Card variant="outlined">
        <CardContent>
          <Typography variant="body2" color="warning.main">
            No fixed users found in saved assignments.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: {
          xs: "repeat(2, minmax(0, 1fr))",
          sm: "repeat(3, minmax(0, 1fr))",
        },
        gap: 1,
      }}
    >
      {users.map((user) => {
        const active = selectedUser === user;
        return (
          <button
            key={user}
            type="button"
            onClick={() => onSelectUser(user)}
            style={{
              borderRadius: 12,
              border: active ? "2px solid #2e7d32" : "2px solid #81c784",
              padding: "10px 12px",
              fontWeight: 700,
              background: active ? "#c8e6c9" : "#e8f5e9",
              color: active ? "#1b5e20" : "#2e7d32",
            }}
          >
            {active ? `${user} (viewing)` : user}
          </button>
        );
      })}
    </Box>
  );
};

const QuantityControl = ({
  value,
  onMinus,
  onPlus,
}: {
  value: number;
  onMinus: () => void;
  onPlus: () => void;
}) => {
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <Button variant="outlined" onClick={onMinus} sx={{ minWidth: 40 }}>
        -
      </Button>
      <Chip
        label={value}
        color="default"
        variant="outlined"
        sx={{ minWidth: 48, fontWeight: 700 }}
      />
      <Button variant="outlined" onClick={onPlus} sx={{ minWidth: 40 }}>
        +
      </Button>
    </Stack>
  );
};

export function IndividualItems({
  users,
  selectedUser,
  selectedUserIndiv,
  itemSummaries,
  currency,
  saving,
  formatMoney,
  onSelectUser,
  onAdjustQuantity,
  onBack,
  onSave,
}: IndividualItemsProps) {
  return (
    <Stack spacing={2.5}>
      <Card sx={{ backgroundColor: "#e8f5e9" }}>
        <CardContent>
          <Typography fontWeight={700}>
            Step 2/3: Please assign non-shared items
          </Typography>
          <Typography variant="body2" mt={1}>
            Currently viewing for: {selectedUser ?? "-"}
          </Typography>
        </CardContent>
      </Card>

      <UserCards
        users={users}
        selectedUser={selectedUser}
        onSelectUser={onSelectUser}
      />

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={1.25}>
            {itemSummaries.map(({ item, index, key, unitPrice }) => {
              const currentQty = selectedUserIndiv?.quantities[key] ?? 0;
              return (
                <Box
                  key={key}
                  sx={{
                    display: "grid",
                    gridTemplateColumns: "1fr auto",
                    alignItems: "center",
                    gap: 1.25,
                  }}
                >
                  <Box
                    sx={{
                      border: "1px solid #f0c48a",
                      backgroundColor: "#fff3e0",
                      borderRadius: 2,
                      px: 1.5,
                      py: 1.25,
                    }}
                  >
                    <Typography fontWeight={700}>
                      {item.name || `Item ${index + 1}`}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {currency} {formatMoney(unitPrice)} | total qty{" "}
                      {item.quantity}
                    </Typography>
                  </Box>
                  <QuantityControl
                    value={currentQty}
                    onMinus={() => onAdjustQuantity(index, -1)}
                    onPlus={() => onAdjustQuantity(index, 1)}
                  />
                </Box>
              );
            })}
          </Stack>
        </CardContent>
      </Card>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={1.5}
        justifyContent="space-between"
      >
        <Button variant="outlined" onClick={onBack}>
          Back
        </Button>
        <Button
          variant="contained"
          onClick={onSave}
          disabled={saving || users.length === 0}
        >
          {saving ? "Saving..." : "Save step 2"}
        </Button>
      </Stack>
    </Stack>
  );
}
