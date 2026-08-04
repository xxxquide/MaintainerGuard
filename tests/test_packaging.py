import tarfile
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path

from veracity import __version__


ROOT = Path(__file__).resolve().parents[1]


def pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def hatchling_or_skip(test) -> None:
    try:
        import hatchling  # noqa: F401
    except ImportError:  # pragma: no cover - hatchling is a build-time dependency
        test.skipTest("hatchling is not installed in this environment")


class PyprojectContractTests(unittest.TestCase):
    def test_pyproject_exposes_veracity_and_mg_scripts(self):
        scripts = pyproject()["project"]["scripts"]
        self.assertEqual("veracity.cli:main", scripts["veracity"])
        self.assertEqual("veracity.cli:main", scripts["vera"])

    def test_version_has_a_single_source(self):
        data = pyproject()
        self.assertIn("version", data["project"]["dynamic"])
        self.assertNotIn(
            "version",
            data["project"],
            "A static version in [project] can drift from veracity.__version__.",
        )
        self.assertEqual(
            "veracity/__init__.py",
            data["tool"]["hatch"]["version"]["path"],
        )
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")

    def test_readme_and_authors_are_declared(self):
        project = pyproject()["project"]
        self.assertEqual("README.md", project["readme"])
        self.assertTrue(project["authors"])

    def test_bundled_data_paths_are_declared_for_the_wheel(self):
        force_include = pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
        for relative in ("action.yml", ".veracity.toml", "examples/sample-data", "schemas"):
            self.assertIn(relative, force_include)


class BuiltDistributionTests(unittest.TestCase):
    """The wheel and sdist must match what the CLI and PyPI actually need."""

    def build(self, directory: str) -> tuple[Path, Path]:
        from hatchling.builders.sdist import SdistBuilder
        from hatchling.builders.wheel import WheelBuilder

        wheel = next(
            iter(WheelBuilder(str(ROOT)).build(directory=directory, versions=["standard"]))
        )
        sdist = next(
            iter(SdistBuilder(str(ROOT)).build(directory=directory, versions=["standard"]))
        )
        return Path(wheel), Path(sdist)

    def test_wheel_ships_the_data_the_cli_reads_and_correct_metadata(self):
        hatchling_or_skip(self)
        with tempfile.TemporaryDirectory() as directory:
            wheel, _sdist = self.build(directory)
            with zipfile.ZipFile(wheel) as archive:
                names = set(archive.namelist())
                metadata = archive.read(
                    next(name for name in names if name.endswith(".dist-info/METADATA"))
                ).decode("utf-8")
                entry_points = archive.read(
                    next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
                ).decode("utf-8")

        for required in (
            "veracity/cli.py",
            "veracity/scanners.py",
            "action.yml",
            ".veracity.toml",
            "examples/sample-data/prs/high-risk-auth.json",
            "examples/sample-data/scanners/dependency-advisory.json",
            "schemas/report.schema.json",
        ):
            self.assertIn(required, names, f"{required} missing from the wheel")
        self.assertIn("veracity = veracity.cli:main", entry_points)
        self.assertIn("vera = veracity.cli:main", entry_points)

        headers, _, long_description = metadata.partition("\n\n")
        project = pyproject()["project"]
        self.assertIn(f"Version: {__version__}", headers)
        self.assertIn("Author: ", headers)
        self.assertIn("Description-Content-Type:", headers)
        self.assertIn("License-File: LICENSE", headers)
        for classifier in project["classifiers"]:
            self.assertIn(classifier, headers)
        for keyword in project["keywords"]:
            self.assertIn(keyword, headers)
        self.assertGreater(
            len(long_description),
            1000,
            "The readme must reach METADATA, otherwise PyPI shows no description.",
        )

    def test_sdist_carries_tests_but_not_the_demo_media(self):
        hatchling_or_skip(self)
        with tempfile.TemporaryDirectory() as directory:
            _wheel, sdist = self.build(directory)
            with tarfile.open(sdist) as archive:
                names = archive.getnames()
            size = sdist.stat().st_size

        self.assertTrue(any(name.endswith("tests/test_scanners.py") for name in names))
        self.assertTrue(any(name.endswith("pyproject.toml") for name in names))
        self.assertFalse(
            any("/assets/" in name or name.endswith(".gif") for name in names),
            "The 13.9 MB demo GIF is not needed to install or run the package.",
        )
        self.assertFalse(any(name.endswith(".coverage") for name in names))
        self.assertLess(size, 5_000_000, f"sdist grew to {size} bytes")


if __name__ == "__main__":
    unittest.main()
