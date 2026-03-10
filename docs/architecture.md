### 1. Architecture: TeachVerse Auth `docs/architecture.md`

```markdown

## 1. Design Philosophy
TeachVerse Auth is designed with a **"Security-First"** approach. It leverages a centralized `PermissionChecker` gatekeeper to ensure access control is strictly enforced at the API entry point.

**Architecture Diagram**
(./images/Architecture-Diagram.png)

## 2. Core Components

### A. The Dependency Gatekeeper (`PermissionChecker`)
We utilize a **Dependency Class Pattern**. By implementing `__call__`, the checker integrates seamlessly into the FastAPI request lifecycle, ensuring security logic is decoupled from business logic.

### B. The Recursive Hierarchy Engine
Unlike flat RBAC systems, TeachVerse Auth uses an **Inheritance-based RBAC model**.
* **Role Hierarchy**: Roles (e.g., `manager`) inherit permissions from their children (e.g., `viewer`).
* **Auto-Generation**: Permissions are calculated dynamically, ensuring ownership propagation.



## 3. Data Flow
1. **Request Received**: Client provides a JWT.
2. **Identity Verification**: `get_current_user` validates the token.
3. **Permission Resolution**: `PermissionChecker` fetches effective permissions.
4. **Enforcement**: If the required scope is missing, a `403 Forbidden` is raised **before** the controller executes.

## 4. Visual Permission Flow Charts
1. **Overall Permission Hierarchy Flow**
(./images/Overall-Permission-Hierarchy-Flow)
2. **Teacher vs Student Permission Matrix**
(./images/Teacher-vs-Student-Permission-Matrix.png)
3. **Automatic Owner "Manage" Permission Flow**
(./images/Automatic-Owner-Manage-Permission-Flow.png)