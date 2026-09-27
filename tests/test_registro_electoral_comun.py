import tempfile
import unittest
from pathlib import Path
import yaml
from herramientas.resolver_eleccion_vigente import resolve, resolve_for_preparation
from herramientas.preparar_fuente_electoral import prepare
from herramientas.adaptador_eleccionesdb import ELECTIONS
ROOT = Path(__file__).resolve().parents[1]

class TestRegistroElectoralComun(unittest.TestCase):
    def setUp(self):
        self.registry=yaml.safe_load((ROOT/"configuracion/registro_electoral.yaml").read_text(encoding="utf-8"))
    def test_registry_follows_canonical_codauto_order(self):
        self.assertEqual(
            list(self.registry["territories"]),
            [
                "andalucia",
                "aragon",
                "principado_de_asturias",
                "illes_balears",
                "canarias",
                "cantabria",
                "castilla_y_leon",
                "castilla_la_mancha",
                "cataluna",
                "comunidad_valenciana",
                "extremadura",
                "galicia",
                "madrid",
                "region_de_murcia",
                "comunidad_foral_de_navarra",
                "pais_vasco",
                "la_rioja",
                "ceuta",
                "melilla",
            ],
        )

    def test_workflow_selector_matches_registry_codauto_order(self):
        names=[row["name"] for row in self.registry["territories"].values()]
        workflow=(ROOT/".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertIn("options: [" + ", ".join(names) + "]", workflow)

    def test_registry_has_exactly_19_identified_elections(self):
        self.assertEqual(self.registry["schema"],"ddd-election-registry/1.0"); self.assertEqual(len(self.registry["territories"]),19)
        for row in self.registry["territories"].values(): self.assertTrue(row["election_id"] and row["election_date"] and row["name"])
    def test_all_registered_territories_can_enter_electoral_preparation(self):
        for registry_id,entry in self.registry["territories"].items():
            with self.subTest(territory=registry_id):
                row=resolve_for_preparation(entry["name"],root_dir=ROOT,edition="2025")
                self.assertTrue(row["territory_id"]); self.assertEqual(row["election_id"],entry["election_id"]); self.assertEqual(row["territorial_edition"],"2025")
    def test_every_registered_election_has_a_technical_route_into_03(self):
        workflow=(ROOT/".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        unresolved=[]
        for registry_id,entry in self.registry["territories"].items():
            row=resolve_for_preparation(entry["name"],root_dir=ROOT,edition="2025")
            mode=row["resolution_mode"]
            election_id=entry["election_id"]
            routed=(
                election_id in ELECTIONS
                or mode in {"governed_override","auto_discovered_declaration","materialized_election_contract"}
                or (election_id=="andalucia_parlamento_2026" and "adapter=siel_andalucia" in workflow)
            )
            if not routed:
                unresolved.append((registry_id,election_id,mode))
        self.assertEqual(unresolved,[])

    def test_identified_election_without_source_reaches_acquisition_and_blocks(self):
        row=resolve_for_preparation("Andalucía",root_dir=ROOT,edition="2025")
        self.assertEqual(row["resolution_mode"],"registered_identity_pending_source")
        with tempfile.TemporaryDirectory() as td:
            result=prepare(territory_id=row["territory_id"],edition="2025",package_out=Path(td)/"electoral",root=ROOT)
        self.assertEqual(result["decision"],"BLOCK"); self.assertIn("Sin paquete reutilizable",result["reason"])
    def test_cantabria_is_identified_but_dead_url_is_not_claimed_as_loaded(self):
        entry=self.registry["territories"]["cantabria"]
        self.assertEqual(entry["election_id"],"cantabria_parlamento_2023")
        self.assertFalse(entry.get("source_verified",False))
        self.assertFalse(entry.get("package_registered",False))
    def test_existing_governed_source_remains_resolvable(self):
        row=resolve("Principado de Asturias",root_dir=ROOT,edition="2025")
        self.assertEqual(row["election_id"],"asturias_jgpa_2023"); self.assertTrue(row["declaration"])
    def test_ceuta_melilla_keep_their_own_identified_assembly_elections(self):
        self.assertEqual(self.registry["territories"]["ceuta"]["election_id"],"ceuta_asamblea_local_2023")
        self.assertEqual(self.registry["territories"]["melilla"]["election_id"],"melilla_asamblea_local_2023")
    def test_unregistered_territory_cannot_enter_preparation(self):
        with self.assertRaises(SystemExit): resolve_for_preparation("Territorio inexistente",root_dir=ROOT,edition="2025")
if __name__=="__main__": unittest.main()
