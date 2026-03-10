```markdown
# Real-World Examples

## 1. E-Learning Platform Hierarchy
The system automatically handles inheritance and scope.

```python
# Teacher has broad, resource-specific access
teacher_permissions = [
    "course:course:*:create",     
    "course:course:123:update",   
    "student:student:*:read",     
]

# Student has limited, self-referential access
student_permissions = [
    "course:course:*:read",       
    "user:profile:self:update",   
    "payment:transaction:self:read", 
]