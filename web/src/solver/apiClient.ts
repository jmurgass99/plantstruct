export async function fetchPlantstructHealthApi(apiBaseUrl: string): Promise<boolean> {
  try {
    const res = await fetch(`${apiBaseUrl}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
