# 🐾 PetCode — Red Comunitaria de Mascotas Perdidas y Encontradas
### Popayán, Cauca, Colombia

PetCode es una plataforma web colaborativa y segura diseñada para ayudar a las mascotas perdidas de **Popayán, Cauca** a regresar a sus hogares. Protege la privacidad de los usuarios evitando la difusión pública de números de teléfono personales, direcciones o WhatsApp, coordinando rescates mediante chats privados cifrados y placas de identificación con Código QR.

---

## 🌐 Enlaces Públicos

* **🚀 Aplicación en Vivo (GitHub Pages):** **[https://samuelcamacho2008.github.io/a11y-agent/](https://samuelcamacho2008.github.io/a11y-agent/)**
* **Acceso alternativo directo:** [https://samuelcamacho2008.github.io/a11y-agent/petcode/](https://samuelcamacho2008.github.io/a11y-agent/petcode/)

---

## ✨ Características Principales

1. **🏷️ Placa de Identificación Digital con Código QR:**
   - Generación instantánea de placa y código QR al registrar la mascota.
   - Opciones para descargar en PNG o imprimir directamente para el collar.
   - Enlace directo codificado en el QR (`?pet=ID`) para que cualquier persona que encuentre al perro o gato pueda escanearlo con la cámara de su celular.

2. **🩺 Alerta de Cuidados Médicos y Problemas de Salud:**
   - Sección especial para registrar condiciones médicas (*alergias, tratamientos, sorderas, medicamentos obligatorios o si es asustadizo*).
   - Al escanear el QR, quien encuentra la mascota ve de inmediato sus cuidados para atenderla adecuadamente.

3. **💬 Chats Privados y Confidenciales:**
   - Quien escanea el QR o encuentra la mascota puede abrir un chat privado directo con el dueño.
   - Privacidad estricta: las conversaciones solo las ven sus participantes y la administración.

4. **📍 Cobertura Completa por Barrios de Popayán, Cauca:**
   - Comuna 1 (Centro Histórico, Caldas, La Pamba, El Empedrado, Santo Domingo, Los Sauces).
   - Comuna 2 (Bello Horizonte, Ciudad Jardín, La Estancia, Prados del Norte, Morinda, Yanaconas, etc.).
   - Comuna 3 (Bolívar, Campamento, Pandiguando, Valencia, El Recuerdo).
   - Comuna 4 (La Esmeralda, María Occidente, Las Américas, Cadillal).
   - Comuna 5 (Alfonso López, Tomás Cipriano, El Refugio, Los Naranjos).
   - Comuna 6 (Lomas de Granada, El Retiro, Santa Clara, La Paz).
   - Comuna 7 (Pomona, Sotará, Pajonal).
   - Corregimientos y Veredas (Julumito, Puelenje, La Rejoya, Río Blanco, Palacé, etc.).
   - Filtro interactivo en el muro de avisos por barrio y especie.

5. **💰 Modelo de Recompensas Justo y Transparente:**
   - **95%** del monto total es para quien encuentra y cuida la mascota.
   - **5%** para la plataforma PetCode por verificación y sostenimiento.
   - Calculadora automática integrada en el formulario y seguimiento del estado del pago en el chat.

6. **🛡️ Panel de Administración (`samuelcamachoaguirre4@gmail.com`):**
   - Menú de Información de la Cuenta.
   - Auditoría de pagos y comisiones del 5%.
   - Botón para limpiar y eliminar avisos antiguos de prueba.

---

## 📁 Estructura del Repositorio

* **`petcode/`**: Código fuente de PetCode (Vite, Firebase Auth & Firestore, QR Code, CSS responsive).
* **`docs/`**: Archivos estáticos de producción desplegados en GitHub Pages.
* **`agente-a11y/`**: Proyecto independiente de auditoría de accesibilidad (A11y Agent, Python/Playwright, Axe-core, reportes).
