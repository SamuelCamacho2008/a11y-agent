/**
 * Utilities for reward calculation and platform fee breakdown (5%).
 */

export const PLATFORM_FEE_PERCENT = 5;

export function calculateRewardSplit(amount) {
  const numericAmount = Math.max(0, Number(amount) || 0);
  if (numericAmount <= 0) {
    return {
      total: 0,
      platformFee: 0,
      finderPayout: 0,
      feePercent: PLATFORM_FEE_PERCENT,
    };
  }

  // 5% platform commission
  const platformFee = Math.round(numericAmount * (PLATFORM_FEE_PERCENT / 100) * 100) / 100;
  // 95% net for the person who finds/helps the pet
  const finderPayout = Math.round((numericAmount - platformFee) * 100) / 100;

  return {
    total: numericAmount,
    platformFee,
    finderPayout,
    feePercent: PLATFORM_FEE_PERCENT,
  };
}

export function formatCurrency(amount) {
  const num = Number(amount) || 0;
  return new Intl.NumberFormat('es-CO', {
    style: 'decimal',
    maximumFractionDigits: 0,
  }).format(num);
}

