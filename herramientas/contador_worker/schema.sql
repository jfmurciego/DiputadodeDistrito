-- T-294 · contador: única tabla; sin IP, user-agent, referente ni hora.
CREATE TABLE IF NOT EXISTS visitas (
  dia  TEXT    NOT NULL,   -- AAAA-MM-DD (UTC)
  ruta TEXT    NOT NULL,   -- ruta de la lista blanca
  n    INTEGER NOT NULL,
  PRIMARY KEY (dia, ruta)
);
