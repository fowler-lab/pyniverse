from pathlib import Path

from pyniverse.cli import main

EXAMPLE_DATA = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "dat"
    / "test-zooniverse-classifications.csv.bz2"
)


def test_cli_generates_expected_graph_files(tmp_path, capsys):
    exit_code = main(
        [
            "--input_file",
            str(EXAMPLE_DATA),
            "--output_dir",
            str(tmp_path),
            "--output_stem",
            "sample",
        ]
    )

    assert exit_code == 0
    assert sorted(path.name for path in tmp_path.glob("*.pdf")) == [
        "sample-classifications-day.pdf",
        "sample-classifications-month.pdf",
        "sample-classifications-week.pdf",
        "sample-user-distribution.pdf",
        "sample-users-day.pdf",
        "sample-users-month.pdf",
        "sample-users-week.pdf",
    ]

    captured = capsys.readouterr()
    assert "Reading classifications from CSV file..." in captured.out
    assert "Total classifications:" in captured.out


def test_cli_honours_private_project_flag(tmp_path, monkeypatch):
    captured = {}

    class FakeClassifications:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def create_users_table(self):
            return None

        def plot_classifications_by_time(self, **kwargs):
            return None

        def plot_users_by_time(self, **kwargs):
            return None

        def plot_user_classification_distribution(self, **kwargs):
            return None

        def __repr__(self):
            return "summary"

    monkeypatch.setattr("pyniverse.cli.pyniverse.Classifications", FakeClassifications)

    exit_code = main(
        [
            "--input_file",
            str(EXAMPLE_DATA),
            "--output_dir",
            str(tmp_path),
            "--private_project",
        ]
    )

    assert exit_code == 0
    assert captured["live_rows"] is False
