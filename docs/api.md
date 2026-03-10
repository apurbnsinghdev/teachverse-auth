### 1. API Documentation `docs/api.md`
## Security & Permissions System
Our API uses a **Dependency Factory Pattern** for granular access control.

### Usage
Every protected endpoint must use the `PermissionChecker` dependency to ensure the system checks permissions **before** the business logic executes.

```python
@router.post("/")
async def create_permission(
    permission_data: PermissionCreate,
    current_user: TokenData = Depends(PermissionChecker("auth", "permission", "create"))
):
    ...