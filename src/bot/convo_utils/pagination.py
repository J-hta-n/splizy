def get_page_window(
    total_items: int, page_size: int, requested_page: int
) -> tuple[int, int, int, int]:
    if page_size <= 0:
        page_size = 1

    total_pages = max(1, (total_items + page_size - 1) // page_size)
    current_page = max(0, min(requested_page, total_pages - 1))
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_items)

    return current_page, total_pages, start_idx, end_idx
