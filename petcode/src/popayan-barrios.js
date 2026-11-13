/**
 * Barrios y sectores de Popayán, Cauca, Colombia para PetCode.
 */

export const POPAYAN_BARRIOS = [
  // Comuna 1: Centro Histórico y alrededores
  { id: 'centro_historico', name: 'Centro Histórico', comuna: 'Comuna 1 (Centro)' },
  { id: 'la_pamba', name: 'La Pamba', comuna: 'Comuna 1 (Centro)' },
  { id: 'caldas', name: 'Caldas', comuna: 'Comuna 1 (Centro)' },
  { id: 'el_empedrado', name: 'El Empedrado', comuna: 'Comuna 1 (Centro)' },
  { id: 'santo_domingo', name: 'Santo Domingo', comuna: 'Comuna 1 (Centro)' },
  { id: 'los_sauces', name: 'Los Sauces', comuna: 'Comuna 1 (Centro)' },

  // Comuna 2: Norte
  { id: 'bello_horizonte', name: 'Bello Horizonte', comuna: 'Comuna 2 (Norte)' },
  { id: 'ciudad_jardin', name: 'Ciudad Jardín', comuna: 'Comuna 2 (Norte)' },
  { id: 'la_estancia', name: 'La Estancia', comuna: 'Comuna 2 (Norte)' },
  { id: 'prados_del_norte', name: 'Prados del Norte', comuna: 'Comuna 2 (Norte)' },
  { id: 'morinda', name: 'Morinda', comuna: 'Comuna 2 (Norte)' },
  { id: 'yanaconas', name: 'Yanaconas', comuna: 'Comuna 2 (Norte)' },
  { id: 'machangara', name: 'Machángara', comuna: 'Comuna 2 (Norte)' },
  { id: 'los_hoyos', name: 'Los Hoyos', comuna: 'Comuna 2 (Norte)' },
  { id: 'pisoje', name: 'Pisojé', comuna: 'Comuna 2 (Norte)' },

  // Comuna 3: Nororiente
  { id: 'bolivar', name: 'Bolívar / Parque Rada', comuna: 'Comuna 3 (Nororiente)' },
  { id: 'campamento', name: 'Campamento', comuna: 'Comuna 3 (Nororiente)' },
  { id: 'pandiguando', name: 'Pandiguando', comuna: 'Comuna 3 (Nororiente)' },
  { id: 'valencia', name: 'Valencia', comuna: 'Comuna 3 (Nororiente)' },
  { id: 'el_recuerdo', name: 'El Recuerdo', comuna: 'Comuna 3 (Nororiente)' },

  // Comuna 4: Occidente
  { id: 'la_esmeralda', name: 'La Esmeralda', comuna: 'Comuna 4 (Occidente)' },
  { id: 'maria_occidente', name: 'María Occidente', comuna: 'Comuna 4 (Occidente)' },
  { id: 'las_americas', name: 'Las Américas', comuna: 'Comuna 4 (Occidente)' },
  { id: 'cadillal', name: 'Cadillal', comuna: 'Comuna 4 (Occidente)' },

  // Comuna 5: Sur
  { id: 'alfonso_lopez', name: 'Alfonso López', comuna: 'Comuna 5 (Sur)' },
  { id: 'tomas_cipriano', name: 'Tomás Cipriano de Mosquera', comuna: 'Comuna 5 (Sur)' },
  { id: 'el_refugio', name: 'El Refugio', comuna: 'Comuna 5 (Sur)' },
  { id: 'los_naranjos', name: 'Los Naranjos', comuna: 'Comuna 5 (Sur)' },
  { id: 'primero_de_mayo', name: 'Primero de Mayo', comuna: 'Comuna 5 (Sur)' },

  // Comuna 6: Suroccidente
  { id: 'lomas_de_granada', name: 'Lomas de Granada', comuna: 'Comuna 6 (Suroccidente)' },
  { id: 'el_retiro', name: 'El Retiro', comuna: 'Comuna 6 (Suroccidente)' },
  { id: 'santa_clara', name: 'Santa Clara', comuna: 'Comuna 6 (Suroccidente)' },
  { id: 'la_paz', name: 'La Paz', comuna: 'Comuna 6 (Suroccidente)' },

  // Comuna 7: Suroriente
  { id: 'pomona', name: 'Pomona', comuna: 'Comuna 7 (Suroriente)' },
  { id: 'sotara', name: 'Sotará', comuna: 'Comuna 7 (Suroriente)' },
  { id: 'pajonal', name: 'Pajonal', comuna: 'Comuna 7 (Suroriente)' },

  // Corregimientos y veredas de Popayán
  { id: 'julumito', name: 'Julumito', comuna: 'Corregimientos / Veredas' },
  { id: 'puelenje', name: 'Puelenje', comuna: 'Corregimientos / Veredas' },
  { id: 'la_rejoya', name: 'La Rejoya', comuna: 'Corregimientos / Veredas' },
  { id: 'rio_blanco', name: 'Río Blanco', comuna: 'Corregimientos / Veredas' },
  { id: 'palace', name: 'Palacé', comuna: 'Corregimientos / Veredas' },
  { id: 'otro_popayan', name: 'Otro barrio de Popayán, Cauca', comuna: 'Otros sectores' },
];

export const BARRIO_MAP = Object.fromEntries(
  POPAYAN_BARRIOS.map((b) => [b.id, `${b.name} (Popayán)`]),
);

// Fallbacks para compatibilidad
BARRIO_MAP.north = 'Norte (Popayán)';
BARRIO_MAP.center = 'Centro (Popayán)';
BARRIO_MAP.south = 'Sur (Popayán)';
BARRIO_MAP.east = 'Oriente (Popayán)';
BARRIO_MAP.west = 'Occidente (Popayán)';
BARRIO_MAP.unspecified = 'Popayán (Sin especificar)';

export function getBarrioLabel(id) {
  return BARRIO_MAP[id] || id || 'Popayán, Cauca';
}

