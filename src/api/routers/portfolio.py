import os

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/portfolio/stats")
def get_portfolio_stats():
    """
    Return P10 through P90 percentile table for 10 core KPIs across all 92 companies.
    """
    csv_path = "output/portfolio_stats.csv"
    if not os.path.exists(csv_path):
        raise HTTPException(
            status_code=404, detail="Portfolio statistics have not been generated yet."
        )

    try:
        df = pd.read_csv(csv_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read portfolio stats: {e!s}"
        )
