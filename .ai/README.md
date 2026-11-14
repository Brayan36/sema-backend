# .ai: contexto del proyecto SEMA

Carpeta con el contexto que necesita una persona o un agente de IA para trabajar en este repositorio. **Leer en este orden:**

| # | Archivo | Para qué sirve |
|---|---|---|
| 1 | [CONTEXT.md](CONTEXT.md) | Punto de entrada: qué es SEMA, alcance, protocolo de trabajo, decisiones, estado y bitácora |
| 2 | [PLAN.md](PLAN.md) | Plan por fases, con checklists y criterios de "listo" |
| 3 | [ARCHITECTURE.md](ARCHITECTURE.md) | Referencia técnica: capas, core, seguridad, convenciones, cómo agregar una feature |

**Reglas de esta carpeta**
- Los nombres de archivo van en inglés. El contenido va en español.
- El código es la fuente de verdad: si un `.md` y el código difieren, gana el código y el `.md` se corrige.
- Al cerrar cada sesión se actualizan la sección de estado y la bitácora de `CONTEXT.md`.
- El código base viene de un proyecto de entrenamiento previo (FastAPI + SQLite) y se adaptó al alcance real de SEMA. Todo lo que aparece como *(por definir)* está abierto y no debe darse por decidido.
- Cómo instalar y ejecutar: [../backend/README.md](../backend/README.md).
