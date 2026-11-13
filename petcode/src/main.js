import {
  ADMIN_EMAIL,
  createReport,
  deleteMessage,
  deleteReport,
  getReport,
  isSafeChatMessage,
  refreshCurrentUser,
  registerAccount,
  resetPassword,
  sendMessage,
  setReportVisibility,
  signIn,
  signOutAccount,
  startConversation,
  updateConversationPayment,
  watchAdminStatus,
  watchAllConversations,
  watchAuth,
  watchMessages,
  watchModerationReports,
  watchMyConversations,
  watchOwnedReportIds,
  watchReportConversations,
  watchReports,
} from './firebase.js';
import { calculateRewardSplit, formatCurrency } from './reward-calculator.js';
import { POPAYAN_BARRIOS, getBarrioLabel } from './popayan-barrios.js';
import QRCode from 'qrcode';

// Legacy test notices to clean from feed & database
const LEGACY_TEST_IDS = new Set([
  'WEdni3eWbFYQSIvL3H5J',
  'jWKQhWrKAw821FVdGJxq',
  'nnnlKJupqTV5Bc23RSXe',
]);

// DOM elements - Reports and Feed
const form = document.querySelector('#report-form');
const petNameInput = document.querySelector('#pet-name');
const specialConditionsInput = document.querySelector('#special-conditions');
const feedStatus = document.querySelector('#feed-status');
const feedError = document.querySelector('#feed-error');
const feedErrorDetail = document.querySelector('#feed-error-detail');
const reportList = document.querySelector('#report-list');
const formError = document.querySelector('#form-error');
const formSuccess = document.querySelector('#form-success');
const submitButton = form.querySelector('button[type="submit"]');

// Feed Filters
const filterBarrio = document.querySelector('#filter-barrio');
const filterSpecies = document.querySelector('#filter-species');

// DOM elements - Account & Forms
const accountForm = document.querySelector('#account-form');
const accountEmail = document.querySelector('#account-email');
const accountPassword = document.querySelector('#account-password');
const handoffField = document.querySelector('.handoff-field');
const handoffOption = document.querySelector('#handoff-option');
const accountCurrent = document.querySelector('#account-current');
const accountSummary = document.querySelector('#account-summary');
const accountMessage = document.querySelector('#account-message');

// DOM elements - Header & Account Menu Modal
const accountMenuButton = document.querySelector('#account-menu-button');
const headerAvatar = document.querySelector('#header-avatar');
const headerAccountLabel = document.querySelector('#header-account-label');
const headerActiveChatsBadge = document.querySelector('#header-active-chats-badge');
const accountMenuModal = document.querySelector('#account-menu-modal');
const accountMenuBackdrop = document.querySelector('#account-menu-backdrop');
const closeAccountMenuButton = document.querySelector('#close-account-menu-button');
const menuLoggedInContent = document.querySelector('#menu-logged-in-content');
const menuLoggedOutContent = document.querySelector('#menu-logged-out-content');
const menuUserAvatar = document.querySelector('#menu-user-avatar');
const menuUserEmail = document.querySelector('#menu-user-email');
const menuRoleBadge = document.querySelector('#menu-role-badge');
const menuVerifiedBadge = document.querySelector('#menu-verified-badge');
const menuChatsCounter = document.querySelector('#menu-chats-counter');
const menuReportsCounter = document.querySelector('#menu-reports-counter');
const menuAdminLink = document.querySelector('#menu-admin-link');
const menuVerifyButton = document.querySelector('#menu-verify-button');
const menuSignOutButton = document.querySelector('#menu-sign-out-button');
const menuGoSigninButton = document.querySelector('#menu-go-signin-button');

// DOM elements - Reward Field in Report Form
const rewardFieldContainer = document.querySelector('#reward-field-container');
const rewardAmountInput = document.querySelector('#reward-amount');
const rewardBreakdownCard = document.querySelector('#reward-breakdown-card');
const rewardCalcTotal = document.querySelector('#reward-calc-total');
const rewardCalcFinder = document.querySelector('#reward-calc-finder');
const rewardCalcFee = document.querySelector('#reward-calc-fee');

// DOM elements - Conversations & Chat
const conversationsPanel = document.querySelector('#conversations-panel');
const conversationList = document.querySelector('#conversation-list');
const chatPanel = document.querySelector('#chat-panel');
const chatMessages = document.querySelector('#chat-messages');
const chatContext = document.querySelector('#chat-context');
const messageForm = document.querySelector('#message-form');
const messageText = document.querySelector('#message-text');
const messageError = document.querySelector('#message-error');

// DOM elements - Chat Reward Box
const chatRewardContainer = document.querySelector('#chat-reward-container');
const chatRewardTotalText = document.querySelector('#chat-reward-total-text');
const chatRewardBreakdownText = document.querySelector('#chat-reward-breakdown-text');
const chatPaymentStatusBadge = document.querySelector('#chat-payment-status-badge');
const chatRewardActions = document.querySelector('#chat-reward-actions');

// DOM elements - Admin Panel
const adminPanel = document.querySelector('#admin-panel');
const adminReportList = document.querySelector('#admin-report-list');
const adminConversationList = document.querySelector('#admin-conversation-list');
const adminOperatorEmail = document.querySelector('#admin-operator-email');
const adminTotalFees = document.querySelector('#admin-total-fees');
const adminTotalPayouts = document.querySelector('#admin-total-payouts');
const adminTotalRewards = document.querySelector('#admin-total-rewards');
const adminCleanLegacyBtn = document.querySelector('#admin-clean-legacy-btn');
const adminCleanStatus = document.querySelector('#admin-clean-status');

// DOM elements - QR Modal
const qrModal = document.querySelector('#qr-modal');
const qrModalBackdrop = document.querySelector('#qr-modal-backdrop');
const closeQrModalButton = document.querySelector('#close-qr-modal-button');
const qrModalImage = document.querySelector('#qr-modal-image');
const qrModalPetName = document.querySelector('#qr-modal-pet-name');
const qrModalPetSub = document.querySelector('#qr-modal-pet-sub');
const qrSummarySpecies = document.querySelector('#qr-summary-species');
const qrSummaryLocation = document.querySelector('#qr-summary-location');
const qrSummaryConditionBox = document.querySelector('#qr-summary-condition-box');
const qrSummaryConditionText = document.querySelector('#qr-summary-condition-text');
const qrSummaryRewardBox = document.querySelector('#qr-summary-reward-box');
const qrSummaryRewardText = document.querySelector('#qr-summary-reward-text');
const downloadQrBtn = document.querySelector('#download-qr-btn');
const printQrBtn = document.querySelector('#print-qr-btn');
const copyQrLinkBtn = document.querySelector('#copy-qr-link-btn');
const qrCopyFeedback = document.querySelector('#qr-copy-feedback');

// DOM elements - Scanned Pet Modal
const scannedPetModal = document.querySelector('#scanned-pet-modal');
const scannedModalBackdrop = document.querySelector('#scanned-modal-backdrop');
const closeScannedModalButton = document.querySelector('#close-scanned-modal-button');
const scannedAvatarIcon = document.querySelector('#scanned-avatar-icon');
const scannedPetName = document.querySelector('#scanned-pet-name');
const scannedSpeciesPill = document.querySelector('#scanned-species-pill');
const scannedBarrioPill = document.querySelector('#scanned-barrio-pill');
const scannedTypePill = document.querySelector('#scanned-type-pill');
const scannedHealthBox = document.querySelector('#scanned-health-box');
const scannedHealthText = document.querySelector('#scanned-health-text');
const scannedRewardBox = document.querySelector('#scanned-reward-box');
const scannedRewardTitle = document.querySelector('#scanned-reward-title');
const scannedRewardDetails = document.querySelector('#scanned-reward-details');
const scannedStartChatBtn = document.querySelector('#scanned-start-chat-btn');

