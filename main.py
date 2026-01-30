from fastmcp import FastMCP
import os
from supabase import create_client, Client

mcp = FastMCP("ExpenseTracker")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in env variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@mcp.tool()
def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add a new expense entry to Supabase."""
    data = {
        "date": date,
        "amount": float(amount),
        "category": category,
        "subcategory": subcategory,
        "note": note,
    }

    res = supabase.table("expenses").insert(data).execute()

    if not res.data:
        return {"status": "error", "message": "Insert failed", "raw": str(res)}

    return {"status": "ok", "id": res.data[0]["id"]}


@mcp.tool()
def list_expenses(start_date: str, end_date: str):
    """List expense entries within an inclusive date range."""
    res = (
        supabase.table("expenses")
        .select("id,date,amount,category,subcategory,note")
        .gte("date", start_date)
        .lte("date", end_date)
        .order("id", desc=False)
        .execute()
    )
    return res.data


@mcp.tool()
def summarize(start_date: str, end_date: str, category: str = None):
    """
    Summarize expenses by category within an inclusive date range.
    (Done client-side because Supabase REST doesn't support easy GROUP BY directly)
    """
    query = (
        supabase.table("expenses")
        .select("category,amount")
        .gte("date", start_date)
        .lte("date", end_date)
    )

    if category:
        query = query.eq("category", category)

    res = query.execute()
    rows = res.data or []

    totals = {}
    for r in rows:
        cat = r["category"]
        amt = float(r["amount"])
        totals[cat] = totals.get(cat, 0) + amt

    output = [{"category": k, "total_amount": v} for k, v in sorted(totals.items())]
    return output


if __name__ == "__main__":
    mcp.run()
