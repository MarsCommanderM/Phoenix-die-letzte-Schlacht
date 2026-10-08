"""The two central registries, and proof that their validator can fail.

Every check in tools/validation/validate_registries.py gets a negative test
here. A validator is only worth the line in CI if a broken registry actually
makes it fail, and the ways these two files break are quiet ones: an
asymmetric collision matrix and an undeclared tag namespace both read as
perfectly ordinary JSON.
"""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Keep this module runnable on its own, not only via scripts/test.py.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "validation"))

import validate_registries as registries  # noqa: E402
from _repo import load_json  # noqa: E402

CONFIG = ROOT / "project" / "Config"
TAGS = CONFIG / "Gameplay" / "tags.json"
LAYERS = CONFIG / "Physics" / "layers.json"


class RegistryHarness(unittest.TestCase):
    """Runs the validator against a throwaway copy of project/Config."""

    def run_with(self, *, tags=None, layers=None) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "Config"
            shutil.copytree(CONFIG, config)
            if tags is not None:
                (config / "Gameplay" / "tags.json").write_text(
                    json.dumps(tags, indent=4), encoding="utf-8"
                )
            if layers is not None:
                (config / "Physics" / "layers.json").write_text(
                    json.dumps(layers, indent=4), encoding="utf-8"
                )
            errors, _ = registries.validate(config)
            return errors

    def assertFailsWith(self, fragment: str, **kwargs):
        errors = self.run_with(**kwargs)
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected a failure mentioning {fragment!r}; got: {errors}",
        )
        return errors


class CommittedRegistriesTests(RegistryHarness):
    def test_both_registries_exist(self):
        self.assertTrue(TAGS.is_file(), "project/Config/Gameplay/tags.json is missing")
        self.assertTrue(LAYERS.is_file(), "project/Config/Physics/layers.json is missing")

    def test_schemas_exist(self):
        for name in ("tags", "layers", "version", "network_protocol", "save_schema"):
            with self.subTest(schema=name):
                self.assertTrue(
                    (CONFIG / "Schema" / f"{name}.schema.json").is_file(),
                    f"{name}.schema.json is missing; the file it governs would be "
                    "shape-checked by nothing",
                )

    def test_the_committed_registries_validate(self):
        errors, _ = registries.validate(CONFIG)
        self.assertEqual(errors, [], f"committed registries do not validate: {errors}")

    def test_the_harness_itself_reports_a_clean_copy(self):
        """Guards the negative tests below: a harness that always fails proves nothing."""
        self.assertEqual(self.run_with(), [])


class TagRegistryTests(RegistryHarness):
    def setUp(self):
        self.tags = load_json(TAGS)

    def test_an_undeclared_namespace_is_rejected(self):
        """The central rule. A typo must not be able to invent a namespace."""
        bad = copy.deepcopy(self.tags)
        bad["tags"].append(
            {"name": "Charater.Player", "description": "A plausible-looking typo."}
        )
        bad["tags"].sort(key=lambda t: t["name"])
        self.assertFailsWith("is not declared", tags=bad)

    def test_a_duplicate_tag_is_rejected(self):
        bad = copy.deepcopy(self.tags)
        bad["tags"].append(dict(bad["tags"][0]))
        bad["tags"].sort(key=lambda t: t["name"])
        self.assertFailsWith("declared more than once", tags=bad)

    def test_unsorted_tags_are_rejected(self):
        bad = copy.deepcopy(self.tags)
        bad["tags"].reverse()
        self.assertFailsWith("alphabetical order", tags=bad)

    def test_a_dead_namespace_is_rejected(self):
        bad = copy.deepcopy(self.tags)
        bad["namespaces"].append(
            {"name": "Zzz", "description": "Declared but never used by any tag."}
        )
        self.assertFailsWith("no tag uses it", tags=bad)

    def test_a_bare_namespace_as_a_tag_is_rejected(self):
        """Caught by the schema's two-segment pattern, which this confirms."""
        bad = copy.deepcopy(self.tags)
        bad["tags"].insert(
            0, {"name": "Character", "description": "A namespace, not a value."}
        )
        self.assertFailsWith("does not match", tags=bad)

    def test_every_namespace_is_used_and_every_tag_declared(self):
        declared = {n["name"] for n in self.tags["namespaces"]}
        used = {t["name"].split(".", 1)[0] for t in self.tags["tags"]}
        self.assertEqual(declared, used)


class LayerRegistryTests(RegistryHarness):
    def setUp(self):
        self.layers = load_json(LAYERS)

    def test_an_asymmetric_matrix_is_rejected(self):
        """A one-directional collision is a contradiction, not a configuration."""
        bad = copy.deepcopy(self.layers)
        bad["collidesWith"]["Character"].remove("Trigger")
        self.assertFailsWith("asymmetric", layers=bad)

    def test_an_omitted_layer_is_rejected(self):
        bad = copy.deepcopy(self.layers)
        del bad["collidesWith"]["Trigger"]
        self.assertFailsWith("collidesWith does not name", layers=bad)

    def test_an_unknown_partner_is_rejected(self):
        bad = copy.deepcopy(self.layers)
        bad["collidesWith"]["Character"] = sorted(
            bad["collidesWith"]["Character"] + ["Charcter"]
        )
        self.assertFailsWith("undeclared layer", layers=bad)

    def test_a_non_contiguous_index_is_rejected(self):
        bad = copy.deepcopy(self.layers)
        bad["layers"][-1]["index"] = 40
        self.assertFailsWith("contiguous from 0", layers=bad)

    def test_index_zero_must_be_the_engine_default(self):
        """Verified engine behaviour: an unresolved layer name lands on index 0."""
        bad = copy.deepcopy(self.layers)
        for layer in bad["layers"]:
            if layer["name"] == "Default":
                layer["name"] = "Nothing"
        bad["collidesWith"]["Nothing"] = bad["collidesWith"].pop("Default")
        bad["collidesWith"] = dict(sorted(bad["collidesWith"].items()))
        self.assertFailsWith("must be 'Default'", layers=bad)

    def test_default_must_be_marked_reserved(self):
        bad = copy.deepcopy(self.layers)
        for layer in bad["layers"]:
            if layer["name"] == "Default":
                layer["reserved"] = False
        self.assertFailsWith("must be marked reserved", layers=bad)

    def test_default_must_collide_with_nothing(self):
        bad = copy.deepcopy(self.layers)
        bad["collidesWith"]["Default"] = ["StaticWorld"]
        bad["collidesWith"]["StaticWorld"] = sorted(
            bad["collidesWith"]["StaticWorld"] + ["Default"]
        )
        self.assertFailsWith("must collide with nothing", layers=bad)

    def test_the_engine_layer_limit_is_pinned(self):
        """maxLayers is const in the schema, so an engine change fails loudly."""
        self.assertEqual(self.layers["maxLayers"], 64)
        bad = copy.deepcopy(self.layers)
        bad["maxLayers"] = 32
        self.assertFailsWith("64 was expected", layers=bad)

    def test_query_only_layers_are_documented_as_such(self):
        """HitQuery and AIPerception carry no authored content; say so in data."""
        descriptions = {layer["name"]: layer["description"] for layer in self.layers["layers"]}
        for name in ("HitQuery", "AIPerception"):
            with self.subTest(layer=name):
                self.assertIn("uery", descriptions[name])


if __name__ == "__main__":
    unittest.main()
