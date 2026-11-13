import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import {
  assertFails,
  assertSucceeds,
  initializeTestEnvironment,
} from '@firebase/rules-unit-testing';
import {
  collection,
  deleteDoc,
  doc,
  getDoc,
  getDocs,
  limit,
  onSnapshot,
  orderBy,
  query,
  serverTimestamp,
  setDoc,
  updateDoc,
  where,
  writeBatch,
} from 'firebase/firestore';

const projectId = 'demo-petcode-chat';
const reportId = 'report-one';
const conversationId = `${reportId}_visitor`;
let testEnvironment;

test('Firestore protects accounts, reports, private conversations, and moderation', async () => {
  testEnvironment = await initializeTestEnvironment({
    projectId,
    firestore: {
      rules: await readFile(new URL('../firestore.rules', import.meta.url), 'utf8'),
    },
  });

  await testEnvironment.clearFirestore();
  await testEnvironment.withSecurityRulesDisabled(async (context) => {
    const adminDb = context.firestore();
    await setDoc(doc(adminDb, 'reports', reportId), {
      reportType: 'found',
      species: 'cat',
      color: 'mixed',
      region: 'center',
      status: 'open',
      chatEnabled: true,
      createdAt: new Date(),
    });
    await setDoc(doc(adminDb, 'reportOwners', reportId), {
      ownerUid: 'owner',
      createdAt: new Date(),
    });
    await setDoc(doc(adminDb, 'reports', 'legacy-report'), {
      reportType: 'lost',
      species: 'dog',
      color: 'black',
      region: 'north',
      status: 'open',
      createdAt: new Date(),
    });
    await setDoc(doc(adminDb, 'admins', 'moderator'), { enabled: true });
    await setDoc(doc(adminDb, 'conversations', 'known-private-chat'), {
      reportId,
      createdBy: 'visitor',
      createdAt: new Date(),
      lastMessageAt: new Date(),
    });
  });

  const ownerDb = testEnvironment.authenticatedContext('owner', { email_verified: true }).firestore();
  const visitorDb = testEnvironment.authenticatedContext('visitor', { email_verified: true }).firestore();
  const outsiderDb = testEnvironment.authenticatedContext('outsider', { email_verified: true }).firestore();
  const moderatorDb = testEnvironment.authenticatedContext('moderator', { email_verified: true }).firestore();
  const unverifiedModeratorDb = testEnvironment.authenticatedContext('moderator', { email_verified: false }).firestore();
  const unverifiedDb = testEnvironment.authenticatedContext('unverified', { email_verified: false }).firestore();

  const publicReports = query(
    collection(testEnvironment.unauthenticatedContext().firestore(), 'reports'),
    where('status', '==', 'open'),
    orderBy('createdAt', 'desc'),
    limit(50),
  );
  const reportSnapshot = await assertSucceeds(getDocs(publicReports));
  assert.equal(reportSnapshot.size, 2);
  assert.equal(Object.hasOwn(reportSnapshot.docs[0].data(), 'ownerUid'), false);

  await assertFails(getDoc(doc(outsiderDb, 'reportOwners', reportId)));
  await assertFails(getDoc(doc(outsiderDb, 'conversations', 'known-private-chat')));
  await assertFails(getDocs(query(
    collection(outsiderDb, 'conversations', 'known-private-chat', 'messages'),
    limit(50),
  )));

  const ownerBatch = writeBatch(ownerDb);
  ownerBatch.set(doc(ownerDb, 'reports', 'new-report'), {
    reportType: 'lost',
    species: 'dog',
    color: 'black',
    region: 'north',
    status: 'open',
    chatEnabled: true,
    createdAt: serverTimestamp(),
  });
  ownerBatch.set(doc(ownerDb, 'reportOwners', 'new-report'), {
    ownerUid: 'owner',
    createdAt: serverTimestamp(),
  });
  await assertSucceeds(ownerBatch.commit());
  const foundReportBatch = writeBatch(ownerDb);
  foundReportBatch.set(doc(ownerDb, 'reports', 'found-with-handoff'), {
    reportType: 'found',
    species: 'dog',
    color: 'brown',
    region: 'center',
    status: 'open',
    chatEnabled: true,
    handoffOption: 'both',
    createdAt: serverTimestamp(),
  });
  foundReportBatch.set(doc(ownerDb, 'reportOwners', 'found-with-handoff'), {
    ownerUid: 'owner',
    createdAt: serverTimestamp(),
  });
  await assertSucceeds(foundReportBatch.commit());

  const lostReportWithHandoff = writeBatch(ownerDb);
  lostReportWithHandoff.set(doc(ownerDb, 'reports', 'lost-with-handoff'), {
    reportType: 'lost',
    species: 'dog',
    color: 'brown',
    region: 'center',
    status: 'open',
    chatEnabled: true,
    handoffOption: 'both',
    createdAt: serverTimestamp(),
  });
  lostReportWithHandoff.set(doc(ownerDb, 'reportOwners', 'lost-with-handoff'), {
    ownerUid: 'owner',
    createdAt: serverTimestamp(),
  });
  await assertFails(lostReportWithHandoff.commit());

  const reportWithPublicLocation = writeBatch(ownerDb);
  reportWithPublicLocation.set(doc(ownerDb, 'reports', 'found-with-location'), {
    reportType: 'found',
    species: 'dog',
    color: 'brown',
    region: 'center',
    status: 'open',
    chatEnabled: true,
    handoffOption: 'meetup',
    location: 'Exact street address',
    createdAt: serverTimestamp(),
  });
  reportWithPublicLocation.set(doc(ownerDb, 'reportOwners', 'found-with-location'), {
    ownerUid: 'owner',
    createdAt: serverTimestamp(),
  });
  await assertFails(reportWithPublicLocation.commit());

  await assertFails(setDoc(doc(unverifiedDb, 'reports', 'unverified-report'), {
    reportType: 'lost',
    species: 'dog',
    color: 'black',
    region: 'north',
    status: 'open',
    chatEnabled: true,
    createdAt: serverTimestamp(),
  }));
  await assertFails(setDoc(doc(outsiderDb, 'reportOwners', 'report-one'), {
    ownerUid: 'outsider',
    createdAt: serverTimestamp(),
  }));

  await assertSucceeds(setDoc(doc(visitorDb, 'conversations', conversationId), {
    reportId,
    createdBy: 'visitor',
    createdAt: serverTimestamp(),
    lastMessageAt: serverTimestamp(),
  }));
  await assertFails(setDoc(doc(visitorDb, 'conversations', 'legacy-report_visitor'), {
    reportId: 'legacy-report',
    createdBy: 'visitor',
    createdAt: serverTimestamp(),
    lastMessageAt: serverTimestamp(),
  }));
  await assertSucceeds(getDoc(doc(ownerDb, 'conversations', conversationId)));

  const visitorBatch = writeBatch(visitorDb);
  const firstMessage = doc(collection(visitorDb, 'conversations', conversationId, 'messages'));
  visitorBatch.set(firstMessage, {
    senderUid: 'visitor',
    text: 'Lo vimos cerca del parque central.',
    createdAt: serverTimestamp(),
  });
  visitorBatch.update(doc(visitorDb, 'conversations', conversationId), {
    lastMessageAt: serverTimestamp(),
  });
  await assertSucceeds(visitorBatch.commit());

  const privateMessages = query(
    collection(ownerDb, 'conversations', conversationId, 'messages'),
    orderBy('createdAt', 'desc'),
    limit(50),
  );
  assert.equal((await assertSucceeds(getDocs(privateMessages))).size, 1);

  const waitForTwoMessages = (db) => new Promise((resolve, reject) => {
    let stop;
    const timer = setTimeout(() => {
      stop?.();
      reject(new Error('The realtime message listener did not receive the second device update.'));
    }, 10000);
    stop = onSnapshot(
      query(
        collection(db, 'conversations', conversationId, 'messages'),
        orderBy('createdAt', 'desc'),
        limit(50),
      ),
      (snapshot) => {
        if (snapshot.size >= 2) {
          clearTimeout(timer);
          stop();
          resolve(snapshot.size);
        }
      },
      (error) => {
        clearTimeout(timer);
        stop?.();
        reject(error);
      },
    );
  });
  const ownerRealtime = waitForTwoMessages(ownerDb);
  const visitorRealtime = waitForTwoMessages(visitorDb);
  const nextMessage = writeBatch(visitorDb);
  nextMessage.set(doc(collection(visitorDb, 'conversations', conversationId, 'messages')), {
    senderUid: 'visitor',
    text: 'Gracias por avisar.',
    createdAt: serverTimestamp(),
  });
  nextMessage.update(doc(visitorDb, 'conversations', conversationId), {
    lastMessageAt: serverTimestamp(),
  });
  await assertSucceeds(nextMessage.commit());
  assert.deepEqual(await Promise.all([ownerRealtime, visitorRealtime]), [2, 2]);

  for (const unsafeText of [
    'Mi número es +57 300 123 4567',
    'Escríbeme a user@example.com',
    'Consulta https://example.com',
  ]) {
    const rejectedMessage = writeBatch(visitorDb);
    rejectedMessage.set(doc(collection(visitorDb, 'conversations', conversationId, 'messages')), {
      senderUid: 'visitor',
      text: unsafeText,
      createdAt: serverTimestamp(),
    });
    rejectedMessage.update(doc(visitorDb, 'conversations', conversationId), {
      lastMessageAt: serverTimestamp(),
    });
    await assertFails(rejectedMessage.commit());
  }

  await assertFails(updateDoc(doc(ownerDb, 'reports', reportId), { status: 'hidden' }));
  await assertSucceeds(updateDoc(doc(moderatorDb, 'reports', reportId), { status: 'hidden' }));
  await assertFails(updateDoc(doc(unverifiedModeratorDb, 'reports', reportId), { status: 'open' }));
  await assertFails(getDoc(doc(visitorDb, 'reports', reportId)));
  await assertFails(deleteDoc(doc(ownerDb, 'conversations', conversationId, 'messages', firstMessage.id)));
  await assertSucceeds(getDocs(query(
    collection(moderatorDb, 'conversations', conversationId, 'messages'),
    limit(50),
  )));
  await assertSucceeds(deleteDoc(doc(moderatorDb, 'conversations', conversationId, 'messages', firstMessage.id)));
  await assertFails(setDoc(doc(outsiderDb, 'admins', 'outsider'), { enabled: true }));

  await testEnvironment.cleanup();
  testEnvironment = null;
});
