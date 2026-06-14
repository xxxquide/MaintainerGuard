import tempfile
import unittest
import tomllib
import zipfile
from pathlib import Path

import maintainerguard_build
from maintainerguard import __version__


DIST_INFO = f"maintainerguard-{maintainerguard_build.VERSION}.dist-info"


class PackagingTests(unittest.TestCase):
    def test_standard_library_backend_builds_wheel_and_sdist(self):
        with tempfile.TemporaryDirectory() as directory:
            wheel = maintainerguard_build.build_wheel(directory)
            sdist = maintainerguard_build.build_sdist(directory)
            self.assertTrue((Path(directory) / wheel).is_file())
            self.assertTrue((Path(directory) / sdist).is_file())

            with zipfile.ZipFile(Path(directory) / wheel) as archive:
                names = set(archive.namelist())
                entry_points = archive.read(f"{DIST_INFO}/entry_points.txt").decode("utf-8")
            self.assertIn("examples/sample-data/prs/high-risk-auth.json", names)
            self.assertIn("examples/sample-data/scanners/dependency-advisory.json", names)
            self.assertIn("action.yml", names)
            self.assertIn("maintainerguard = maintainerguard.cli:main", entry_points)
            self.assertIn("mg = maintainerguard.cli:main", entry_points)

    def test_standard_library_backend_builds_editable_wheel(self):
        with tempfile.TemporaryDirectory() as directory:
            wheel = maintainerguard_build.build_editable(directory)
            with zipfile.ZipFile(Path(directory) / wheel) as archive:
                names = set(archive.namelist())
                pth = archive.read("maintainerguard-editable.pth").decode("utf-8")
                entry_points = archive.read(f"{DIST_INFO}/entry_points.txt").decode("utf-8")
            self.assertIn(str(Path(__file__).resolve().parents[1]), pth)
            self.assertIn(f"{DIST_INFO}/METADATA", names)
            self.assertIn("mg = maintainerguard.cli:main", entry_points)

    def test_pyproject_exposes_maintainerguard_and_mg_scripts(self):
        pyproject = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
        scripts = pyproject["project"]["scripts"]
        self.assertEqual("maintainerguard.cli:main", scripts["maintainerguard"])
        self.assertEqual("maintainerguard.cli:main", scripts["mg"])

    def test_package_versions_stay_synchronized(self):
        pyproject = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(pyproject["project"]["version"], __version__)
        self.assertEqual(pyproject["project"]["version"], maintainerguard_build.VERSION)


if __name__ == "__main__":
    unittest.main()
