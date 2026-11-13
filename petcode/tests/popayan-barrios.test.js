import assert from 'node:assert/strict';
import test from 'node:test';
import {
  POPAYAN_BARRIOS,
  getBarrioLabel,
} from '../src/popayan-barrios.js';

test('popayan barrios list contains essential neighborhoods', () => {
  const ids = POPAYAN_BARRIOS.map((b) => b.id);
  assert.ok(ids.includes('centro_historico'));
  assert.ok(ids.includes('bello_horizonte'));
  assert.ok(ids.includes('la_estancia'));
  assert.ok(ids.includes('pandiguando'));
  assert.ok(ids.includes('alfonso_lopez'));
  assert.ok(ids.includes('pomona'));
  assert.ok(ids.includes('lomas_de_granada'));
  assert.ok(ids.includes('maria_occidente'));
});

test('getBarrioLabel returns formatted name with Popayan', () => {
  assert.equal(getBarrioLabel('bello_horizonte'), 'Bello Horizonte (Popayán)');
  assert.equal(getBarrioLabel('centro_historico'), 'Centro Histórico (Popayán)');
  assert.equal(getBarrioLabel('unknown_barrio'), 'unknown_barrio');
});

