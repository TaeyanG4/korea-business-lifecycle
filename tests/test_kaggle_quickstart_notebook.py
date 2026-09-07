from korea_business_lifecycle.kaggle_quickstart import build_notebook


def test_quickstart_notebook_is_valid_public_dataset_example() -> None:
    notebook = build_notebook()
    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) >= 15
    ids = [cell["id"] for cell in notebook["cells"]]
    assert len(ids) == len(set(ids))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert code_cells
    for index, cell in enumerate(code_cells, start=1):
        compile("".join(cell["source"]), f"quickstart-cell-{index}", "exec")
    all_text = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "3,010,802" in all_text
    assert "South Korea Food-Service Permits - Snapshot" in all_text
    assert "current snapshot" in all_text.lower()
    assert "not a historical time series" in all_text.lower()
    assert "EPSG:5174" in all_text
    assert "business_type_name" in all_text
    assert "present_pct" in all_text
    assert "korea_food_service_permits.csv" in all_text
    assert "korea_food_service_permits.parquet" in all_text


def test_quickstart_notebook_generation_is_deterministic() -> None:
    assert build_notebook() == build_notebook()
