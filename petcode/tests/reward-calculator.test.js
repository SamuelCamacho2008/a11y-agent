import assert from 'node:assert/strict';
import test from 'node:test';
import {
  PLATFORM_FEE_PERCENT,
  calculateRewardSplit,
  formatCurrency,
} from '../src/reward-calculator.js';

test('calculates 5% platform fee and 95% finder payout accurately', () => {
  const result = calculateRewardSplit(100000);
  assert.equal(result.total, 100000);
  assert.equal(result.platformFee, 5000);
  assert.equal(result.finderPayout, 95000);
  assert.equal(result.feePercent, 5);
});

test('handles 50,000 correctly', () => {
  const result = calculateRewardSplit(50000);
  assert.equal(result.total, 50000);
  assert.equal(result.platformFee, 2500);
  assert.equal(result.finderPayout, 47500);
});

test('handles 0 or negative amounts gracefully', () => {
  const zero = calculateRewardSplit(0);
  assert.equal(zero.total, 0);
  assert.equal(zero.platformFee, 0);
  assert.equal(zero.finderPayout, 0);

  const neg = calculateRewardSplit(-500);
  assert.equal(neg.total, 0);
  assert.equal(neg.platformFee, 0);
  assert.equal(neg.finderPayout, 0);
});

test('formats currency properly in Spanish locale', () => {
  const formatted = formatCurrency(100000);
  assert.ok(formatted.includes('100') && (formatted.includes('.') || formatted.includes(',')));
});

