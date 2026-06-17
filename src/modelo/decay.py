"""Decaimiento temporal tipo Hawkes para los eventos del grafo (PENDIENTE DE DISENO).

Idea: un evento geopolitico no afecta solo al dia en que ocurre; su influencia
decae en el tiempo. Un kernel de Hawkes pondera la contribucion de eventos pasados
al snapshot actual con un decaimiento exponencial, de modo que un shock reciente
pesa mas que uno antiguo.

Stub: la implementacion se abordara al definir la arquitectura HGNN dinamica.
"""
from __future__ import annotations


def kernel_exponencial(delta_dias, beta: float = 0.5):
    """Peso de un evento ocurrido hace `delta_dias` con decaimiento exp(-beta * dt).

    Placeholder a la espera del diseno definitivo del mecanismo temporal.
    """
    raise NotImplementedError("decay de Hawkes pendiente de diseno")