const labels = {
  reportType: { lost: 'Se perdió', found: 'Fue encontrada' },
  species: { dog: 'Perro', cat: 'Gato', other: 'Otro' },
  color: {
    black: 'Negro',
    white: 'Blanco',
    brown: 'Marrón',
    gray: 'Gris',
    mixed: 'Varios colores',
    unknown: 'No se sabe',
  },
  region: {
    north: 'Norte (Popayán)',
    center: 'Centro (Popayán)',
    south: 'Sur (Popayán)',
    east: 'Oriente (Popayán)',
    west: 'Occidente (Popayán)',
    unspecified: 'Popayán (Sin especificar)',
  },
};
const handoffLabels = {
  meetup: 'Acordar un punto público para recogerla',
  deliver: 'Puede llevarla a un punto acordado',
  both: 'Puede hacer cualquiera de las dos',
};

const allowedValues = {
  reportType: new Set(['lost', 'found']),
  species: new Set(['dog', 'cat', 'other']),
  color: new Set(['black', 'white', 'brown', 'gray', 'mixed', 'unknown']),
  region: new Set([
    ...POPAYAN_BARRIOS.map((b) => b.id),
    'north',
    'center',
    'south',
    'east',
    'west',
    'unspecified',
  ]),
};

const reports = new Map();
let rawFeedReports = [];
let pendingScannedPetId = null;
let currentQrDataUrl = null;
let currentQrPetUrl = null;

const conversations = new Map();
const ownerConversationStops = new Map();
const ownedReportIds = new Set();
let moderationReports = [];
let currentUser = null;
let currentUserIsAdmin = false;
let activeConversationId = null;
let stopAdminStatus = null;
let stopOwnedReports = null;
let stopMyConversations = null;
let stopAdminReports = null;
let stopAdminConversations = null;
let stopMessages = null;

