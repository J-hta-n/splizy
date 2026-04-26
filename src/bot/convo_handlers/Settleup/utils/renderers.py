from io import BytesIO
from math import cos, radians, sin

import matplotlib
import matplotlib.colors as mcolors
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from src.bot.convo_handlers.Settleup.utils.general import SettleupStats
from src.bot.convo_utils.telegram import get_message_thread_id
from src.lib.currencies.utils import get_shorthand_currency

matplotlib.use("Agg")
import matplotlib.pyplot as plt

TABLE_FONT_FAMILY = "DejaVu Sans"
TABLE_BODY_FONT_SIZE = 16
TABLE_HEADER_FONT_SIZE = 17


async def send_stats_table(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    stats: SettleupStats,
):
    image = _build_stats_table_image(stats)
    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image,
            message_thread_id=get_message_thread_id(update),
        )
    except BadRequest:
        pass


def _fmt_signed(amount: float, currency: str) -> str:
    if abs(amount) <= 0.005:
        return "-"
    sign = "+" if amount > 0 else "-"
    return f"{sign}{currency}{abs(amount):.2f}"


def _fmt_money(amount: float, currency: str) -> str:
    return f"{currency}{amount:.2f}"


def _fit_user_label(user: str, max_len: int = 10) -> str:
    label = f"@{user}"
    if len(label) <= max_len:
        return label
    return f"{label[: max_len - 1]}..."


def _build_stats_table_image(stats: SettleupStats) -> BytesIO:
    currency = get_shorthand_currency(stats["currency"])
    payers = stats.get("payers", {})
    transfers = stats.get("transfers", {})
    final_spending = stats.get("individual_spending", {})
    total_spending = stats.get("total_spending", sum(final_spending.values()))

    users = sorted(set(payers) | set(transfers) | set(final_spending))
    rows: list[list[str]] = []
    for user in users:
        rows.append(
            [
                _fit_user_label(user),
                _fmt_signed(-payers.get(user, 0.0), currency),
                _fmt_signed(transfers.get(user, 0.0), currency),
                _fmt_money(final_spending.get(user, 0.0), currency),
            ]
        )

    rows.append(
        [
            "Total",
            "-",
            "-",
            _fmt_money(total_spending, currency),
        ]
    )

    headers = [
        "User",
        "Amount paid\nfor group",
        "Suggested\ntransfers",
        "Final indiv\nspending",
    ]

    fig_h = max(4.2, 1.7 + 0.62 * (len(rows) + 1))
    fig, ax = plt.subplots(figsize=(10.5, fig_h), facecolor="#05070C")
    ax.axis("off")

    table = ax.table(
        cellText=rows,
        colLabels=headers,
        loc="center",
        cellLoc="left",
        colLoc="center",
        colWidths=[0.25, 0.25, 0.25, 0.25],
        bbox=[0.04, 0.04, 0.92, 0.92],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(TABLE_BODY_FONT_SIZE)

    cell_keys = list(table.get_celld().keys())
    max_row = max(r for r, _ in cell_keys)
    max_col = max(c for _, c in cell_keys)

    for (row, col), cell in table.get_celld().items():
        edges = "BRTL"
        if row == 0:
            edges = edges.replace("T", "")
        if row == max_row:
            edges = edges.replace("B", "")
        if col == 0:
            edges = edges.replace("L", "")
        if col == max_col:
            edges = edges.replace("R", "")
        cell.visible_edges = edges if edges else "open"

        cell.set_edgecolor("#00FFFF")
        cell.set_linewidth(1.45)
        if row == 0:
            cell.set_facecolor("#1B2742")
            cell.set_height(0.215)
            cell.set_alpha(1.0)
            if col < 3:
                # Prevent diagonal anti-aliasing artifacts in the first 3 headers.
                cell.set_antialiased(False)
            cell.get_text().set_color("#F2FCFF")
            cell.get_text().set_fontsize(TABLE_HEADER_FONT_SIZE)
            cell.get_text().set_fontweight("bold")
            cell.get_text().set_fontfamily(TABLE_FONT_FAMILY)
            cell.get_text().set_ha("center")
            cell.get_text().set_va("center")
            cell.get_text().set_linespacing(1.25)
        else:
            cell.set_facecolor("#090D17" if row % 2 else "#0C1120")
            cell.set_height(0.12)
            cell.set_alpha(1.0)
            text = cell.get_text().get_text()
            cell.get_text().set_fontfamily(TABLE_FONT_FAMILY)
            cell.get_text().set_fontsize(TABLE_BODY_FONT_SIZE)
            if row == max_row:
                cell.set_facecolor("#131A2C")
                cell.get_text().set_fontweight("bold")
            if col in (1, 2) and text == "-":
                cell.get_text().set_color("#FFFFFF")
            elif col in (1, 2) and text.startswith("-"):
                cell.get_text().set_color("#FF768E")
            elif col in (1, 2) and text.startswith("+"):
                cell.get_text().set_color("#57FFA3")
            elif col == 3:
                cell.get_text().set_color("#00FFFF")
                cell.get_text().set_fontweight("bold")
            else:
                cell.get_text().set_color("#EAF3FF")

    image = BytesIO()
    fig.savefig(
        image, format="png", dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor()
    )
    plt.close(fig)
    image.seek(0)
    image.name = "settleup_table.png"
    return image


async def send_stats_chart(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    stats: SettleupStats,
):
    chart = _build_spending_chart(stats)
    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=chart,
            message_thread_id=get_message_thread_id(update),
        )
    except BadRequest:
        pass


