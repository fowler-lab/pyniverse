import os

import dateutil.parser
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas
import ujson
from tqdm import tqdm


class Classifications:
    """Classifications class for Zooniverse Data Exports CSV file.

    Args:
        zooniverse_file (str):
            Path to the Zooniverse data export file. This can be a plain CSV file
            or a compressed file such as ``foo.csv.bz2`` or ``foo.csv.gz``.
        pickle_file (str):
            Alternatively, provide the path to a pickle file saved earlier with
            ``save_pickle()``.
        from_date (str):
            Only consider classifications after this date. ISO format is
            recommended, for example ``2018-02-20``.
        to_date (str):
            Only consider classifications up to this date. ISO format is
            recommended, for example ``2018-02-26``.
    """

    def __init__(self, *args, **kwargs):
        if "zooniverse_file" not in kwargs and "pickle_file" not in kwargs:
            msg = "one of zooniverse_file or pickle_file must be specified"
            raise ValueError(msg)

        if "zooniverse_file" in kwargs:
            classifications = pandas.read_csv(
                kwargs["zooniverse_file"],
                parse_dates=["created_at"],
                converters={
                    "subject_data": self._parse_json,
                    "metadata": self._parse_json,
                    "annotations": self._parse_json,
                },
                index_col="classification_id",
            )

            classifications = classifications.drop(
                ["gold_standard", "expert"], axis=1, errors="ignore"
            )

            from_date = kwargs.get("from_date")
            to_date = kwargs.get("to_date")

            if from_date:
                classifications = classifications.loc[
                    classifications.created_at > self._parse_bound_date(from_date)
                ]

            if to_date:
                classifications = classifications.loc[
                    classifications.created_at < self._parse_bound_date(to_date)
                ]

            self.classifications = classifications.copy()

            self.classifications["live_project"] = [
                self._get_live_project(q) for q in self.classifications.metadata
            ]

            if kwargs.get("live_rows", True):
                self.classifications = self.classifications.loc[
                    self.classifications["live_project"]
                ]

            self.total_classifications = len(self.classifications)

        elif "pickle_file" in kwargs:
            self.classifications = pandas.read_pickle(kwargs["pickle_file"])
            self.total_classifications = len(self.classifications)

    def create_users_table(self):
        """Create a users table, stored internally as a Pandas dataframe.

        Notes
            * Also calculates the Gini coefficient, which measures inequality
              between the users who have done the most and least
              classifications.
            * Since it calculates ``total_users``, this method must be called
              before any print statements.
        """

        # create a table of users and how many classifications they have done
        self.users = (
            self.classifications[["user_name", "created_at"]]
            .groupby("user_name")
            .count()
        )

        # rename the total column
        self.users.columns = ["classifications"]

        # how many users have contributed?
        self.total_users = len(self.users)

        # sort the table so the top users are last
        self.users.sort_values(["classifications"], ascending=True, inplace=True)

        # label each user as whether it is anonymous or not
        self.users["anonymous"] = self.users.apply(self._anonymous_user, axis=1)

        # # create a cumulating column
        self.users["cumulative_classifications"] = self.users.classifications.cumsum()

        # use this to create a percentage of the total column
        self.users["proportion_total_classifications"] = (
            self.users["cumulative_classifications"] / self.total_classifications
        )

        # number the users
        self.users["rank"] = range(1, self.total_users + 1, 1)

        # calculate the proportion of the user base
        self.users["proportion_user_base"] = self.users["rank"] / self.total_users

        # now calculate the Gini coefficient

        area_under_curve = (
            self.users["proportion_total_classifications"].sum()
        ) / self.total_users
        self.gini_coefficient = 1 - (2 * area_under_curve)

    def __repr__(self):
        """Print a summary of the Zooniverse classifications stored."""

        line = f"{'Total classifications:':>30} {self.total_classifications:7d}\n"
        line += f"{'Total users:':>30} {self.total_users:7d}\n"
        line += f"{'Gini coefficient:':>30} {self.gini_coefficient:7.2f}\n"
        line += "\n"

        # sort the table so the top users are first
        self.users.sort_values(["classifications"], ascending=False, inplace=True)

        top_10 = (
            100 * self.users.classifications[:10].sum()
        ) / self.total_classifications
        line += f"{'Top   10 users have done:':>30} {top_10:7.1f} %\n"
        top_100 = (
            100 * self.users.classifications[:100].sum()
        ) / self.total_classifications
        line += f"{'Top  100 users have done:':>30} {top_100:7.1f} %\n"
        top_1000 = (
            100 * self.users.classifications[:1000].sum()
        ) / self.total_classifications
        line += f"{'Top 1000 users have done:':>30} {top_1000:7.1f} %\n"

        # restore ascending order after reporting headline numbers
        self.users.sort_values(["classifications"], ascending=True, inplace=True)

        return line

    def _parse_json(self, data):
        return ujson.loads(data)

    def _parse_bound_date(self, value):
        timestamp = pandas.Timestamp(dateutil.parser.parse(value))
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp

    def _get_live_project(self, row):
        try:
            return row["live_project"]
        except (KeyError, TypeError):
            return False

    def plot_classifications_by_time(
        self,
        sampling=None,
        colour="#dc2d4c",
        filename=None,
        from_date=None,
        to_date=None,
        add_cumulative=False,
    ):
        tmp = self.classifications[["created_at"]]

        # set it as the index and then re-sample
        tmp.set_index(tmp.created_at, inplace=True)

        self._plot_time_bar(
            tmp, sampling, colour, filename, add_cumulative, yaxis="Classifications"
        )

    def plot_users_by_time(
        self,
        sampling="week",
        colour="#9ab51e",
        filename=None,
        from_date=None,
        to_date=None,
        add_cumulative=False,
    ):
        if from_date:
            a = self.classifications.loc[
                self.classifications.created_at > self._parse_bound_date(from_date)
            ]

        else:
            a = self.classifications[["user_name", "created_at"]]

        if to_date:
            b = a.loc[a.created_at < self._parse_bound_date(to_date)]
        else:
            b = a

        foo = b[["user_name", "created_at"]].groupby("user_name").min()
        foo.set_index(foo.created_at, inplace=True)

        self._plot_time_bar(
            foo, sampling, colour, filename, add_cumulative, yaxis="Users"
        )

    def plot_user_classification_distribution(self, colour="#9ab51e", filename=None):
        stem, file_extension = os.path.splitext(filename)

        # use a square figure
        fig = plt.figure(figsize=(5, 5))
        axes1 = plt.gca()

        axes1.plot(
            self.users.proportion_user_base,
            self.users.proportion_total_classifications,
            color=colour,
            linewidth=2,
        )
        axes1.plot([0, 1], [0, 1], color=colour, linestyle="dashed", linewidth=2)
        axes1.text(
            0.15,
            0.65,
            f"Gini-coefficient = {self.gini_coefficient:.2f}",
            color=colour,
        )
        axes1.set_xlabel("cumulative contributors")
        axes1.set_ylabel("cumulative classifications")
        fig.savefig(stem + file_extension, transparent=True)

    def _plot_time_bar(
        self,
        data,
        sampling="week",
        colour="#e41a1c",
        filename=None,
        add_cumulative=False,
        yaxis=None,
    ):
        if sampling not in {"week", "month", "day"}:
            msg = "sampling must be either week, month or day"
            raise ValueError(msg)

        if filename is None:
            msg = "need to specify a filename with a valid extension"
            raise ValueError(msg)

        if sampling == "week":
            resampled_data = data.resample("W").count()
            bar_width = 7.1
        elif sampling == "month":
            resampled_data = data.resample("ME").count()
            bar_width = 20
        elif sampling == "day":
            resampled_data = data.resample("D").count()
            bar_width = 1.01

        number_of_months = max(
            self._month_span(data.index.min(), data.index.max()),
            1,
        )

        resampled_data.columns = ["number"]

        resampled_data["total"] = resampled_data.cumsum()

        fig = plt.figure(figsize=(9, 5))
        axes1 = plt.gca()

        axes1.yaxis.set_major_formatter(
            matplotlib.ticker.StrMethodFormatter("{x:,.0f}")
        )

        # axes1.spines['top'].set_visible(False)
        # axes1.spines['right'].set_visible(False)

        axes1.set_ylabel(yaxis + " per " + sampling, color=colour)
        axes1.tick_params("y", colors=colour)
        axes1.bar(
            resampled_data.index,
            resampled_data.number,
            width=bar_width,
            align="center",
            lw=0,
            fc=colour,
            zorder=10,
        )
        axes1.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        axes1.xaxis.set_major_locator(
            mdates.MonthLocator(interval=int(number_of_months / 12) + 1)
        )
        axes1.set_ylim(bottom=0)

        if add_cumulative:
            axes2 = axes1.twinx()
            axes2.yaxis.set_major_formatter(
                matplotlib.ticker.StrMethodFormatter("{x:,.0f}")
            )
            axes2.tick_params("y", colors="black")
            axes2.plot(
                resampled_data.index, resampled_data.total, zorder=20, color="black"
            )
            axes2.xaxis.set_major_locator(
                mdates.MonthLocator(interval=int(number_of_months / 12) + 1)
            )
            axes2.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
            axes2.set_ylim(bottom=0)

        fig.savefig(filename, transparent=True)
        plt.close(fig)

    def _task_duration(self, row):
        try:
            start = dateutil.parser.parse(row.metadata["started_at"])
            end = dateutil.parser.parse(row.metadata["finished_at"])
            duration = (end - start) / pandas.Timedelta(1, unit="s")
            return duration
        except (KeyError, TypeError, ValueError):
            return 0.0

    def _user_language(self, row):
        try:
            return row.metadata["user_language"]
        except (KeyError, TypeError):
            return ""

    def _month_span(self, start, end):
        return (end.year - start.year) * 12 + (end.month - start.month)

    def _parse_viewport_width(self, row):
        return row.metadata["viewport"]["width"]

    def _parse_viewport_height(self, row):
        return row.metadata["viewport"]["height"]

    def _anonymous_user(self, row):
        if row.name[0:13] == "not-logged-in":
            return True
        else:
            return False

    def create_misc_fields(self):
        tqdm.pandas(desc="extracting language  ")
        self.classifications["user_language"] = self.classifications.progress_apply(
            self._user_language, axis=1
        )

        tqdm.pandas(desc="extracting viewport  ")
        self.classifications["viewport_width"] = self.classifications.progress_apply(
            self._parse_viewport_width, axis=1
        )
        self.classifications["viewport_height"] = self.classifications.progress_apply(
            self._parse_viewport_height, axis=1
        )

    def calculate_task_durations(self):
        tqdm.pandas(desc="extracting durations ")
        self.classifications["task_duration"] = self.classifications.progress_apply(
            self._task_duration, axis=1
        )

    def save_pickle(self, filename):
        self.classifications.to_pickle(filename)

    def save_csv(self, filename, compression=False):
        if compression:
            self.classifications.to_csv(filename, compression="bz2")
        else:
            self.classifications.to_csv(filename)
