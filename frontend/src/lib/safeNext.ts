/** Only allow post-login redirects to paths inside this app (prevents open redirects). */
export function safeNext(value: string | null): string | null {
  return value && value.startsWith('/') && !value.startsWith('//') ? value : null
}
