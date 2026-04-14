import csv
from datetime import datetime, timezone
from io import BytesIO, StringIO

import matplotlib
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from src.bot.convo_handlers.Settleup.utils.general import get_settleup_details
from src.lib.currencies.config import ALL_CURRENCY_CODES, CURRENCY_SHORTHAND_MAPPING
from src.lib.currencies.utils import convert, read_cached_exchange_rates
from src.lib.splizy_repo.model import ExpenseRow

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _fmt_signed_raw(amount: float) -> str:
    if abs(amount) < 0.005:
        return "0.00"
    sign = "+" if amount > 0 else "-"
    return f"{sign}{abs(amount):.2f}"


def _get_users(all_expenses: list[ExpenseRow]) -> list[str]:
    users = set()
    for expense in all_expenses:
        users.add(expense["paid_by"])
        for payee in expense["payees"]:
            users.add(payee["user"])
    return sorted(users, key=str.lower)


def _sorted_expenses_chronological(all_expenses: list[ExpenseRow]) -> list[ExpenseRow]:
    return sorted(all_expenses, key=lambda expense: expense.get("created_at", ""))


def _compute_per_expense_rows(
    all_expenses: list[ExpenseRow], settleup_currency: str, users: list[str]
) -> list[tuple[str, dict[str, float]]]:
    per_expense_rows: list[tuple[str, dict[str, float]]] = []

    for expense in _sorted_expenses_chronological(all_expenses):
        row = {u: 0.0 for u in users}
        currency = expense["currency"]

        paid_amount = convert(expense["amount"], currency, settleup_currency)
        row[expense["paid_by"]] -= paid_amount  # Payer starts with deficit

        for payee in expense["payees"]:
            row[payee["user"]] += convert(
                payee["amount"], currency, settleup_currency
            )  # Payee owes positive

        title = (expense.get("title") or "").strip()
        row_label = title or expense.get("id") or "untitled_expense"
        per_expense_rows.append((row_label, row))

    return per_expense_rows


def _build_metadata_lines(
    all_expenses: list[ExpenseRow],
    settleup_currency: str,
    report_generated_at: datetime,
) -> list[str]:
    settle_currency = settleup_currency.upper()
    settle_shorthand = CURRENCY_SHORTHAND_MAPPING.get(settle_currency, settle_currency)
    settle_desc = ALL_CURRENCY_CODES.get(settle_currency, settle_currency)

    lines = [
        f"All amounts are in {settle_currency}, {settle_shorthand} ({settle_desc}).",
    ]

    rates_payload = read_cached_exchange_rates()
    if rates_payload:
        rates_date_str = str(rates_payload.get("date", ""))
        try:
            rates_date = datetime.fromisoformat(rates_date_str.replace("Z", "+00:00"))
            rates_date_friendly = rates_date.strftime("%d %b %Y")
        except (ValueError, AttributeError):
            rates_date_friendly = "unavailable"
    else:
        rates_date_friendly = "unavailable"

    generated_at_utc = report_generated_at.astimezone(timezone.utc).strftime("%d %b %Y")
    lines.append(
        f"Exchange rates as of {rates_date_friendly} (report generated: {generated_at_utc})."
    )

    involved_currencies = sorted(
        {
            expense["currency"].upper()
            for expense in all_expenses
            if expense["currency"].upper() != settle_currency
        }
    )

    if not involved_currencies:
        lines.append(
            f"No currency conversion needed: all expenses already in {settle_currency}."
        )
        return lines

    for src_currency in involved_currencies:
        try:
            rate = convert(1.0, settle_currency, src_currency)
            lines.append(f"1 {settle_currency} = {rate:.2f} {src_currency}")
        except RuntimeError:
            lines.append(
                f"1 {settle_currency} = unavailable {src_currency} (missing exchange rate)"
            )

    return lines


def _build_transfer_matrix(
    payments: dict[str, list[tuple[str, float]]], users: list[str]
) -> list[tuple[str, dict[str, float]]]:
    """Build transfer rows in matrix format: sender gets positive, receiver gets negative."""
    transfer_rows: list[tuple[str, dict[str, float]]] = []
    transfer_idx = 1

    for receiver in sorted(payments, key=str.lower):
        for sender, amount in sorted(payments[receiver], key=lambda x: x[0].lower()):
            row = {u: 0.0 for u in users}
            row[sender] = amount  # Sender gets credit back (positive)
            row[receiver] = -amount  # Receiver pay off debt (negative)
            transfer_rows.append((f"transfer_{transfer_idx}", row))
            transfer_idx += 1

    return transfer_rows


def _build_report_parts(
    all_expenses: list[ExpenseRow],
    settleup_currency: str,
    report_generated_at: datetime,
) -> tuple[
    list[str],
    list[str],
    list[list[str]],
    dict[str, float],
    list[tuple[str, dict[str, float]]],
]:
    users = _get_users(all_expenses)
    per_expense_rows = _compute_per_expense_rows(all_expenses, settleup_currency, users)

    metadata_lines = _build_metadata_lines(
        all_expenses, settleup_currency, report_generated_at
    )
    headers = ["expense", *users]
    rows: list[list[str]] = []
    for label, row in per_expense_rows:
        rows.append([label, *[_fmt_signed_raw(row[u]) for u in users]])

    # Compute net balances before settleup (sum across all expenses)
    before_balances: dict[str, float] = {u: 0.0 for u in users}
    for _, expense_row in per_expense_rows:
        for user in users:
            before_balances[user] += expense_row[user]

    # Get suggested transfers in matrix format
    stats, payments = get_settleup_details(all_expenses, settleup_currency)
    transfer_rows = _build_transfer_matrix(payments, users)

    return metadata_lines, headers, rows, before_balances, transfer_rows