function getReportTime(report) {
  const rawTime = report?.createdAt;
  if (!rawTime) return null;

  const date = typeof rawTime.toDate === 'function' ? rawTime.toDate() : new Date(rawTime);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatTime(rawTime) {
  if (!rawTime) return 'Hora no disponible';
  const date = typeof rawTime.toDate === 'function' ? rawTime.toDate() : new Date(rawTime);
  if (Number.isNaN(date.getTime())) return 'Hora no disponible';
  return new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function reportTitle(report) {
  const type = labels.reportType[report?.reportType] ?? 'Aviso';
  const species = labels.species[report?.species] ?? labels.species.other;
  const color = labels.color[report?.color] ?? labels.color.unknown;
  const region = getBarrioLabel(report?.region);
  const namePart = report?.petName?.trim() ? ` · "${report.petName.trim()}"` : '';
  return `${type}: ${species} · ${color} · ${region}${namePart}`;
}

function formatReportTime(report) {
  return formatTime(getReportTime(report));
}

function makeButton(text, className, onClick) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = className;
  button.textContent = text;
  button.addEventListener('click', onClick);
  return button;
}

// Filter conversations strictly so only direct participants (or admin) can see them
function getUserVisibleConversations() {
  if (!currentUser?.emailVerified) return [];
  return [...conversations.values()].filter((conv) => {
    if (currentUserIsAdmin) return true;
    return conv.createdBy === currentUser.uid || ownedReportIds.has(conv.reportId);
  });
}

function updateAccountMenuState() {
  if (!accountMenuModal) return;

  if (!currentUser) {
    if (headerAvatar) headerAvatar.textContent = '👤';
    if (headerAccountLabel) headerAccountLabel.textContent = 'Mi cuenta';
    if (headerActiveChatsBadge) headerActiveChatsBadge.hidden = true;
    if (menuLoggedInContent) menuLoggedInContent.hidden = true;
    if (menuLoggedOutContent) menuLoggedOutContent.hidden = false;
    if (menuAdminLink) menuAdminLink.hidden = true;
    return;
  }

  const email = currentUser.email || 'Usuario';
  const initial = email[0].toUpperCase();
  if (headerAvatar) headerAvatar.textContent = initial;
  if (headerAccountLabel) headerAccountLabel.textContent = email.split('@')[0];

  if (menuLoggedInContent) menuLoggedInContent.hidden = false;
  if (menuLoggedOutContent) menuLoggedOutContent.hidden = true;
  if (menuUserAvatar) menuUserAvatar.textContent = initial;
  if (menuUserEmail) menuUserEmail.textContent = email;

  const isAdmin = currentUserIsAdmin || email.toLowerCase() === ADMIN_EMAIL.toLowerCase();
  if (menuRoleBadge) {
    if (isAdmin) {
      menuRoleBadge.textContent = '🛡️ Administrador';
      menuRoleBadge.className = 'role-badge admin-badge';
    } else {
      menuRoleBadge.textContent = 'Usuario Comunitario';
      menuRoleBadge.className = 'role-badge';
    }
  }

  if (menuAdminLink) {
    menuAdminLink.hidden = !isAdmin;
  }

  if (menuVerifiedBadge) {
    if (currentUser.emailVerified) {
      menuVerifiedBadge.textContent = '✓ Verificado';
      menuVerifiedBadge.className = 'verified-badge is-verified';
      if (menuVerifyButton) menuVerifyButton.hidden = true;
    } else {
      menuVerifiedBadge.textContent = '✉ Pendiente verificación';
      menuVerifiedBadge.className = 'verified-badge';
      if (menuVerifyButton) menuVerifyButton.hidden = false;
    }
  }

  const visibleConversations = getUserVisibleConversations();
  if (menuChatsCounter) menuChatsCounter.textContent = String(visibleConversations.length);
  if (headerActiveChatsBadge) {
    if (visibleConversations.length > 0) {
      headerActiveChatsBadge.textContent = String(visibleConversations.length);
      headerActiveChatsBadge.hidden = false;
    } else {
      headerActiveChatsBadge.hidden = true;
    }
  }

  const navChatsBadge = document.querySelector('#nav-chats-badge');
  if (navChatsBadge) {
    if (visibleConversations.length > 0) {
      navChatsBadge.textContent = String(visibleConversations.length);
      navChatsBadge.hidden = false;
    } else {
      navChatsBadge.hidden = true;
    }
  }

  if (menuReportsCounter) menuReportsCounter.textContent = String(ownedReportIds.size);

  // Synchronize In-Page Account Section (#cuenta)
  const profileAvatar = document.querySelector('#profile-avatar');
  const profileEmail = document.querySelector('#profile-email');
  const profileRoleBadge = document.querySelector('#profile-role-badge');
  const profileVerifiedBadge = document.querySelector('#profile-verified-badge');
  const profileVerificationHint = document.querySelector('#profile-verification-hint');
  const profileRoleTitle = document.querySelector('#profile-role-title');
  const profileRoleDesc = document.querySelector('#profile-role-desc');
  const profileStats = document.querySelector('#profile-stats');
  const profileAdminBtn = document.querySelector('#profile-admin-btn');

  if (profileAvatar) profileAvatar.textContent = initial;
  if (profileEmail) profileEmail.textContent = email;
  if (profileRoleBadge) {
    profileRoleBadge.textContent = isAdmin ? '🛡️ Administrador del Sistema' : 'Usuario Comunitario';
    profileRoleBadge.className = isAdmin ? 'badge-role-admin' : 'badge-verified';
  }
  if (profileRoleTitle) profileRoleTitle.textContent = isAdmin ? 'Administrador del Sistema' : 'Usuario Comunitario';
  if (profileRoleDesc) {
    profileRoleDesc.textContent = isAdmin
      ? `${email} tiene permisos de administrador para auditar pagos de recompensas (5% PetCode) y supervisar avisos comunitarios.`
      : 'Puedes publicar avisos, pactar recompensas y conversar privadamente de forma segura.';
  }
  if (profileVerifiedBadge) {
    profileVerifiedBadge.textContent = currentUser.emailVerified ? '✓ Verificado' : '✉ Pendiente verificación';
    profileVerifiedBadge.className = currentUser.emailVerified ? 'badge-verified' : 'badge-role-admin';
  }
  if (profileVerificationHint) {
    profileVerificationHint.textContent = currentUser.emailVerified
      ? 'Cuenta verificada. Tienes acceso completo a moderar avisos, auditar recompensas y chatear con seguridad.'
      : 'Revisa tu bandeja de entrada y confirma tu correo para chatear y publicar.';
  }
  if (profileStats) {
    profileStats.textContent = `${visibleConversations.length} chats privados · ${ownedReportIds.size} avisos publicados`;
  }
  if (profileAdminBtn) {
    profileAdminBtn.hidden = !isAdmin;
  }
}

function openAccountMenu() {
  if (!accountMenuModal) return;
  accountMenuModal.hidden = false;
  accountMenuModal.setAttribute('aria-hidden', 'false');
  accountMenuButton?.setAttribute('aria-expanded', 'true');
  updateAccountMenuState();
}

function closeAccountMenu() {
  if (!accountMenuModal) return;
  accountMenuModal.hidden = true;
  accountMenuModal.setAttribute('aria-hidden', 'true');
  accountMenuButton?.setAttribute('aria-expanded', 'false');
}

function updateRewardBreakdown() {
  if (!rewardAmountInput || !rewardBreakdownCard) return;
  const val = rewardAmountInput.value;
  const split = calculateRewardSplit(val);
  if (split.total > 0) {
    rewardBreakdownCard.hidden = false;
    rewardCalcTotal.textContent = `$${formatCurrency(split.total)}`;
    rewardCalcFinder.textContent = `$${formatCurrency(split.finderPayout)}`;
    rewardCalcFee.textContent = `$${formatCurrency(split.platformFee)}`;
  } else {
    rewardBreakdownCard.hidden = true;
  }
}

async function showQrModalForReport(report) {
  if (!qrModal) return;
  const origin = window.location.origin;
  const pathname = window.location.pathname;
  const petUrl = report?.id ? `${origin}${pathname}?pet=${report.id}` : `${origin}${pathname}`;
  currentQrPetUrl = petUrl;

  try {
    const dataUrl = await QRCode.toDataURL(petUrl, {
      width: 320,
      margin: 2,
      color: {
        dark: '#1e3329',
        light: '#ffffff',
      },
    });
    currentQrDataUrl = dataUrl;
    if (qrModalImage) qrModalImage.src = dataUrl;
  } catch (err) {
    console.error('[petcode] QR code generation error:', err);
  }

  const petDisplayName = report?.petName?.trim() || labels.species[report?.species] || 'Mascota';
  if (qrModalPetName) qrModalPetName.textContent = petDisplayName;
  if (qrModalPetSub) qrModalPetSub.textContent = 'Escanéame con la cámara de tu celular';

  if (qrSummarySpecies) {
    const sp = labels.species[report?.species] || report?.species || 'Mascota';
    const col = labels.color[report?.color] || report?.color || '';
    qrSummarySpecies.textContent = `${sp} · ${col}${report?.petName ? ` ("${report.petName.trim()}")` : ''}`;
  }
  if (qrSummaryLocation) {
    qrSummaryLocation.textContent = getBarrioLabel(report?.region);
  }

  if (qrSummaryConditionBox && qrSummaryConditionText) {
    if (report?.specialConditions?.trim()) {
      qrSummaryConditionText.textContent = report.specialConditions.trim();
      qrSummaryConditionBox.hidden = false;
    } else {
      qrSummaryConditionBox.hidden = true;
    }
  }

  if (qrSummaryRewardBox && qrSummaryRewardText) {
    if (report?.rewardAmount && Number(report.rewardAmount) > 0) {
      const split = calculateRewardSplit(report.rewardAmount);
      qrSummaryRewardText.textContent = `$${formatCurrency(split.total)} COP (95% para quien la encuentre: $${formatCurrency(split.finderPayout)} · 5% PetCode: $${formatCurrency(split.platformFee)})`;
      qrSummaryRewardBox.hidden = false;
    } else {
      qrSummaryRewardBox.hidden = true;
    }
  }

  if (qrCopyFeedback) qrCopyFeedback.hidden = true;
  qrModal.hidden = false;
  qrModal.setAttribute('aria-hidden', 'false');
}

function closeQrModal() {
  if (!qrModal) return;
  qrModal.hidden = true;
  qrModal.setAttribute('aria-hidden', 'true');
}

async function openScannedPetModal(petId) {
  if (!scannedPetModal) return;
  let report = reports.get(petId);
  if (!report) {
    try {
      report = await getReport(petId);
      if (report) reports.set(report.id, report);
    } catch (e) {
      console.warn('[petcode] Could not fetch scanned pet report from Firestore:', e);
    }
  }

  const speciesName = labels.species[report?.species] || 'Mascota';
  const colorName = labels.color[report?.color] || '';
  const barrioName = getBarrioLabel(report?.region);
  const petName = report?.petName?.trim() || `${speciesName} identificado`;

  if (scannedAvatarIcon) {
    scannedAvatarIcon.textContent = report?.species === 'cat' ? '🐱' : (report?.species === 'dog' ? '🐕' : '🐾');
  }
  if (scannedPetName) scannedPetName.textContent = petName;
  if (scannedSpeciesPill) scannedSpeciesPill.textContent = `${speciesName} · ${colorName}`;
  if (scannedBarrioPill) scannedBarrioPill.textContent = `📍 ${barrioName}`;
  if (scannedTypePill) {
    scannedTypePill.textContent = report?.reportType === 'lost' ? 'Buscada por su dueño' : 'Mascota comunitaria';
  }

  // Cuidados Médicos y Salud Especial ("si tiene algún problema")
  if (scannedHealthBox && scannedHealthText) {
    if (report?.specialConditions?.trim()) {
      scannedHealthText.textContent = report.specialConditions.trim();
      scannedHealthBox.className = 'scanned-health-card has-condition';
    } else {
      scannedHealthText.textContent = 'Sin problemas de salud ni cuidados especiales conocidos reportados.';
      scannedHealthBox.className = 'scanned-health-card';
    }
  }

  // Recompensa ofrecida
  if (scannedRewardBox) {
    if (report?.rewardAmount && Number(report.rewardAmount) > 0) {
      const split = calculateRewardSplit(report.rewardAmount);
      if (scannedRewardTitle) scannedRewardTitle.textContent = `Recompensa ofrecida: $${formatCurrency(split.total)} COP`;
      if (scannedRewardDetails) {
        scannedRewardDetails.textContent = `🐾 95% para ti ($${formatCurrency(split.finderPayout)} COP) por cuidarla y entregarla · 🛡️ 5% PetCode ($${formatCurrency(split.platformFee)} COP)`;
      }
      scannedRewardBox.hidden = false;
    } else {
      scannedRewardBox.hidden = true;
    }
  }

  if (scannedStartChatBtn) {
    scannedStartChatBtn.onclick = () => {
      closeScannedModal();
      if (currentUser?.emailVerified) {
        openConversationForReport(petId, report?.rewardAmount);
      } else {
        const accountSection = document.querySelector('#cuenta');
        accountSection?.scrollIntoView({ behavior: 'smooth' });
        if (accountMessage) {
          accountMessage.textContent = 'Inicia sesión o regístrate para abrir el chat privado seguro con el dueño de esta mascota.';
        }
      }
    };
  }

  scannedPetModal.hidden = false;
  scannedPetModal.setAttribute('aria-hidden', 'false');
}

function closeScannedModal() {
  if (!scannedPetModal) return;
  scannedPetModal.hidden = true;
  scannedPetModal.setAttribute('aria-hidden', 'true');
}

function checkScannedPetUrl() {
  try {
    const params = new URLSearchParams(window.location.search);
    const petId = params.get('pet');
    if (petId) {
      pendingScannedPetId = petId;
      openScannedPetModal(petId);
    }
  } catch (err) {
    console.error('[petcode] error reading URL params:', err);
  }
}

function initPopayanFilters() {
  if (filterBarrio && filterBarrio.children.length <= 1) {
    POPAYAN_BARRIOS.forEach((b) => {
      const opt = document.createElement('option');
      opt.value = b.id;
      opt.textContent = `${b.name} (${b.comuna})`;
      filterBarrio.appendChild(opt);
    });
    filterBarrio.addEventListener('change', () => {
      renderReports(rawFeedReports);
    });
  }
  filterSpecies?.addEventListener('change', () => {
    renderReports(rawFeedReports);
  });
}

function renderReports(reportRecords) {
  if (Array.isArray(reportRecords)) {
    rawFeedReports = reportRecords;
  }
  const source = Array.isArray(rawFeedReports) ? rawFeedReports : [];

  reportList.replaceChildren();
  reports.clear();
  source.forEach((report) => reports.set(report.id, report));

  if (pendingScannedPetId && reports.has(pendingScannedPetId)) {
    openScannedPetModal(pendingScannedPetId);
  }

  // Filter out legacy test IDs and hidden notices
  const cleanReports = source.filter((report) => !LEGACY_TEST_IDS.has(report.id) && report.status !== 'hidden');

  // Filter by Barrio and Species
  const barrioFilter = filterBarrio?.value || 'all';
  const speciesFilter = filterSpecies?.value || 'all';

  const visibleReports = cleanReports.filter((report) => {
    if (barrioFilter !== 'all' && report.region !== barrioFilter) return false;
    if (speciesFilter !== 'all' && report.species !== speciesFilter) return false;
    return true;
  });

  if (visibleReports.length === 0) {
    feedStatus.hidden = false;
    feedStatus.classList.add('is-empty');
    if (cleanReports.length > 0) {
      feedStatus.innerHTML = '<span class="empty-mark" aria-hidden="true">🔍</span><strong>No hay avisos para estos filtros</strong><span>Prueba seleccionando otro sector o especie en Popayán.</span>';
    } else {
      feedStatus.innerHTML = '<span class="empty-mark" aria-hidden="true">♡</span><strong>Aún no hay avisos en Popayán</strong><span>Sé la primera persona en publicar un aviso comunitario.</span>';
    }
    reportList.setAttribute('aria-busy', 'false');
    feedError.hidden = true;
    renderAdminReports();
    return;
  }

  feedStatus.hidden = true;
  feedError.hidden = true;
  reportList.setAttribute('aria-busy', 'false');

  visibleReports.forEach((report) => {
    const card = document.createElement('article');
    card.className = 'report-card';

    const symbol = document.createElement('span');
    symbol.className = `report-symbol ${report.reportType === 'lost' ? 'lost-symbol' : 'found-symbol'}`;
    symbol.setAttribute('aria-hidden', 'true');
    symbol.textContent = report.reportType === 'lost' ? '↗' : '⌂';

    const content = document.createElement('div');
    content.className = 'report-content';

    const heading = document.createElement('div');
    heading.className = 'report-card-heading';
    const title = document.createElement('h4');
    const typeLabel = labels.reportType[report.reportType] ?? 'Aviso';
    if (report.petName && report.petName.trim()) {
      title.innerHTML = `<strong>${escapeHtml(report.petName.trim())}</strong> <span class="report-type-badge ${report.reportType}">${typeLabel}</span>`;
    } else {
      title.textContent = typeLabel;
    }

    const time = document.createElement('time');
    const date = getReportTime(report);
    if (date) time.dateTime = date.toISOString();
    time.textContent = formatReportTime(report);
    heading.append(title, time);

    const details = document.createElement('p');
    details.className = 'report-details';
    const sp = labels.species[report.species] ?? report.species;
    const col = labels.color[report.color] ?? report.color;
    const bar = getBarrioLabel(report.region);
    details.textContent = `${sp} · ${col} · 📍 ${bar}`;
    content.append(heading, details);

    // Special health conditions or medical problems callout ("si tiene algun problema")
    if (report.specialConditions && report.specialConditions.trim()) {
      const conditionBadge = document.createElement('div');
      conditionBadge.className = 'pet-condition-badge';
      conditionBadge.innerHTML = `<span class="condition-icon" aria-hidden="true">🩺</span> <div><strong>Condición de salud / Atención:</strong> <span>${escapeHtml(report.specialConditions.trim())}</span></div>`;
      content.append(conditionBadge);
    }

    // If report has reward, show badge with 95% finder / 5% PetCode split
    if (report.rewardAmount && Number(report.rewardAmount) > 0) {
      const split = calculateRewardSplit(report.rewardAmount);
      const rewardTag = document.createElement('div');
      rewardTag.className = 'reward-tag';
      rewardTag.innerHTML = `<span class="reward-tag-icon" aria-hidden="true">🎁</span> <strong>Recompensa: $${formatCurrency(split.total)}</strong> <span class="reward-tag-sub">95% rescatista ($${formatCurrency(split.finderPayout)}) · 5% PetCode ($${formatCurrency(split.platformFee)})</span>`;
      content.append(rewardTag);
    }

    if (report.reportType === 'found' && handoffLabels[report.handoffOption]) {
      const handoff = document.createElement('p');
      handoff.className = 'handoff-hint';
      handoff.textContent = `Entrega opcional: ${handoffLabels[report.handoffOption]}. Acuerden el lugar por el chat privado.`;
      content.append(handoff);
    }

    const actions = document.createElement('div');
    actions.className = 'report-actions';

    // Button to inspect or print QR Placa
    actions.append(makeButton('🏷️ Placa QR', 'secondary-button qr-action-btn', () => {
      showQrModalForReport(report);
    }));

    if (!report.chatEnabled) {
      const ownerLabel = document.createElement('span');
      ownerLabel.className = 'owner-label';
      ownerLabel.textContent = 'Chat no disponible';
      actions.append(ownerLabel);
    } else if (ownedReportIds.has(report.id)) {
      const ownerLabel = document.createElement('span');
      ownerLabel.className = 'owner-label';
      ownerLabel.textContent = 'Tu aviso';
      actions.append(ownerLabel);
    } else if (currentUser?.emailVerified) {
      actions.append(makeButton('Iniciar conversación', 'text-button', () => {
        openConversationForReport(report.id, report.rewardAmount);
      }));
    } else {
      const signInLink = document.createElement('a');
      signInLink.className = 'text-button';
      signInLink.href = '#cuenta';
      signInLink.textContent = currentUser ? 'Verifica tu correo para conversar' : 'Inicia sesión para conversar';
      actions.append(signInLink);
    }

    card.append(symbol, content, actions);
    reportList.append(card);
  });

  renderAdminReports();
}

function showListenerError(error) {
  console.error('[petcode] Could not load Firestore reports:', error);
  const connStatus = document.querySelector('#feed-connection-status');
  if (connStatus) connStatus.textContent = 'Sin conexión';
  feedStatus.hidden = true;
  feedError.hidden = false;
  reportList.setAttribute('aria-busy', 'false');
  if (error?.message?.startsWith('Firebase configuration is missing')) {
    feedErrorDetail.textContent = 'Falta configurar Firebase para habilitar los avisos.';
  } else if (error?.code === 'permission-denied') {
    feedErrorDetail.textContent = 'Firebase rechazó la consulta. Verifica las reglas de Firestore.';
  } else {
    feedErrorDetail.textContent = 'No fue posible conectarse para recibir avisos. Comprueba tu conexión e inténtalo más tarde.';
  }
}

function showFormError(message) {
  formError.textContent = message;
  formError.hidden = false;
  formSuccess.hidden = true;
}

function accountErrorText(error) {
  const code = error?.code ?? error?.message;
  const messages = {
    'auth/email-already-in-use': 'Ese correo ya tiene una cuenta. Inicia sesión.',
    'auth/invalid-email': 'Escribe un correo electrónico válido.',
    'auth/invalid-credential': 'No coincide el correo con la contraseña.',
    'auth/user-disabled': 'Esta cuenta está deshabilitada.',
    'auth/too-many-requests': 'Hubo muchos intentos. Espera un momento e inténtalo de nuevo.',
    'auth/weak-password': 'Usa una contraseña de al menos 8 caracteres.',
    'auth/network-request-failed': 'No hay conexión con Firebase. Inténtalo de nuevo.',
  };
  return messages[code] ?? 'No pudimos completar la acción. Revisa los datos e inténtalo de nuevo.';
}

function resetUserSubscriptions() {
  stopAdminStatus?.();
  stopAdminStatus = null;
  stopOwnedReports?.();
  stopOwnedReports = null;
  stopMyConversations?.();
  stopMyConversations = null;
  stopAdminReports?.();
  stopAdminReports = null;
  stopAdminConversations?.();
  stopAdminConversations = null;
  ownerConversationStops.forEach((stop) => stop());
  ownerConversationStops.clear();
  ownedReportIds.clear();
  conversations.clear();
  moderationReports = [];
  currentUserIsAdmin = false;
  closeChat();
  renderConversations();
  updateAccountMenuState();
  adminPanel.hidden = true;
}

function handleAuthState(user) {
  const signedInUser = user && !user.isAnonymous ? user : null;
  const changedUser = currentUser?.uid !== signedInUser?.uid;
  const becameVerified = signedInUser?.emailVerified && !currentUser?.emailVerified;
  if (changedUser) resetUserSubscriptions();
  currentUser = signedInUser;

  const showAccountForm = !currentUser;
  accountForm.hidden = !showAccountForm;
  accountCurrent.hidden = showAccountForm;
  accountMessage.textContent = '';

  if (!currentUser) {
    accountMessage.textContent = 'Inicia sesión o crea una cuenta individual para publicar y conversar.';
    renderConversations();
    renderReports([...reports.values()]);
    updateAccountMenuState();
    return;
  }

  const isSamuelAdmin = currentUser.email?.toLowerCase() === ADMIN_EMAIL.toLowerCase();
  const verificationStatus = currentUser.emailVerified
    ? 'Correo verificado: ya puedes publicar y chatear.'
    : 'Revisa tu correo y confirma la dirección para publicar o chatear.';
  accountSummary.textContent = `${currentUser.email ?? 'Cuenta'} · ${verificationStatus}`;
  document.querySelector('#refresh-account-button').hidden = currentUser.emailVerified;

  if (changedUser || !stopAdminStatus) {
    stopAdminStatus = watchAdminStatus(currentUser.uid, (isAdmin) => {
      currentUserIsAdmin = (isAdmin || isSamuelAdmin) && currentUser.emailVerified;
      accountSummary.textContent = `${currentUser.email} · ${verificationStatus}${currentUserIsAdmin ? ' · Administrador' : ''}`;
      updateAccountMenuState();
      if (currentUserIsAdmin) startAdminSubscriptions();
      else stopAdminSubscriptions();
    }, (error) => {
      console.error('[petcode] Could not check administrator access:', error);
      if (isSamuelAdmin && currentUser.emailVerified) {
        currentUserIsAdmin = true;
        updateAccountMenuState();
        startAdminSubscriptions();
      } else {
        accountMessage.textContent = 'No pudimos comprobar los permisos de esta cuenta.';
      }
    });
  }

  if (currentUser.emailVerified && (changedUser || becameVerified)) startUserSubscriptions(currentUser);
  renderReports([...reports.values()]);
  updateAccountMenuState();
}

function startUserSubscriptions(user) {
  stopOwnedReports?.();
  stopMyConversations?.();
  stopOwnedReports = watchOwnedReportIds(user.uid, (reportIds) => {
    const nextIds = new Set(reportIds);
    ownedReportIds.clear();
    nextIds.forEach((id) => ownedReportIds.add(id));

    ownerConversationStops.forEach((stop, reportId) => {
      if (!nextIds.has(reportId)) {
        stop();
        ownerConversationStops.delete(reportId);
      }
    });

    nextIds.forEach((reportId) => {
      if (!ownerConversationStops.has(reportId)) {
        const stop = watchReportConversations(reportId, mergeConversations, showConversationError);
        ownerConversationStops.set(reportId, stop);
      }
    });
    renderReports([...reports.values()]);
    updateAccountMenuState();
  }, showConversationError);

  stopMyConversations = watchMyConversations(user.uid, mergeConversations, showConversationError);
  conversationsPanel.hidden = false;
  renderReports([...reports.values()]);
  updateAccountMenuState();
}

function startAdminSubscriptions() {
  if (stopAdminReports || stopAdminConversations) return;
  if (adminOperatorEmail) {
    adminOperatorEmail.textContent = currentUser?.email || ADMIN_EMAIL;
  }
  stopAdminReports = watchModerationReports((items) => {
    moderationReports = items;
    renderAdminReports();
  }, showConversationError);

  stopAdminConversations = watchAllConversations((items) => {
    adminConversationList.replaceChildren();

    // Calculate aggregated metrics for PetCode 5% platform fee and payouts
    let totalRewards = 0;
    let totalFees = 0;
    let totalPayouts = 0;

    items.forEach((conv) => {
      const report = reports.get(conv.reportId);
      const amount = conv.rewardAmount || report?.rewardAmount;
      if (amount && Number(amount) > 0) {
        const split = calculateRewardSplit(amount);
        totalRewards += split.total;
        totalFees += split.platformFee;
        totalPayouts += split.finderPayout;
      }
    });

    if (adminTotalFees) adminTotalFees.textContent = `$${formatCurrency(totalFees)}`;
    if (adminTotalPayouts) adminTotalPayouts.textContent = `$${formatCurrency(totalPayouts)}`;
    if (adminTotalRewards) adminTotalRewards.textContent = `$${formatCurrency(totalRewards)}`;

    if (items.length === 0) {
      adminConversationList.textContent = 'Aún no hay conversaciones.';
      return;
    }
    items.forEach((conversation) => {
      const item = document.createElement('article');
      item.className = 'admin-item';
      const detail = document.createElement('p');
      const report = reports.get(conversation.reportId) ?? {};
      const amount = conversation.rewardAmount || report.rewardAmount;
      let rewardText = '';
      if (amount && Number(amount) > 0) {
        const split = calculateRewardSplit(amount);
        const status = conversation.paymentStatus || 'pending';
        rewardText = ` · 🎁 Recompensa: $${formatCurrency(split.total)} (5% PetCode: $${formatCurrency(split.platformFee)} | 95% rescatista: $${formatCurrency(split.finderPayout)}) [${status}]`;
      }
      detail.textContent = `${reportTitle(report)} · ${formatTime(conversation.lastMessageAt)}${rewardText}`;
      item.append(detail, makeButton('Revisar chat y pagos', 'secondary-button', () => openConversation(conversation)));
      adminConversationList.append(item);
    });
  }, showConversationError);
  adminPanel.hidden = false;
}

function stopAdminSubscriptions() {
  stopAdminReports?.();
  stopAdminReports = null;
  stopAdminConversations?.();
  stopAdminConversations = null;
  adminPanel.hidden = true;
}

function mergeConversations(items) {
  items.forEach((conversation) => conversations.set(conversation.id, conversation));
  renderConversations();
  updateAccountMenuState();
}

function renderConversations() {
  conversationList.replaceChildren();
  const visibleItems = getUserVisibleConversations();

  if (!currentUser?.emailVerified || visibleItems.length === 0) {
    conversationList.textContent = currentUser?.emailVerified
      ? 'Aún no tienes conversaciones. Puedes iniciar una desde un aviso.'
      : '';
    conversationsPanel.hidden = !currentUser?.emailVerified;
    updateAccountMenuState();
    return;
  }

  conversationsPanel.hidden = false;
  const items = visibleItems
    .sort((left, right) => (getReportTime({ createdAt: right.lastMessageAt })?.getTime() ?? 0)
      - (getReportTime({ createdAt: left.lastMessageAt })?.getTime() ?? 0));
  items.forEach((conversation) => {
    const report = reports.get(conversation.reportId);
    const item = document.createElement('article');
    item.className = 'conversation-item';
    const detail = document.createElement('p');
    detail.textContent = report ? reportTitle(report) : 'Conversación de aviso';
    const meta = document.createElement('span');
    const amount = conversation.rewardAmount || report?.rewardAmount;
    let rewardInfo = '';
    if (amount && Number(amount) > 0) {
      rewardInfo = ` · 🎁 Recompensa: $${formatCurrency(amount)}`;
    }
    meta.textContent = `Último movimiento: ${formatTime(conversation.lastMessageAt)}${rewardInfo}`;
    item.append(detail, meta, makeButton('Abrir conversación', 'secondary-button', () => openConversation(conversation)));
    conversationList.append(item);
  });
  updateAccountMenuState();
}

function renderAdminReports() {
  if (!currentUserIsAdmin || !adminReportList) return;
  const items = moderationReports;
  adminReportList.replaceChildren();
  if (items.length === 0) {
    adminReportList.textContent = 'Aún no hay avisos.';
    return;
  }
  items.forEach((report) => {
    const item = document.createElement('article');
    item.className = 'admin-item';
    const detail = document.createElement('p');
    detail.textContent = `${reportTitle(report)} · ${report.status === 'hidden' ? 'Oculto' : 'Visible'}`;
    item.append(detail, makeButton(
      report.status === 'hidden' ? 'Volver a mostrar' : 'Ocultar aviso',
      'secondary-button',
      async () => {
        try {
          await setReportVisibility(report.id, report.status === 'hidden' ? 'open' : 'hidden');
        } catch (error) {
          console.error('[petcode] Could not moderate report:', error);
          accountMessage.textContent = 'No se pudo actualizar el aviso. Comprueba los permisos.';
        }
      },
    ));
    adminReportList.append(item);
  });
}

function showConversationError(error) {
  console.error('[petcode] Could not load or update conversations:', error);
  accountMessage.textContent = error?.code === 'permission-denied'
    ? 'Firebase rechazó el acceso a esta conversación.'
    : 'No pudimos actualizar las conversaciones. Comprueba tu conexión.';
}

function renderMessages(messages) {
  chatMessages.replaceChildren();
  if (messages.length === 0) {
    chatMessages.textContent = 'Inicia la conversación con un mensaje respetuoso. No incluyas información personal.';
    return;
  }

  messages.forEach((message) => {
    const item = document.createElement('article');
    item.className = `chat-message${message.senderUid === currentUser?.uid ? ' own-message' : ''}`;
    const sender = document.createElement('strong');
    sender.textContent = message.senderUid === currentUser?.uid ? 'Tú' : 'Otra persona';
    const body = document.createElement('p');
    body.textContent = message.text;
    const time = document.createElement('time');
    time.textContent = formatTime(message.createdAt);
    item.append(sender, body, time);
    if (currentUserIsAdmin) {
      item.append(makeButton('Eliminar mensaje', 'text-button danger-button', async () => {
        if (!window.confirm('¿Eliminar este mensaje por incumplir las normas de privacidad?')) return;
        try {
          await deleteMessage(activeConversationId, message.id);
        } catch (error) {
          console.error('[petcode] Could not remove moderated message:', error);
          messageError.textContent = 'No se pudo eliminar el mensaje.';
          messageError.hidden = false;
        }
      }));
    }
    chatMessages.append(item);
  });
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function renderChatReward(conversation, report) {
  if (!chatRewardContainer) return;
  const rewardAmount = conversation?.rewardAmount || report?.rewardAmount;
  if (!rewardAmount || Number(rewardAmount) <= 0) {
    chatRewardContainer.hidden = true;
    return;
  }

  chatRewardContainer.hidden = false;
  const split = calculateRewardSplit(rewardAmount);
  if (chatRewardTotalText) chatRewardTotalText.textContent = `$${formatCurrency(split.total)}`;
  if (chatRewardBreakdownText) {
    chatRewardBreakdownText.textContent = `🐾 95% para rescatista: $${formatCurrency(split.finderPayout)} · 🛡️ 5% comisión PetCode: $${formatCurrency(split.platformFee)}`;
  }

  const status = conversation.paymentStatus || 'pending';
  if (chatPaymentStatusBadge) {
    chatPaymentStatusBadge.className = `chat-status-badge status-${status}`;
    if (status === 'verified') {
      chatPaymentStatusBadge.textContent = '✓ Pago Verificado por Admin (5% Recaudado)';
    } else if (status === 'paid') {
      chatPaymentStatusBadge.textContent = '✓ Pago Registrado (Pendiente Verificación)';
    } else {
      chatPaymentStatusBadge.textContent = '⏳ Recompensa Pendiente';
    }
  }

  if (chatRewardActions) {
    chatRewardActions.replaceChildren();

    if (status !== 'verified') {
      if (status !== 'paid') {
        const payButton = makeButton('Registrar Pago de Recompensa', 'primary-button', async () => {
          const confirmMsg = `¿Confirmas el pago de la recompensa de $${formatCurrency(split.total)}?\n- Rescatista: $${formatCurrency(split.finderPayout)} (95%)\n- Comisión PetCode: $${formatCurrency(split.platformFee)} (5%)`;
          if (!window.confirm(confirmMsg)) return;
          try {
            await updateConversationPayment(conversation.id, {
              paymentStatus: 'paid',
              rewardAmount: split.total,
              paymentMethod: 'acuerdo_mutuo',
              paymentNote: 'Pago de recompensa pactado',
            });
            conversation.paymentStatus = 'paid';
            renderChatReward(conversation, report);
            await sendMessage(conversation.id, `[Pago registrado]: Se acordo la recompensa de $${formatCurrency(split.total)}. Rescatista: $${formatCurrency(split.finderPayout)} (95%), Comision PetCode: $${formatCurrency(split.platformFee)} (5%).`);
          } catch (err) {
            console.error('[petcode] Could not register payment:', err);
            messageError.textContent = 'No se pudo registrar el pago. Comprueba los permisos.';
            messageError.hidden = false;
          }
        });
        chatRewardActions.append(payButton);
      }

      // Admin verification button (Samuel or Admin)
      if (currentUserIsAdmin) {
        const adminVerifyButton = makeButton('Aprobar & Verificar 5% PetCode (Admin)', 'secondary-button', async () => {
          try {
            await updateConversationPayment(conversation.id, {
              paymentStatus: 'verified',
              rewardAmount: split.total,
              paymentMethod: 'verificado_admin',
              paymentNote: 'Comision del 5% verificada por administracion',
            });
            conversation.paymentStatus = 'verified';
            renderChatReward(conversation, report);
            await sendMessage(conversation.id, `[Admin Verificado]: Pago de recompensa y comision del 5% verificados satisfactoriamente.`);
          } catch (err) {
            console.error('[petcode] Could not verify payment as admin:', err);
            messageError.textContent = 'No se pudo verificar el pago.';
            messageError.hidden = false;
          }
        });
        chatRewardActions.append(adminVerifyButton);
      }
    }
  }
}

function openConversation(conversation) {
  if (!currentUser?.emailVerified) {
    accountMessage.textContent = 'Verifica tu correo para usar el chat.';
    return;
  }

  activeConversationId = conversation.id;
  const report = reports.get(conversation.reportId);
  chatContext.textContent = report ? reportTitle(report) : 'Aviso moderado';
  chatPanel.hidden = false;
  messageError.hidden = true;

  renderChatReward(conversation, report);

  stopMessages?.();
  stopMessages = watchMessages(conversation.id, renderMessages, (error) => {
    console.error('[petcode] Could not load chat messages:', error);
    chatMessages.textContent = 'No pudimos cargar los mensajes. Comprueba tu acceso o conexión.';
  });
  chatPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closeChat() {
  stopMessages?.();
  stopMessages = null;
  activeConversationId = null;
  chatPanel.hidden = true;
  chatMessages.replaceChildren();
  if (chatRewardContainer) chatRewardContainer.hidden = true;
}

async function openConversationForReport(reportId, rewardAmount = null) {
  try {
    const conversationId = await startConversation(reportId, rewardAmount ? { rewardAmount } : null);
    const conversation = conversations.get(conversationId) ?? {
      id: conversationId,
      reportId,
      createdBy: currentUser.uid,
      lastMessageAt: new Date(),
      ...(rewardAmount && Number(rewardAmount) > 0 ? { rewardAmount: Number(rewardAmount), paymentStatus: 'pending' } : {}),
    };
    conversations.set(conversationId, conversation);
    renderConversations();
    openConversation(conversation);
  } catch (error) {
    console.error('[petcode] Could not start conversation:', error);
    accountMessage.textContent = error?.code === 'permission-denied'
      ? 'No se pudo iniciar el chat. El aviso podría ser tuyo o estar oculto.'
      : 'No pudimos iniciar la conversación. Inténtalo de nuevo.';
  }
}

// Account Menu Listeners
accountMenuButton?.addEventListener('click', () => {
  const isHidden = accountMenuModal?.hidden !== false;
  if (isHidden) openAccountMenu();
  else closeAccountMenu();
});

closeAccountMenuButton?.addEventListener('click', closeAccountMenu);
accountMenuBackdrop?.addEventListener('click', closeAccountMenu);

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && accountMenuModal && !accountMenuModal.hidden) {
    closeAccountMenu();
  }
});

