# PetCode

PetCode is a Spanish-language lost-and-found pet bulletin board. Reports use
fixed-choice categories; a private owner mapping links a report to its account
without publishing the account ID. Conversations are visible only to the person
who opened a chat, the report owner, and moderators.

## Firebase setup

1. Register a Firebase Web app and enable **Authentication → Sign-in method →
   Email/Password**.
2. Create a Cloud Firestore database.
3. From the repository root, deploy the Firestore rules and indexes:

   ```sh
   firebase deploy --only firestore:rules,firestore:indexes --project petcode-rescue-samuel
   ```

   The rules in [`firestore.rules`](firestore.rules) allow public reads of the
   latest 50 visible reports, require verified accounts for posting and chat,
   keep report ownership private, and limit moderation to an administrator.
   The indexes in [`firestore.indexes.json`](firestore.indexes.json) support the
   live feed and conversation queries. Firestore Admin SDK writes bypass client
   rules; do not put untrusted documents in the `reports` collection.
4. Copy `.env.example` to `.env.local` and fill in the Firebase Web app values:

   ```dotenv
   VITE_FIREBASE_API_KEY=...
   VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your-project
   VITE_FIREBASE_APP_ID=...
   ```

5. From `petcode/`, install dependencies and start the development server:

   ```sh
   npm install
   npm run dev
   ```

The production build is `npm run build`. Vite writes it to `dist/` inside this folder, uses relative asset URLs (`base: './'`), and is completely independent and portable.

## Accounts, private chat, and administrator

Each user creates their own Firebase email/password account and verifies the
email address before posting or chatting. Passwords are never hard-coded or
shared between accounts. If a password is forgotten, enter the account email
and select **Olvidé mi contraseña** to request a reset link from Firebase.
Sign in on a second device with that user's individual credentials to see the
same account's reports and conversations; a different verified account can
start a private conversation from any visible report.
The live feed and chat use Firestore `onSnapshot` listeners.

When publishing a **found-pet** report, the person who currently has the pet
may optionally say they can arrange a public pickup point, bring the pet to an
agreed point, or either. This preference does not include a location; coordinate
the actual handoff in the private chat. The option is not offered for lost-pet
reports and is enforced by Firestore rules.

To grant moderator access, create a Firestore document at
`admins/<FIREBASE_AUTH_UID>` for the moderator's already-registered,
email-verified account. Its only field should be `enabled: true`. Get the UID
from **Firebase Console → Authentication → Users**. Only a trusted Firebase
project owner should create or revoke this document; all client writes to
`admins` are denied. Never put a moderator password or privileged credential
in the repository.

Moderators can hide/reopen reports and delete messages. Messages reject email
addresses, phone-number-like sequences, and web links, but automated checks
cannot detect every address or identifying detail. Users should not share
personal information in messages. Configure App Check, abuse monitoring, and
moderation/retention procedures before broad public use.

Run `npm test` from this directory for client-side message privacy checks.
From the repository root, run the following emulator-only command to exercise
authorization with separate owner, visitor, outsider, and moderator identities:

```sh
firebase emulators:exec --only firestore --project demo-petcode-chat "npm run test:rules --prefix petcode"
```

## Firebase Hosting deployment

The root `firebase.json` serves the generated `docs/petcode` directory, and
`.firebaserc` selects the `petcode-rescue-samuel` project. The
`Deploy PetCode to Firebase Hosting` GitHub Actions workflow builds and
publishes PetCode without replacing the main GitHub Pages site.

In the repository's **Settings → Secrets and variables → Actions**, add these
four repository **Variables**:

- `PETCODE_FIREBASE_API_KEY`
- `PETCODE_FIREBASE_AUTH_DOMAIN`
- `PETCODE_FIREBASE_PROJECT_ID`
- `PETCODE_FIREBASE_APP_ID`

Also add the repository **Secret**
`FIREBASE_SERVICE_ACCOUNT_PETCODE_RESCUE_SAMUEL`, containing the JSON for a
service account authorized to deploy to Firebase Hosting. Keep that JSON in
GitHub Secrets; never commit it or paste it into source files. Firebase Web
app configuration is public client configuration and is embedded in the
generated client bundle.

After adding the variables and secret, run the workflow manually once from
**Actions → Deploy PetCode to Firebase Hosting → Run workflow**, or push a
change under `petcode/`. The public URL is
`https://petcode-rescue-samuel.web.app/`.
