from korea_business_lifecycle.kaggle_regional_market import build_regional_market_notebook


def test_regional_market_notebook_is_compilable_and_semantically_bounded() -> None:
    notebook = build_regional_market_notebook()
    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) >= 15
    ids = [cell["id"] for cell in notebook["cells"]]
    assert len(ids) == len(set(ids))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    for index, cell in enumerate(code_cells, start=1):
        compile("".join(cell["source"]), f"regional-market-cell-{index}", "exec")
    text = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "3,010,802" in text
    assert "REGION_EN" in text
    assert "recent_admin_permit_share_pct" in text
    assert "coordinate_coverage_pct" in text
    assert "not an opportunity score" in text
    assert "not investment advice" in text
    assert "not a historical time series" in text
    assert "EPSG:5174" in text
    assert "status `03` is reversible" in text


def test_regional_market_notebook_generation_is_deterministic() -> None:
    assert build_regional_market_notebook() == build_regional_market_notebook()
