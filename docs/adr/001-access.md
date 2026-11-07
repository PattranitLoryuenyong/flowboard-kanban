# Access model
Use Supabase Auth and database RLS with user access tokens. The API never uses a service-role secret. Private database helper functions check ownership/membership without recursive RLS. Admin RPC functions are privileged but explicitly check an immutable admin table and refuse self-suspension. Public registration cannot assign admin status.

Tradeoff: sharing requires the registered recipient’s user ID rather than email lookup, avoiding a public user directory. Suspended users may still authenticate but cannot access boards or cards.
