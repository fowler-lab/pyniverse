from pathlib import Path

import pytest

from pyniverse import Classifications

EXAMPLE_DATA = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "dat"
    / "test-zooniverse-classifications.csv.bz2"
)


def test_requires_input_source():
    with pytest.raises(ValueError, match="must be specified"):
        Classifications()


def test_example_dataset_loads_and_filters_live_rows():
    live_only = Classifications(zooniverse_file=str(EXAMPLE_DATA))
    include_private = Classifications(
        zooniverse_file=str(EXAMPLE_DATA), live_rows=False
    )

    assert live_only.total_classifications == 218629
    assert include_private.total_classifications >= live_only.total_classifications
    assert live_only.classifications["live_project"].all()


def test_date_filter_reduces_dataset_size():
    full_dataset = Classifications(zooniverse_file=str(EXAMPLE_DATA), live_rows=False)
    filtered_dataset = Classifications(
        zooniverse_file=str(EXAMPLE_DATA),
        from_date="2016-09-01",
        to_date="2016-10-01",
        live_rows=False,
    )

    assert (
        0 < filtered_dataset.total_classifications < full_dataset.total_classifications
    )


def test_invalid_sampling_raises_value_error(tmp_path):
    classifications = Classifications(zooniverse_file=str(EXAMPLE_DATA))

    with pytest.raises(ValueError, match="sampling must be either week, month or day"):
        classifications.plot_classifications_by_time(
            sampling="year",
            filename=str(tmp_path / "invalid.pdf"),
        )
