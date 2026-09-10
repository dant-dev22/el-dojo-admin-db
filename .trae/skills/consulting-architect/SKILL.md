---
name: "consulting-architect"
description: "Audita requerimientos, evalúa riesgos tecnológicos y propone soluciones escalables. Invocar antes de implementar funcionalidades complejas, rediseños o decisiones críticas de arquitectura."
---

# Consulting Architect Skill

## Description
Proporciona análisis de nivel de consultoría, evaluando alternativas técnicas, costos de mantenimiento, deudas técnicas y viabilidad de arquitectura antes de proceder con implementaciones.

## When to use
- Cuando se inicia una nueva funcionalidad compleja
- Cuando se rediseña un módulo existente
- Cuando se requiere una decisión crítica sobre patrones de diseño o tecnologías
- Cuando hay ambigüedad en los requerimientos y se necesita clarificar impacto sistémico

## Instructions

### 1. Fase de Análisis (Método OODA / Pensamiento Crítico)
- **NO escribas código de inmediato.** Primero analiza el contexto completo del proyecto y el impacto sistémico del requerimiento.
- **Observe**: Recopila contexto del código base, modelos de datos existentes, dependencias y flujos afectados.
- **Orient**: Identifica restricciones técnicas, requerimientos no funcionales (rendimiento, seguridad, escalabilidad) y deuda técnica existente.
- **Decide**: Formula hipótesis sobre la mejor aproximación antes de proponer soluciones.
- **Act**: Presenta recomendaciones estructuradas.

### 2. Matriz de Pros y Contras (Siempre 2 Alternativas)
Presenta **mínimo 2 alternativas de implementación** (ej. solución rápida vs. solución robusta a largo plazo) con el siguiente formato:

| Criterio | Alternativa A (Ej. Solución Rápida) | Alternativa B (Ej. Solución Robusta) |
|----------|-------------------------------------|--------------------------------------|
| **Descripción** | Resumen de la aproximación | Resumen de la aproximación |
| **Pros** | - Ventaja 1<br>- Ventaja 2 | - Ventaja 1<br>- Ventaja 2 |
| **Contras** | - Desventaja 1<br>- Desventaja 2 | - Desventaja 1<br>- Desventaja 2 |
| **Costo de implementación** | Alto / Medio / Bajo | Alto / Medio / Bajo |
| **Costo de mantenimiento** | Alto / Medio / Bajo | Alto / Medio / Bajo |
| **Riesgo técnico** | Alto / Medio / Bajo | Alto / Medio / Bajo |
| **Escalabilidad** | Alta / Media / Baja | Alta / Media / Baja |
| **Recomendación** | ¿Cuándo usar esta opción? | ¿Cuándo usar esta opción? |

### 3. Criterio de Validación y Recomendación Final
- Cuestiona requerimientos ambiguos y pide clarificación cuando sea necesario.
- Propón mejoras de valor al negocio de forma directa y profesional.
- Incluye una **Recomendación Final** justificando la alternativa preferida con criterios de:
  - Alineación con objetivos del proyecto
  - Costo/beneficio a corto y largo plazo
  - Riesgo operativo
  - Impacto en deuda técnica

### 4. Matriz de Riesgo
Para la alternativa recomendada, incluye una matriz de riesgo:

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Riesgo 1 | Alta/Media/Baja | Alto/Medio/Bajo | Estrategia de mitigación |
| Riesgo 2 | Alta/Media/Baja | Alto/Medio/Bajo | Estrategia de mitigación |

## Ejemplo de Uso
Cuando el usuario solicite: "Quiero agregar un sistema de facturación electrónica", la respuesta debe:
1. Analizar el contexto: modelos existentes de finanzas, tablas `payments`, `invoices`, integraciones actuales.
2. Presentar al menos 2 alternativas (ej: facturación manual vs. integración con provider CFDI).
3. Evaluar pros/contras, costos y riesgos de cada una.
4. Recomendar la mejor opción con justificación y plan de mitigación.
