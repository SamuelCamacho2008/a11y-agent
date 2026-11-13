import { getApps, initializeApp } from 'firebase/app';
import {
  createUserWithEmailAndPassword,
  getAuth,
  onAuthStateChanged,
  reload,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
} from 'firebase/auth';
import {
  collection,
  deleteDoc,
  doc,
  getDoc,
  getFirestore,
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
import { isSafeChatMessage } from './chat-validation.js';
import { calculateRewardSplit } from './reward-calculator.js';

export const ADMIN_EMAIL = 'samuelcamachoaguirre4@gmail.com';

const requiredConfig = [
  'VITE_FIREBASE_API_KEY',
  'VITE_FIREBASE_AUTH_DOMAIN',
  'VITE_FIREBASE_PROJECT_ID',
  'VITE_FIREBASE_APP_ID',
];

const envSource = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env : (typeof process !== 'undefined' && process.env ? process.env : {});

const firebaseConfig = {
  apiKey: envSource.VITE_FIREBASE_API_KEY,
  authDomain: envSource.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: envSource.VITE_FIREBASE_PROJECT_ID,
  appId: envSource.VITE_FIREBASE_APP_ID,
};

const allowedValues = {
  reportType: ['lost', 'found'],
  species: ['dog', 'cat', 'other'],
  color: ['black', 'white', 'brown', 'gray', 'mixed', 'unknown'],
  region: [], // Validated dynamically for Popayán barrios
};

const reportFields = ['reportType', 'species', 'color', 'region'];
const handoffOptions = ['meetup', 'deliver', 'both'];
let services;

function getServices() {
  const missing = requiredConfig.filter((key) => !envSource[key]);
  if (missing.length > 0) {
    throw new Error(
      `Firebase configuration is missing: ${missing.join(', ')}. ` +
        'Set these VITE_FIREBASE_* variables and restart the app.',
    );
  }

  if (!services) {
    const app = getApps().length > 0 ? getApps()[0] : initializeApp(firebaseConfig);
    services = {
      auth: getAuth(app),
      db: getFirestore(app),
    };
  }

  return services;
}

function requireVerifiedUser() {
  const { auth } = getServices();
  if (!auth.currentUser) {
    throw new Error('auth/unauthenticated');
  }
  if (!auth.currentUser.emailVerified) {
    throw new Error('auth/email-not-verified');
  }
  return auth.currentUser;
}

function normalizeReport(report) {
  if (report === null || typeof report !== 'object' || Array.isArray(report)) {
    throw new TypeError('A report must be an object with the required fields.');
  }

  const validKeys = [
    ...reportFields,
    'handoffOption',
    'rewardAmount',
    'platformFeePercent',
    'specialConditions',
    'petName',
  ];
  const keys = Object.keys(report);
  if (
    keys.some((field) => !validKeys.includes(field)) ||
    !reportFields.every((field) => Object.prototype.hasOwnProperty.call(report, field))
  ) {
    throw new TypeError(`A report must contain ${reportFields.join(', ')}.`);
  }

  for (const field of reportFields) {
    if (field === 'region') {
      if (typeof report.region !== 'string' || !report.region.trim() || report.region.length > 80) {
        throw new TypeError('Invalid region / barrio value.');
      }
    } else if (!allowedValues[field].includes(report[field])) {
      throw new TypeError(`Invalid ${field} value: ${String(report[field])}.`);
    }
  }

  const hasHandoffOption = Object.prototype.hasOwnProperty.call(report, 'handoffOption') && report.handoffOption;
  if (
    hasHandoffOption &&
    (report.reportType !== 'found' || !handoffOptions.includes(report.handoffOption))
  ) {
    throw new TypeError('A handoff option is only valid for a found-pet report.');
  }

  const normalizedReport = {
    reportType: report.reportType,
    species: report.species,
    color: report.color,
    region: report.region.trim(),
  };
  if (hasHandoffOption) normalizedReport.handoffOption = report.handoffOption;

  if (report.petName && typeof report.petName === 'string' && report.petName.trim()) {
    normalizedReport.petName = report.petName.trim().slice(0, 100);
  }

  if (report.specialConditions && typeof report.specialConditions === 'string' && report.specialConditions.trim()) {
    normalizedReport.specialConditions = report.specialConditions.trim().slice(0, 500);
  }

  if (report.reportType === 'lost' && report.rewardAmount != null && report.rewardAmount !== '') {
    const amount = Number(report.rewardAmount);
    if (!Number.isNaN(amount) && amount > 0) {
      normalizedReport.rewardAmount = amount;
      normalizedReport.platformFeePercent = 5;
    }
  }

  return normalizedReport;
}

function recordsFromSnapshot(snapshot) {
  return snapshot.docs.map((entry) => ({
    id: entry.id,
    ...entry.data(),
  }));
}

function watchQuery(targetQuery, onUpdate, onError) {
  if (typeof onUpdate !== 'function') {
    throw new TypeError('A Firestore subscription requires an onUpdate callback.');
  }

  return onSnapshot(
    targetQuery,
    (snapshot) => onUpdate(recordsFromSnapshot(snapshot)),
    (error) => onError?.(error),
  );
}

export function watchAuth(onUpdate, onError) {
  if (typeof onUpdate !== 'function') {
    throw new TypeError('watchAuth requires an onUpdate callback.');
  }

  const { auth } = getServices();
  return onAuthStateChanged(auth, onUpdate, onError);
}

export async function registerAccount(email, password) {
  const { auth } = getServices();
  const credential = await createUserWithEmailAndPassword(
    auth,
    email.trim().toLowerCase(),
    password,
  );
  await sendEmailVerification(credential.user);
  return credential.user;
}

export async function signIn(email, password) {
  const { auth } = getServices();
  const credential = await signInWithEmailAndPassword(
    auth,
    email.trim().toLowerCase(),
    password,
  );
  return credential.user;
}

export async function resetPassword(email) {
  const { auth } = getServices();
  return sendPasswordResetEmail(auth, email.trim().toLowerCase());
}

export async function signOutAccount() {
  const { auth } = getServices();
  return signOut(auth);
}

export async function refreshCurrentUser() {
  const { auth } = getServices();
  if (!auth.currentUser) {
    throw new Error('auth/unauthenticated');
  }
  await reload(auth.currentUser);
  await auth.currentUser.getIdToken(true);
  return auth.currentUser;
}

export function watchAdminStatus(uid, onUpdate, onError) {
  if (typeof uid !== 'string' || !uid) {
    throw new TypeError('watchAdminStatus requires a user ID.');
  }
  const { db, auth } = getServices();
  const email = auth.currentUser?.email?.toLowerCase();
  if (email === ADMIN_EMAIL) {
    onUpdate(true);
  }
  return onSnapshot(
    doc(db, 'admins', uid),
    (snapshot) => {
      const isDocAdmin = snapshot.exists() && snapshot.data().enabled === true;
      const isAdminEmail = auth.currentUser?.email?.toLowerCase() === ADMIN_EMAIL;
      onUpdate(isDocAdmin || isAdminEmail);
    },
    (err) => {
      if (auth.currentUser?.email?.toLowerCase() === ADMIN_EMAIL) {
        onUpdate(true);
      } else {
        onError?.(err);
      }
    },
  );
}

export function watchReports(onUpdate, onError) {
  const { db } = getServices();
  return watchQuery(
    query(
      collection(db, 'reports'),
      where('status', '==', 'open'),
      orderBy('createdAt', 'desc'),
      limit(50),
    ),
    onUpdate,
    onError,
  );
}

export function watchModerationReports(onUpdate, onError) {
  const { db } = getServices();
  return watchQuery(
    query(collection(db, 'reports'), orderBy('createdAt', 'desc'), limit(50)),
    onUpdate,
    onError,
  );
}

export function watchOwnedReportIds(uid, onUpdate, onError) {
  const { db } = getServices();
  return onSnapshot(
    query(collection(db, 'reportOwners'), where('ownerUid', '==', uid), limit(50)),
    (snapshot) => onUpdate(snapshot.docs.map((entry) => entry.id)),
    onError,
  );
}

export function watchMyConversations(uid, onUpdate, onError) {
  const { db } = getServices();
  return watchQuery(
    query(
      collection(db, 'conversations'),
      where('createdBy', '==', uid),
      orderBy('lastMessageAt', 'desc'),
      limit(50),
    ),
    onUpdate,
    onError,
  );
}

export function watchReportConversations(reportId, onUpdate, onError) {
  const { db } = getServices();
  return watchQuery(
    query(
      collection(db, 'conversations'),
      where('reportId', '==', reportId),
      orderBy('lastMessageAt', 'desc'),
      limit(50),
    ),
    onUpdate,
    onError,
  );
}

export function watchAllConversations(onUpdate, onError) {
  const { db } = getServices();
  return watchQuery(
    query(collection(db, 'conversations'), orderBy('lastMessageAt', 'desc'), limit(50)),
    onUpdate,
    onError,
  );
}

export function watchMessages(conversationId, onUpdate, onError) {
  const { db } = getServices();
  return onSnapshot(
    query(
      collection(db, 'conversations', conversationId, 'messages'),
      orderBy('createdAt', 'desc'),
      limit(50),
    ),
    (snapshot) => onUpdate(recordsFromSnapshot(snapshot).reverse()),
    onError,
  );
}

export async function createReport(report) {
  const sanitizedReport = normalizeReport(report);
  const user = requireVerifiedUser();
  const { db } = getServices();
  const reportRef = doc(collection(db, 'reports'));
  const ownerRef = doc(db, 'reportOwners', reportRef.id);
  const batch = writeBatch(db);

  batch.set(reportRef, {
    ...sanitizedReport,
    status: 'open',
    chatEnabled: true,
    createdAt: serverTimestamp(),
  });
  batch.set(ownerRef, {
    ownerUid: user.uid,
    createdAt: serverTimestamp(),
  });

  await batch.commit();
  return reportRef;
}

export async function startConversation(reportId, rewardData = null) {
  const user = requireVerifiedUser();
  const { db } = getServices();
  const conversationId = `${reportId}_${user.uid}`;
  const conversationRef = doc(db, 'conversations', conversationId);
  try {
    const data = {
      reportId,
      createdBy: user.uid,
      createdAt: serverTimestamp(),
      lastMessageAt: serverTimestamp(),
    };
    if (rewardData && Number(rewardData.rewardAmount) > 0) {
      const split = calculateRewardSplit(rewardData.rewardAmount);
      data.rewardAmount = split.total;
      data.platformFeePercent = split.feePercent;
      data.platformFee = split.platformFee;
      data.finderPayout = split.finderPayout;
      data.paymentStatus = 'pending';
    }
    await setDoc(conversationRef, data);
    return conversationId;
  } catch (error) {
    if (error?.code !== 'permission-denied') throw error;
    const existing = await getDoc(conversationRef);
    if (existing.exists() && existing.data().createdBy === user.uid) {
      return conversationId;
    }
    throw error;
  }
}

export async function updateConversationPayment(conversationId, paymentDetails) {
  const user = requireVerifiedUser();
  const { db } = getServices();
  const conversationRef = doc(db, 'conversations', conversationId);
  const patch = {
    paymentStatus: paymentDetails.paymentStatus || 'paid',
    ...(paymentDetails.paymentMethod ? { paymentMethod: paymentDetails.paymentMethod } : {}),
    ...(paymentDetails.paymentNote ? { paymentNote: paymentDetails.paymentNote } : {}),
    paidAt: serverTimestamp(),
    paidBy: user.uid,
  };
  if (paymentDetails.rewardAmount) {
    const split = calculateRewardSplit(paymentDetails.rewardAmount);
    patch.rewardAmount = split.total;
    patch.platformFee = split.platformFee;
    patch.finderPayout = split.finderPayout;
  }
  return updateDoc(conversationRef, patch);
}

export async function sendMessage(conversationId, text) {
  const user = requireVerifiedUser();
  if (!isSafeChatMessage(text)) {
    throw new TypeError('message/unsafe-content');
  }

  const { db } = getServices();
  const conversationRef = doc(db, 'conversations', conversationId);
  const messageRef = doc(collection(conversationRef, 'messages'));
  const batch = writeBatch(db);

  batch.set(messageRef, {
    senderUid: user.uid,
    text: text.trim(),
    createdAt: serverTimestamp(),
  });
  batch.update(conversationRef, { lastMessageAt: serverTimestamp() });
  await batch.commit();
  return messageRef;
}

export async function getReport(reportId) {
  const { db } = getServices();
  const snap = await getDoc(doc(db, 'reports', reportId));
  if (!snap.exists()) return null;
  return { id: snap.id, ...snap.data() };
}

export async function setReportVisibility(reportId, status) {
  if (!['open', 'hidden'].includes(status)) {
    throw new TypeError('Invalid report visibility.');
  }
  const { db } = getServices();
  return updateDoc(doc(db, 'reports', reportId), { status });
}

export async function deleteReport(reportId) {
  const { db } = getServices();
  const batch = writeBatch(db);
  batch.delete(doc(db, 'reports', reportId));
  batch.delete(doc(db, 'reportOwners', reportId));
  return batch.commit();
}

export async function deleteMessage(conversationId, messageId) {
  const { db } = getServices();
  return deleteDoc(doc(db, 'conversations', conversationId, 'messages', messageId));
}

export { isSafeChatMessage, normalizeReport };