def _build_spending_chart(stats: SettleupStats) -> BytesIO:
    currency = get_shorthand_currency(stats["currency"])
    indiv = stats.get("individual_spending", {})

    if isinstance(indiv, dict):
        participants = [
            (user, amount) for user, amount in indiv.items() if amount > 0.01
        ]
    else:
        participants = [(user, amount) for user, amount in indiv if amount > 0.01]

    if not participants:
        participants = [("No data", 1.0)]

    labels = [f"@{user}" for user, _ in participants]
    values = [amount for _, amount in participants]

    n_colors = len(values)
    denom = max(n_colors - 1, 1)
    gradient_colors = [
        mcolors.hsv_to_rgb((0.5, 0.7, 1.0 - 0.22 * (i / denom)))
        for i in range(n_colors)
    ]
    order: list[int] = []
    left = 0
    right = n_colors - 1
    while left <= right:
        order.append(left)
        if left != right:
            order.append(right)
        left += 1
        right -= 1
    colors = [gradient_colors[i] for i in order]

    fig, ax = plt.subplots(figsize=(7, 7), facecolor="#0F1012")
    ax.set_facecolor("#0F1012")

    wedges, _ = ax.pie(
        values,
        startangle=90,
        colors=colors,
        wedgeprops={"width": 0.38, "edgecolor": "#0F1012", "linewidth": 2.6},
    )

    for wedge, label, value in zip(wedges, labels, values):
        angle = (wedge.theta1 + wedge.theta2) / 2
        x = 1.12 * cos(radians(angle))
        y = 1.12 * sin(radians(angle))
        label_text = f"{label}\n{currency}{value:.2f}"
        ax.text(
            x,
            y,
            label_text,
            color="#F2F2F2",
            fontsize=15,
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.45", "fc": "#232428", "ec": "none"},
        )

    total_spending = stats.get("total_spending", sum(values))
    ax.text(
        0,
        0,
        f"Total\n{currency}{total_spending:.2f}",
        ha="center",
        va="center",
        color="#EDEDED",
        fontsize=20,
        fontweight="bold",
    )

    ax.set(aspect="equal")

    image = BytesIO()
    fig.savefig(
        image,
        format="png",
        dpi=170,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    image.seek(0)
    image.name = "spending_stats.png"
    return image
