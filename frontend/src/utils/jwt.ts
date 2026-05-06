/** 仅从 JWT payload 解码 `sub`（用户 id）；签名验证由后端接口完成。 */
export function getJwtSubject(token: string | null): string | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    let b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64.length % 4 ? "=".repeat(4 - (b64.length % 4)) : "";
    b64 += pad;
    const json = JSON.parse(atob(b64)) as { sub?: string };
    return typeof json.sub === "string" ? json.sub : null;
  } catch {
    return null;
  }
}
