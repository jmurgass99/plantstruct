"""Tests memoria completa estanque."""
from industrialjm.memos import TankMemoInput, render_tank_memo


def test_memoria_genera_outputs():
    r = render_tank_memo(TankMemoInput(
        D_m=20, H_l_m=15, H_shell_m=16, t_shell_mm=8,
        Sa_i_g=0.3, Sa_c_g=0.1,
    ))
    assert "Housner" in r.markdown
    assert "Anclajes" in r.markdown
    assert "Pandeo" in r.markdown
    assert "masses" in r.to_dict()


def test_memoria_tank_severo_falla():
    r = render_tank_memo(TankMemoInput(
        D_m=30, H_l_m=20, H_shell_m=21, t_shell_mm=5,
        Sa_i_g=0.6, Sa_c_g=0.2, n_bolts=8,
    ))
    # Acel alta + manto delgado + pocos pernos → no safe
    assert not r.is_safe


# ===========================================================================
# IN-004: Tests memoria paso-a-paso con todas las secciones
# ===========================================================================

def test_memo_contiene_geometria():
    """Markdown contiene seccion de geometria con D, H, t."""
    r = render_tank_memo(TankMemoInput(
        D_m=10, H_l_m=8, H_shell_m=9, t_shell_mm=8,
        Sa_i_g=0.3, Sa_c_g=0.1,
    ))
    assert "Geometria" in r.markdown
    assert "D = 10.0" in r.markdown
    assert "H_l = 8.0" in r.markdown


def test_memo_contiene_periodos_Ti_Tc():
    """Markdown incluye periodos impulsivo y convectivo."""
    r = render_tank_memo(TankMemoInput(
        D_m=10, H_l_m=8, H_shell_m=9, t_shell_mm=8,
        Sa_i_g=0.3, Sa_c_g=0.1,
    ))
    assert "T_i" in r.markdown
    assert "T_c" in r.markdown
    # Periodos deben estar en el dict de masas
    assert "T_i_s" in r.masses
    assert "T_c_s" in r.masses
    assert r.masses["T_i_s"] > 0
    assert r.masses["T_c_s"] > 0


def test_memo_verificacion_espesor():
    """Memo incluye verificacion de espesor por hidrostatica."""
    r = render_tank_memo(TankMemoInput(
        D_m=10, H_l_m=8, H_shell_m=9, t_shell_mm=8,
        Sa_i_g=0.3, Sa_c_g=0.1,
    ))
    assert "espesor" in r.markdown.lower() or "t_design" in r.markdown
    assert "shell_thickness" in r.to_dict()


def test_memo_anchorage_J():
    """Memo incluye J-ratio en los resultados."""
    r = render_tank_memo(TankMemoInput(
        D_m=10, H_l_m=8, H_shell_m=9, t_shell_mm=8,
        Sa_i_g=0.3, Sa_c_g=0.1,
    ))
    assert "J-ratio" in r.markdown
    assert "anchorage_J" in r.to_dict()
    assert r.anchorage_J["J"] > 0


def test_memo_pandeo_diamond():
    """Memo incluye factor Rotter diamond en pandeo."""
    r = render_tank_memo(TankMemoInput(
        D_m=10, H_l_m=8, H_shell_m=9, t_shell_mm=8,
        Sa_i_g=0.3, Sa_c_g=0.1,
    ))
    assert "Rotter" in r.markdown or "alpha_diamond" in r.markdown
    assert "buckling_full" in r.to_dict()
    assert 0 < r.buckling_full["alpha_diamond"] < 1


def test_memo_render_produce_secciones_clave():
    """El render produce output con todas las secciones requeridas."""
    r = render_tank_memo(TankMemoInput(
        D_m=10, H_l_m=8, H_shell_m=9, t_shell_mm=8,
        Sa_i_g=0.3, Sa_c_g=0.1,
    ))
    secciones = ["Geometria", "Housner", "espesor", "Anclajes", "Pandeo", "Resultado"]
    for sec in secciones:
        assert sec.lower() in r.markdown.lower(), f"Seccion '{sec}' faltante"