// Menu Quick Links smooth jump and auto-close
const menuActionLinks = [
  '#menu-conversations-link',
  '#menu-reports-link',
  '#menu-new-report-link',
  '#menu-admin-link',
  '#menu-go-signin-button',
];
menuActionLinks.forEach((selector) => {
  const link = document.querySelector(selector);
  link?.addEventListener('click', () => {
    closeAccountMenu();
  });
});

menuSignOutButton?.addEventListener('click', async () => {
  closeAccountMenu();
  try {
    await signOutAccount();
    accountMessage.textContent = 'Sesión cerrada.';
  } catch (error) {
    console.error('[petcode] Sign-out failed:', error);
    accountMessage.textContent = 'No pudimos cerrar la sesión. Inténtalo de nuevo.';
  }
});

menuVerifyButton?.addEventListener('click', async () => {
  try {
    const user = await refreshCurrentUser();
    if (user.emailVerified) {
      accountMessage.textContent = 'Correo verificado. Ya puedes publicar y chatear.';
      handleAuthState(user);
    } else {
      accountMessage.textContent = 'Aún no aparece la verificación. Abre el enlace del correo y vuelve a intentar.';
    }
  } catch (error) {
    console.error('[petcode] Could not refresh account:', error);
    accountMessage.textContent = 'No pudimos comprobar el estado de la cuenta.';
  }
});

accountForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  accountMessage.textContent = '';
  if (!accountForm.reportValidity()) return;

  try {
    await signIn(accountEmail.value, accountPassword.value);
    accountPassword.value = '';
    accountMessage.textContent = 'Sesión iniciada.';
  } catch (error) {
    console.error('[petcode] Sign-in failed:', error);
    accountMessage.textContent = accountErrorText(error);
  }
});

document.querySelector('#register-button').addEventListener('click', async () => {
  accountMessage.textContent = '';
  if (!accountForm.reportValidity()) return;
  if (accountPassword.value.length < 8) {
    accountMessage.textContent = 'Usa una contraseña de al menos 8 caracteres.';
    accountPassword.focus();
    return;
  }

  try {
    await registerAccount(accountEmail.value, accountPassword.value);
    accountPassword.value = '';
    accountMessage.textContent = 'Cuenta creada. Revisa tu correo y confirma la dirección antes de publicar o chatear.';
  } catch (error) {
    console.error('[petcode] Account registration failed:', error);
    accountMessage.textContent = accountErrorText(error);
  }
});

document.querySelector('#reset-password-button').addEventListener('click', async () => {
  accountMessage.textContent = '';
  if (!accountEmail.value.trim() || !accountEmail.checkValidity()) {
    accountEmail.reportValidity();
    accountEmail.focus();
    return;
  }

  try {
    await resetPassword(accountEmail.value);
    accountMessage.textContent = 'Si existe una cuenta con ese correo, recibirás un enlace para restablecer la contraseña.';
  } catch (error) {
    console.error('[petcode] Password reset failed:', error);
    accountMessage.textContent = error?.code === 'auth/invalid-email'
      ? 'Escribe un correo electrónico válido.'
      : accountErrorText(error);
  }
});

