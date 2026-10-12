from ..utils.router_group import APIRouter
from ..utils.validation import QueryField

# Initialize the group with an explicit prefix path namespace rule
router = APIRouter(prefix="/items")

@router.get("/")
async def list_items(limit: int = QueryField(default=5)):
    """
    List all warehouse catalog items.
    """
    return {
        "router_group": "items",
        "mock_catalog": [f"Item SKU-{i}" for i in range(1, limit + 1)]
    }

@router.get("/{item_id:int}")
async def get_item_details(item_id: int):
    """
    Retrieve descriptive item fields via parameterized path routing.
    """
    return {
        "router_group": "items",
        "requested_id": item_id,
        "status": "active"
    }
