"""FastAPI app para IndustrialJm — estanques API 650."""
from typing import Any


def create_router() -> Any:
    """Devuelve el APIRouter con los endpoints. Mountable en gateway."""
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field

    from ..tanks import (
        AnchorageInput, ShellBucklingInput, TankGeometry,
        check_anchorage, check_shell_buckling, housner_masses,
        AnchorageJInput, check_anchorage_J,
        ShellBucklingFullInput, check_shell_buckling_full,
    )
    from ..memos import TankMemoInput, render_tank_memo

    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    class TankHousnerPayload(BaseModel):
        D_m: float = Field(..., gt=0)
        H_l_m: float = Field(..., gt=0)
        t_shell_mm: float = Field(6.0, gt=0)
        rho_l_kg_m3: float = Field(1000.0, gt=0)
        Sa_i: float = Field(..., ge=0)
        Sa_c: float = Field(..., ge=0)

    @router.post("/api/tanks/api650/housner")
    def housner(payload: TankHousnerPayload):
        g = TankGeometry(
            D_m=payload.D_m, H_l_m=payload.H_l_m,
            t_shell_mm=payload.t_shell_mm, rho_l_kg_m3=payload.rho_l_kg_m3,
        )
        return housner_masses(g, Sa_i=payload.Sa_i, Sa_c=payload.Sa_c).to_dict()

    class AnchoragePayload(BaseModel):
        D_m: float = Field(..., gt=0)
        W_tank_kN: float = Field(..., gt=0)
        M_overturn_kNm: float = Field(..., ge=0)
        n_bolts: int = Field(12, ge=4)
        bolt_diameter_mm: float = Field(25.4, gt=0)
        bolt_Fy_MPa: float = Field(250.0, gt=0)

    @router.post("/api/tanks/anchorage")
    def anchorage(payload: AnchoragePayload):
        try:
            r = check_anchorage(AnchorageInput(**payload.model_dump()))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return r.to_dict()

    class ShellPayload(BaseModel):
        D_m: float = Field(..., gt=0)
        H_shell_m: float = Field(..., gt=0)
        H_liquid_m: float = Field(..., gt=0)
        t_shell_mm: float = Field(..., gt=0)
        sigma_axial_imposed_MPa: float = Field(0.0, ge=0)

    @router.post("/api/tanks/shell-buckling")
    def shell_buckling(payload: ShellPayload):
        r = check_shell_buckling(ShellBucklingInput(**payload.model_dump()))
        return r.to_dict()

    # ---------------------------------------------------------------
    # POST /api/tanks/api650/full-design  — diseño completo en un solo paso
    # ---------------------------------------------------------------
    class FullDesignPayload(BaseModel):
        D: float = Field(..., gt=0, description="Diametro del estanque [m]")
        H: float = Field(..., gt=0, description="Altura del liquido [m]")
        t_shell: float = Field(..., gt=0, description="Espesor manto [mm]")
        liquid_density: float = Field(1000.0, gt=0,
                                       description="Densidad liquido [kg/m3]")
        Sa: float = Field(..., ge=0,
                          description="Aceleracion espectral impulsiva [g]")
        Ss: float = Field(..., ge=0,
                          description="Aceleracion espectral convectiva [g]")
        n_bolts: int = Field(24, ge=4)
        bolt_diameter_mm: float = Field(25.4, gt=0)

    @router.post("/api/tanks/api650/full-design")
    def full_design(payload: FullDesignPayload):
        """Diseno completo de estanque API 650 §E.

        Retorna masas Housner, periodos, corte basal, momento volcante,
        verificacion de anclaje (J-ratio), pandeo del manto y memoria en
        markdown.
        """
        # Geometria
        g = TankGeometry(
            D_m=payload.D, H_l_m=payload.H,
            t_shell_mm=payload.t_shell,
            rho_l_kg_m3=payload.liquid_density,
        )

        # Masas y periodos
        masses = housner_masses(g, Sa_i=payload.Sa, Sa_c=payload.Ss)
        W_tank = g.W_l_kN * 1.05  # peso estabilizante estimado

        # Anclaje J-ratio
        aj = check_anchorage_J(AnchorageJInput(
            D_m=payload.D, M_rw_kNm=masses.M_overturn_kNm, W_t_kN=W_tank,
            bolt_diameter_mm=payload.bolt_diameter_mm,
        ))

        # Pandeo completo
        bf = check_shell_buckling_full(ShellBucklingFullInput(
            D_m=payload.D, H_shell_m=payload.H * 1.05,
            H_liquid_m=payload.H, t_shell_mm=payload.t_shell,
        ))

        # Corte basal simplificado: V = Sa_i · W_i + Sa_c · W_c
        base_shear = payload.Sa * masses.W_i_kN + payload.Ss * masses.W_c_kN

        # Memoria markdown
        memo = render_tank_memo(TankMemoInput(
            D_m=payload.D, H_l_m=payload.H,
            H_shell_m=payload.H * 1.05,
            t_shell_mm=payload.t_shell,
            Sa_i_g=payload.Sa, Sa_c_g=payload.Ss,
            n_bolts=payload.n_bolts,
            bolt_diameter_mm=payload.bolt_diameter_mm,
            rho_l_kg_m3=payload.liquid_density,
        ))

        return {
            "masses": {
                "m_i": masses.W_i_kN,
                "m_c": masses.W_c_kN,
            },
            "periods": {
                "T_i": masses.T_i_s,
                "T_c": masses.T_c_s,
            },
            "base_shear": base_shear,
            "overturning_moment": masses.M_overturn_kNm,
            "anchorage": {
                "J": aj.J,
                "N_bolts": aj.N_bolts_required,
                "type": aj.anchorage_type,
                "t_base_plate_mm": aj.t_base_plate_mm,
                "L_anchor_mm": aj.L_anchor_mm,
            },
            "buckling": {
                "ratio": bf.DCR_interaction,
                "status": "safe" if bf.is_safe else "unsafe",
                "governing_mode": bf.governing_mode,
                "DCR_axial": bf.DCR_axial,
                "DCR_hoop": bf.DCR_hoop,
                "alpha_diamond": bf.alpha_diamond,
            },
            "memo_md": memo.markdown,
        }

    return router


def create_app() -> Any:
    """App FastAPI standalone."""
    from fastapi import FastAPI

    app = FastAPI(title="IndustrialJm API", version="0.1.0")
    app.include_router(create_router())
    return app
