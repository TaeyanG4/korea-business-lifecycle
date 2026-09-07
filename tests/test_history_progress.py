from korea_business_lifecycle.history_progress import format_history_progress


def test_page_progress_contains_page_and_row_percentages() -> None:
    rendered = format_history_progress(
        {
            "event": "page_complete",
            "task_index": 2,
            "task_total": 6,
            "page_no": 12,
            "total_pages": 57,
            "stored_rows": 1200,
            "total_count": 5664,
        }
    )
    assert rendered == "[2/6] PAGE 12/57 (21.1%) rows 1,200/5,664"


def test_done_progress_contains_overall_task_percentage() -> None:
    rendered = format_history_progress(
        {
            "event": "task_complete",
            "task_index": 1,
            "task_total": 6,
            "finished_tasks": 1,
            "source_key": "rest_cafes",
            "authority_code": "3830000",
            "base_date": "20260831",
            "observed_pages": 57,
            "observed_rows": 5664,
        }
    )
    assert "overall 1/6 (16.7%)" in rendered
    assert "pages=57 rows=5,664" in rendered