def build_settleup_csv(
    all_expenses: list[ExpenseRow],
    settleup_currency: str,
    report_generated_at: datetime | None = None,
) -> bytes:
    generated_at = report_generated_at or datetime.now(timezone.utc)
    metadata_lines, headers, rows, before_balances, transfer_rows = _build_report_parts(
        all_expenses, settleup_currency, generated_at
    )
    users = list(before_balances.keys())

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["settleup_currency", settleup_currency])
    writer.writerow([])

    # Expense breakdown
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    # Settle-up logic
    writer.writerow([])
    writer.writerow(["BEFORE SETTLEUP"])
    writer.writerow(headers)
    before_row = [u for u in users]
    writer.writerow(["net", *[_fmt_signed_raw(before_balances[u]) for u in users]])

    writer.writerow([])
    writer.writerow(["SUGGESTED TRANSFERS"])
    writer.writerow(headers)
    for label, transfer_row in transfer_rows:
        writer.writerow([label, *[_fmt_signed_raw(transfer_row[u]) for u in users]])

    writer.writerow([])
    writer.writerow(["AFTER SETTLEUP"])
    writer.writerow(headers)
    writer.writerow(["net", *["0.00" for _ in users]])

    return output.getvalue().encode("utf-8")


def build_settleup_pdf(
    all_expenses: list[ExpenseRow],
    settleup_currency: str,
    report_generated_at: datetime | None = None,
) -> bytes:
    generated_at = report_generated_at or datetime.now(timezone.utc)
    metadata_lines, headers, rows, before_balances, transfer_rows = _build_report_parts(
        all_expenses, settleup_currency, generated_at
    )
    users = list(before_balances.keys())

    # Build all data for single combined table
    before_row = ["net", *[_fmt_signed_raw(before_balances[u]) for u in users]]
    transfer_data = [
        [label, *[_fmt_signed_raw(transfer_row[u]) for u in users]]
        for label, transfer_row in transfer_rows
    ]
    after_row = ["net", *["0.00" for _ in users]]

    # Calculate figure height
    num_expense_rows = len(rows)
    num_transfer_rows = len(transfer_data)
    total_data_rows = (
        num_expense_rows + 1 + num_transfer_rows + 1 + 0.5
    )  # expenses + before + transfers + after
    fig_h = max(6.0, 1.5 + 0.35 * total_data_rows + 0.3 * len(metadata_lines))

    fig = plt.figure(figsize=(12, fig_h), facecolor="#FFFFFF")
    ax = fig.add_subplot(111)
    ax.axis("off")

    text_y = 0.98

    # Add metadata at top
    for line in metadata_lines:
        ax.text(
            0.02,
            text_y,
            line,
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=9,
        )
        text_y -= 0.035

    # Combine all table data with section labels
    all_table_rows = []

    # Expense breakdown section
    for row in rows:
        all_table_rows.append(row)

    # Separator
    all_table_rows.append(["" for _ in headers])

    # Before section label
    all_table_rows.append(["[BEFORE SETTLEUP]"] + ["" for _ in users])
    all_table_rows.append(before_row)

    # Transfers section label
    all_table_rows.append(["[SUGGESTED TRANSFERS]"] + ["" for _ in users])
    for transfer_row in transfer_data:
        all_table_rows.append(transfer_row)

    # After section label
    all_table_rows.append(["[AFTER SETTLEUP]"] + ["" for _ in users])
    all_table_rows.append(after_row)

    table_y_top = text_y - 0.01
    table = ax.table(
        cellText=all_table_rows,
        colLabels=headers,
        bbox=[0.0, 0.02, 1.0, table_y_top],
        cellLoc="left",
        colLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)

    # Apply color coding to data cells (skip label rows)
    for (row_idx, col_idx), cell in table.get_celld().items():
        if row_idx == 0 or col_idx == 0:  # Headers and row labels
            continue
        cell_text = cell.get_text().get_text().strip()
        if cell_text.startswith("-"):
            cell.get_text().set_color("#C62828")  # Red for negative (paid/owed)
        elif cell_text.startswith("+"):
            cell.get_text().set_color("#2E7D32")  # Green for positive (received/credit)

    buffer = BytesIO()
    fig.savefig(buffer, format="pdf", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


async def send_settleup_csv(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    all_expenses: list[ExpenseRow],
    settleup_currency: str,
    report_generated_at: datetime | None = None,
) -> None:
    csv_bytes = build_settleup_csv(all_expenses, settleup_currency, report_generated_at)
    try:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=BytesIO(csv_bytes),
            filename="settleup_breakdown.csv",
            caption="Settle-up breakdown CSV",
        )
    except BadRequest:
        pass


async def send_settleup_reports(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    all_expenses: list[ExpenseRow],
    settleup_currency: str,
    report_generated_at: datetime | None = None,
) -> None:
    csv_bytes = build_settleup_csv(all_expenses, settleup_currency, report_generated_at)
    pdf_bytes = build_settleup_pdf(all_expenses, settleup_currency, report_generated_at)

    try:
        csv_file = BytesIO(csv_bytes)
        csv_file.name = "settleup_breakdown.csv"
        pdf_file = BytesIO(pdf_bytes)
        pdf_file.name = "settleup_breakdown.pdf"

        await context.bot.send_document(
            chat_id=update.effective_chat.id, document=csv_file
        )
        await context.bot.send_document(
            chat_id=update.effective_chat.id, document=pdf_file
        )
    except BadRequest:
        pass
