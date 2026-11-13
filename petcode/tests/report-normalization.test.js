import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeReport } from '../src/firebase.js';

test('normalizeReport accepts valid report with Popayan barrio, petName, specialConditions, and reward', () => {
  const input = {
    reportType: 'lost',
    species: 'dog',
    color: 'brown',
    region: 'centro_historico',
    petName: 'Rocky',
    specialConditions: 'Necesita medicamento diario para alergias, es asustadizo',
    rewardAmount: 60000,
  };

  const result = normalizeReport(input);

  assert.equal(result.reportType, 'lost');
  assert.equal(result.species, 'dog');
  assert.equal(result.color, 'brown');
  assert.equal(result.region, 'centro_historico');
  assert.equal(result.petName, 'Rocky');
  assert.equal(result.specialConditions, 'Necesita medicamento diario para alergias, es asustadizo');
  assert.equal(result.rewardAmount, 60000);
  assert.equal(result.platformFeePercent, 5);
});

test('normalizeReport accepts found pet with Popayan barrio and optional handoffOption', () => {
  const input = {
    reportType: 'found',
    species: 'cat',
    color: 'black',
    region: 'ciudad_jardin',
    handoffOption: 'meetup',
    petName: '',
    specialConditions: 'Tiene una patita lastimada',
  };

  const result = normalizeReport(input);

  assert.equal(result.reportType, 'found');
  assert.equal(result.species, 'cat');
  assert.equal(result.region, 'ciudad_jardin');
  assert.equal(result.handoffOption, 'meetup');
  assert.equal(result.specialConditions, 'Tiene una patita lastimada');
  assert.equal(result.petName, undefined);
  assert.equal(result.rewardAmount, undefined);
});

test('normalizeReport rejects invalid region or missing required fields', () => {
  assert.throws(() => {
    normalizeReport({
      reportType: 'lost',
      species: 'dog',
      color: 'black',
      // missing region
    });
  }, /A report must contain/);

  assert.throws(() => {
    normalizeReport({
      reportType: 'lost',
      species: 'dog',
      color: 'black',
      region: '', // empty region
    });
  }, /Invalid region/);
});

