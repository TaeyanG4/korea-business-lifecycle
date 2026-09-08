from korea_business_lifecycle.kaggle_permit_demand_forecast import build_notebook


def test_permit_demand_notebook_is_valid_business_ml_analysis() -> None:
    notebook = build_notebook()
    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) >= 25
    ids = [cell["id"] for cell in notebook["cells"]]
    assert len(ids) == len(set(ids))

    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert code_cells
    for index, cell in enumerate(code_cells, start=1):
        compile("".join(cell["source"]), f"permit-demand-cell-{index}", "exec")

    all_text = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "3,010,802" in all_text
    assert "current snapshot" in all_text.lower()
    assert "next 3" in all_text.lower()
    assert "walk-forward" in all_text.lower()
    assert "count:poisson" in all_text
    assert "reg:tweedie" in all_text
    assert "seasonal_ml_blend" in all_text
    assert "top10_capture" in all_text
    assert "SHAP" in all_text
    assert "uncertainty" in all_text.lower()
    assert "2026-08" in all_text
    assert "authoritative administrative boundary" in all_text


def test_permit_demand_notebook_generation_is_deterministic() -> None:
    assert build_notebook() == build_notebook()