document.querySelector('#sign-out-button').addEventListener('click', async () => {
  try {
    await signOutAccount();
    accountMessage.textContent = 'Sesión cerrada.';
  } catch (error) {
    console.error('[petcode] Sign-out failed:', error);
    accountMessage.textContent = 'No pudimos cerrar la sesión. Inténtalo de nuevo.';
  }
});

document.querySelector('#refresh-account-button').addEventListener('click', async () => {
  try {
    const user = await refreshCurrentUser();
    if (user.emailVerified) {
      accountMessage.textContent = 'Correo verificado. Ya puedes publicar y chatear.';
      handleAuthState(user);
    } else {
      accountMessage.textContent = 'Aún no aparece la verificación. Abre el enlace del correo y vuelve a intentar.';
    }
  } catch (error) {
    console.error('[petcode] Could not refresh account:', error);
    accountMessage.textContent = 'No pudimos comprobar el estado de la cuenta.';
  }
});

form.addEventListener('change', () => {
  formError.hidden = true;
  formSuccess.hidden = true;
});

rewardAmountInput?.addEventListener('input', updateRewardBreakdown);

form.addEventListener('change', (event) => {
  if (event.target.name !== 'reportType') return;
  const isFoundReport = form.reportType.value === 'found';
  const isLostReport = form.reportType.value === 'lost';

  handoffField.hidden = !isFoundReport;
  if (!isFoundReport) handoffOption.value = '';

  if (rewardFieldContainer) {
    rewardFieldContainer.hidden = !isLostReport;
    if (!isLostReport && rewardAmountInput) {
      rewardAmountInput.value = '';
      if (rewardBreakdownCard) rewardBreakdownCard.hidden = true;
    }
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  formError.hidden = true;
  formSuccess.hidden = true;

  const values = {
    reportType: form.reportType.value,
    species: form.species.value,
    color: form.color.value,
    region: form.region.value,
  };
  const missingField = Object.keys(allowedValues).find(
    (field) => !allowedValues[field].has(values[field]),
  );

  if (missingField) {
    showFormError('Completa todos los campos para publicar el aviso.');
    const target = missingField === 'reportType'
      ? form.querySelector('input[name="reportType"]')
      : form.elements.namedItem(missingField);
    target?.focus();
    return;
  }

  if (!currentUser) {
    showFormError('Inicia sesión con una cuenta para publicar un aviso.');
    document.querySelector('#cuenta').scrollIntoView({ behavior: 'smooth' });
    return;
  }
  if (!currentUser.emailVerified) {
    showFormError('Verifica tu correo antes de publicar.');
    return;
  }

  const petNameVal = petNameInput?.value?.trim();
  const specialConditionsVal = specialConditionsInput?.value?.trim();

  const report = {
    reportType: values.reportType,
    species: values.species,
    color: values.color,
    region: values.region,
    ...(petNameVal ? { petName: petNameVal } : {}),
    ...(specialConditionsVal ? { specialConditions: specialConditionsVal } : {}),
    ...(values.reportType === 'found' && handoffOption.value
      ? { handoffOption: handoffOption.value }
      : {}),
    ...(values.reportType === 'lost' && rewardAmountInput?.value && Number(rewardAmountInput.value) > 0
      ? { rewardAmount: Number(rewardAmountInput.value) }
      : {}),
  };

  submitButton.disabled = true;
  submitButton.classList.add('is-loading');
  submitButton.querySelector('span:first-child').textContent = 'Publicando…';

  try {
    const reportRef = await createReport(report);
    const createdReport = { id: reportRef.id, ...report };
    form.reset();
    if (rewardBreakdownCard) rewardBreakdownCard.hidden = true;
    if (rewardFieldContainer) rewardFieldContainer.hidden = true;
    formSuccess.textContent = '¡Aviso publicado con éxito! Aquí tienes tu Placa Digital y Código QR.';
    formSuccess.hidden = false;

    // Immediately display QR code modal for this pet
    await showQrModalForReport(createdReport);
  } catch (error) {
    console.error('[petcode] Could not publish report:', error);
    if (error?.message?.startsWith('Firebase configuration is missing')) {
      showFormError('Falta configurar Firebase. El aviso no se publicó.');
    } else if (error?.message === 'auth/email-not-verified') {
      showFormError('Verifica tu correo antes de publicar.');
    } else if (error?.code === 'permission-denied') {
      showFormError('Firebase rechazó el aviso. Verifica tu correo y vuelve a intentar.');
    } else {
      showFormError('No pudimos publicar el aviso. Revisa tu conexión e inténtalo de nuevo.');
    }
  } finally {
    submitButton.disabled = false;
    submitButton.classList.remove('is-loading');
    submitButton.querySelector('span:first-child').textContent = 'Publicar aviso';
  }
});

// QR Modal Action Listeners
downloadQrBtn?.addEventListener('click', () => {
  if (!currentQrDataUrl) return;
  const link = document.createElement('a');
  link.download = `placa-qr-petcode-${Date.now()}.png`;
  link.href = currentQrDataUrl;
  link.click();
});

printQrBtn?.addEventListener('click', () => {
  window.print();
});

copyQrLinkBtn?.addEventListener('click', async () => {
  if (!currentQrPetUrl) return;
  try {
    await navigator.clipboard.writeText(currentQrPetUrl);
    if (qrCopyFeedback) {
      qrCopyFeedback.textContent = '✓ ¡Enlace directo copiado al portapapeles!';
      qrCopyFeedback.hidden = false;
    }
  } catch (err) {
    if (qrCopyFeedback) {
      qrCopyFeedback.textContent = `Enlace: ${currentQrPetUrl}`;
      qrCopyFeedback.hidden = false;
    }
  }
});

closeQrModalButton?.addEventListener('click', closeQrModal);
qrModalBackdrop?.addEventListener('click', closeQrModal);
closeScannedModalButton?.addEventListener('click', closeScannedModal);
scannedModalBackdrop?.addEventListener('click', closeScannedModal);

// Admin Button to Clean Legacy Test Notices from Firestore
adminCleanLegacyBtn?.addEventListener('click', async () => {
  if (!currentUserIsAdmin) return;
  if (!window.confirm('¿Confirmas que deseas borrar definitivamente los avisos de prueba antiguos de la base de datos?')) return;
  if (adminCleanStatus) {
    adminCleanStatus.hidden = false;
    adminCleanStatus.textContent = 'Borrando avisos de prueba en Firestore...';
  }
  try {
    for (const testId of LEGACY_TEST_IDS) {
      try {
        await deleteReport(testId);
      } catch (err) {
        console.warn(`[petcode] Notice ${testId} could not be deleted or was already removed:`, err);
      }
    }
    if (adminCleanStatus) {
      adminCleanStatus.textContent = '✓ Avisos antiguos eliminados de Firestore con éxito.';
    }
    renderReports(rawFeedReports);
  } catch (err) {
    console.error('[petcode] Error during legacy cleanup:', err);
    if (adminCleanStatus) {
      adminCleanStatus.textContent = 'No se pudieron eliminar todos los avisos antiguos.';
    }
  }
});

messageForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  messageError.hidden = true;
  const value = messageText.value;
  if (!isSafeChatMessage(value)) {
    messageError.textContent = 'El mensaje no puede estar vacío ni incluir correos, teléfonos, enlaces o más de 1000 caracteres.';
    messageError.hidden = false;
    messageText.focus();
    return;
  }
  if (!activeConversationId) return;

  const button = messageForm.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    await sendMessage(activeConversationId, value);
    messageText.value = '';
  } catch (error) {
    console.error('[petcode] Could not send chat message:', error);
    messageError.textContent = error?.code === 'permission-denied'
      ? 'No tienes permiso para enviar en este chat o el aviso está oculto.'
      : 'No pudimos enviar el mensaje. Inténtalo de nuevo.';
    messageError.hidden = false;
  } finally {
    button.disabled = false;
  }
});

document.querySelector('#close-chat-button').addEventListener('click', closeChat);

initPopayanFilters();
checkScannedPetUrl();

try {
  watchAuth(handleAuthState, (error) => {
    console.error('[petcode] Authentication state failed:', error);
    accountMessage.textContent = 'No pudimos comprobar la sesión con Firebase.';
  });
  watchReports(
    (reportRecords) => {
      renderReports(reportRecords);
      renderConversations();
    },
    showListenerError,
  );
} catch (error) {
  showListenerError(error);
}
