// C++ / WebAssembly kernel para tensión circunferencial API 650 y frecuencia cuadrada de chapoteo (Housner)
extern "C" {
  double hoopHydrostaticStress(double gamma_kn_m3, double depth_m, double radius_m, double t_mm) {
    return (gamma_kn_m3 * depth_m * radius_m) / t_mm;
  }

  double sloshingFreqSquared(double g_m_s2, double radius_m, double tanh_val) {
    return (1.841 * g_m_s2 / radius_m) * tanh_val;
  }
}
