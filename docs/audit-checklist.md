# Entra ID audit checklist

Checks my agent runs in Stage 3. Each one is based on Microsoft documentation.

| # | Check | Pass when | Severity if it fails | Source |
|---|---|---|---|---|
| 1 | Legacy authentication is blocked | Security defaults are on, or an enabled Conditional Access policy blocks "Exchange ActiveSync" and "Other clients" for all users | High | [Block legacy authentication](https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-block-legacy-authentication) |
| 2 | Admins have MFA | Every user with an admin role has MFA registered and is covered by MFA (security defaults or a Conditional Access policy for all apps) | High | [Best practices for Entra roles, section 3](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/best-practices) |
| 3 | Service principals are not over-privileged | No app holds a high-risk Microsoft Graph application permission or the Global Administrator role | High / Medium | [Best practices for Entra roles, section 1 (least privilege)](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/best-practices) |
| 4 | Fewer than 5 Global Admins | Fewer than 5 Global Administrator assignments | Medium | [Best practices for Entra roles, section 5](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/best-practices) |

## Why these matter
- Legacy authentication: Microsoft says more than 97% of credential stuffing attacks and more than 99% of password spray attacks use legacy authentication. Legacy protocols can't do MFA
- Admin MFA: Microsoft says an account is 99.9% less likely to be compromised with MFA
- Over-privileged apps: apps can't do MFA. Some Graph permissions let an app make itself or others Global Admin
- Global Admin count: every Global Admin can take over the whole tenant

## High-risk Graph application permissions (check 3)
- High: `RoleManagement.ReadWrite.Directory`, `AppRoleAssignment.ReadWrite.All` - can grant admin roles or more permissions, a direct path to Global Admin
- High: `Application.ReadWrite.All` - can add credentials to other apps and act as them
- Medium: `Directory.ReadWrite.All`, `User.ReadWrite.All`, `Group.ReadWrite.All`, `Policy.ReadWrite.ConditionalAccess` - can change users, groups or security policies

## Not checked automatically (yet)
- PIM eligible role assignments
- Group membership inside Conditional Access policies (groups are listed, not resolved)
- Fewer than 10 privileged role assignments (Microsoft best practice, section 6)
