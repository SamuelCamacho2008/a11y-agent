const emailPattern = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i;
const phonePattern = /(?:\+?\d[\s().-]*){7,}/;
const urlPattern = /\b(?:https?:\/\/|www\.)/i;

export function isSafeChatMessage(value) {
  if (typeof value !== 'string') return false;
  const text = value.trim();
  return text.length > 0
    && text.length <= 1000
    && !emailPattern.test(text)
    && !phonePattern.test(text)
    && !urlPattern.test(text);
}
