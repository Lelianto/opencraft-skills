# Firebase pack AI rules

- Authorize every Firestore/Storage read and write in security rules; never in client code.
- Never use the admin SDK in the client; privileged work runs in Cloud Functions.
- Model documents around access patterns; scope per-user data by uid in the path.
- Validate auth context in every callable function.
