#! /usr/bin/env python

import dateutil.parser
import datetime
import os

import ujson
import pandas, numpy
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from tqdm import tqdm

class Classifications(object):

    """ Classifications class for Zooniverse Data Exports CSV file.

    Args:
        zooniverse_file (str): the path to the zooniverse data exports file. Can be a simple foo.csv file or a compressed file
        as Python can parse most common compression formats (e.g. foo.csv.bz2, foo.csv.gz)
        pickle_file (str): alternatively, one can provide the path to a pickle (foo.pkl) file that was saved earlier using the save_pickle() method.
        from_date (str): only consider classifications after this date. Although a string, is parsed so ISO format recommended e.g. 2018-02-20
        to_date (str): only consider classifications up to this date. Although a string, is parsed so ISO format recommended e.g. 2018-02-26
    """

    # def __init__(self,zooniverse_file=None,pickle_file=None,from_date=None,to_date=None,live_rows=True):
    def __init__(self,*args,**kwargs):

        # check that one of zooniverse_file or pickle_file is specified
        assert 'zooniverse_file' or 'pickle_file' in kwargs.keys(), "one of zooniverse_file or pickle_file must be specified"

        if 'zooniverse_file' in kwargs.keys():

            # read in the raw classifications, parsing the JSON as you go
            classifications = pandas.read_csv(kwargs['zooniverse_file'],parse_dates=['created_at'],infer_datetime_format=True,converters={'subject_data':self._parse_json,'metadata':self._parse_json,'annotations':self._parse_json},index_col='classification_id')

            # drop a few of the (unused) columns
            classifications.drop(['gold_standard','expert'], axis=1, inplace=True)

            # create a dataseries of just the date/times
            if 'from_date' in kwargs.keys() and kwargs['from_date'] is not False:
                a=classifications.loc[classifications.created_at>dateutil.parser.parse(kwargs['from_date']).date()]
            else:
                a=classifications

            if 'to_date' in kwargs.keys() and kwargs['to_date'] is not False:
                b=a.loc[a.created_at<dateutil.parser.parse(kwargs['to_date']).date()]
            else:
                b=a

            self.classifications=b

            # then create a Boolean column defining if the classification was made during live or not
            self.classifications['live_project']  = [self._get_live_project(q) for q in self.classifications.metadata]

            # if asked, create a new dataset containing only live classifications
            if 'live_rows' not in kwargs.keys() or kwargs['live_rows']:
                self.classifications=self.classifications.loc[self.classifications["live_project"]==True]

            # how many classifications have been done?
            self.total_classifications=len(self.classifications)

        elif 'pickle_file' in kwargs.keys():

            # find out the file extension so we can load in the dataset using the right method
            stem, file_extension = os.path.splitext(kwargs['pickle_file'])

            # doing it this way means you can provide either pickle file and it will still work
            # self.classifications=pandas.read_pickle(stem+"-classifications"+file_extension)
            self.classifications=pandas.read_pickle(kwargs['pickle_file'])

            # how many classifications have been done?
            self.total_classifications=len(self.classifications)


    def create_users_table(self):
        """ Create a users table, stored internally as a Pandas dataframe.

        Notes
         * also calculates the Gini coefficient which is a measure of the inequality between the users who have done the most and least classifications.
         * since it calculates the total_users, this method must be called before any print statements
        """

        # create a table of users and how many classifications they have done
        self.users=self.classifications[['user_name','created_at']].groupby('user_name').count()

        # rename the total column
        self.users.columns=['classifications']

        # how many users have contributed?
        self.total_users=len(self.users)

        # sort the table so the top users are last
        self.users.sort_values(['classifications'],ascending=True,inplace=True)

        # label each user as whether it is anonymous or not
        self.users['anonymous']=self.users.apply(self._anonymous_user,axis=1)

        # # create a cumulating column
        self.users['cumulative_classifications']=self.users.classifications.cumsum()

        # use this to create a percentage of the total column
        self.users['proportion_total_classifications']=self.users['cumulative_classifications']/self.total_classifications

        # number the users
        self.users['rank']=range(1,self.total_users+1,1)

        # calculate the proportion of the user base
        self.users['proportion_user_base']=self.users['rank']/self.total_users

        # now calculate the Gini coefficient

        area_under_curve=(self.users['proportion_total_classifications'].sum())/self.total_users
        self.gini_coefficient=1-(2*area_under_curve)


    def __repr__(self):
        ''' Print a summary of the Zooniverse classifications stored.
        '''

        line="%30s %7i\n" % ("Total classifications:",self.total_classifications)
        line+="%30s %7i\n" % ("Total users:",self.total_users)
        line+="%30s %7.2f\n" % ("Gini coefficient:",self.gini_coefficient)
        line+="\n"

        # sort the table so the top users are first
        self.users.sort_values(['classifications'],ascending=False,inplace=True)

        top_10=(100*self.users.classifications[:10].sum())/self.total_classifications
        line+="%30s %7.1f %%\n" % ("Top   10 users have done:",top_10)
        top_100=(100*self.users.classifications[:100].sum())/self.total_classifications
        line+="%30s %7.1f %%\n" % ("Top  100 users have done:",top_100)
        top_1000=(100*self.users.classifications[:1000].sum())/self.total_classifications
        line+="%30s %7.1f %%\n" % ("Top 1000 users have done:",top_1000)

        # sort the table so the top users are last
        self.users.sort_values(['classifications'],ascending=False,inplace=True)


        return(line)


    def _parse_json(self,data):
        return ujson.loads(data)

    def _get_live_project(self,row):
        try:
            return row['live_project']
        except:
            # apparently some subject metadata doesn't have this? dunno?
            return False

    def plot_classifications_by_time(self,sampling=None,colour='#dc2d4c',filename=None,from_date=None,to_date=None,add_cumulative=False):

        tmp=self.classifications[['created_at']]

        # set it as the index and then re-sample
        tmp.set_index(tmp.created_at,inplace=True)

        self._plot_time_bar(tmp,sampling,colour,filename,add_cumulative,yaxis="Classifications")


    def plot_users_by_time(self,sampling='week',colour='#9ab51e',filename=None,from_date=None,to_date=None,add_cumulative=False):

        # create a dataseries of just the date/times
        if from_date:
            a=self.classifications.loc[self.classifications.created_at>dateutil.parser.parse(from_date).date()]

        else:
            a=self.classifications[['user_name','created_at']]

        if to_date:
            b=a.loc[a.created_at<dateutil.parser.parse(to_date).date()]
        else:
            b=a

        foo=b[['user_name','created_at']].groupby('user_name').min()
        foo.set_index(foo.created_at,inplace=True)
        tmp=foo.created_at

        self._plot_time_bar(foo,sampling,colour,filename,add_cumulative,yaxis="Users")

    def plot_user_classification_distribution(self,colour="#9ab51e",filename=None):

        stem, file_extension = os.path.splitext(filename)

        # use a square figure
        fig = plt.figure(figsize=(5, 5))
        axes1 = plt.gca()

        axes1.plot(self.users.proportion_user_base,self.users.proportion_total_classifications,color=colour,linewidth=2)
        axes1.plot([0,1],[0,1],color=colour,linestyle='dashed',linewidth=2)
        axes1.text(0.15,0.65,"Gini-coefficient = %.2f" % self.gini_coefficient,color=colour)
        axes1.set_xlabel('cumulative contributors')
        axes1.set_ylabel('cumulative classifications')
        fig.savefig(stem+file_extension,transparent=True)


    def _plot_time_bar(self,data,sampling='week',colour='#e41a1c',filename=None,add_cumulative=False,yaxis=None):

        assert sampling in ['week','month','day'], "sampling must be either week, month or day"

        assert filename is not None, 'need to specify a filename with a valid extension'

        if sampling=='week':
            resampled_data=data.resample('W').count()
            bar_width=7.1
        elif sampling=="month":
            resampled_data=data.resample('M').count()
            bar_width=20
        elif sampling=="day":
            resampled_data=data.resample('D').count()
            bar_width=1.01

        number_of_months = int((data.index.max()-data.index.min())/numpy.timedelta64(1, 'M'))

        resampled_data.columns=['number']

        resampled_data['total']=resampled_data.cumsum()

        fig = plt.figure(figsize=(9, 5))
        axes1 = plt.gca()

        axes1.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))

        # axes1.spines['top'].set_visible(False)
        # axes1.spines['right'].set_visible(False)

        axes1.set_ylabel(yaxis+" per "+sampling,color=colour)
        axes1.tick_params('y', colors=colour)
        axes1.bar(resampled_data.index,resampled_data.number,width=bar_width,align='center',lw=0,fc=colour,zorder=10)
        axes1.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
        axes1.xaxis.set_major_locator(mdates.MonthLocator(interval=int(number_of_months/12)+1))
        axes1.set_ylim(bottom=0)

        if add_cumulative:
            axes2 = axes1.twinx()
            axes2.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))
            axes2.tick_params('y', colors='black')
            axes2.plot(resampled_data.index,resampled_data.total,zorder=20,color='black')
            axes2.xaxis.set_major_locator(mdates.MonthLocator(interval=int(number_of_months/12)+1))
            axes2.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
            axes2.set_ylim(bottom=0)

        fig.savefig(filename,transparent=True)

    def _task_duration(self,row):
        try:
            start=(dateutil.parser.parse(row.metadata['started_at']))
            end=(dateutil.parser.parse(row.metadata['finished_at']))
            duration = (end-start)/pandas.Timedelta(1, unit='s')
            return(duration)
        except:
            return(pandas.Timedelta(0, unit='s'))

    def _user_language(self,row):
        try:
            return row.metadata['user_language']
        except:
            return ""

    def _parse_viewport_width(self,row):
        return row.metadata['viewport']['width']

    def _parse_viewport_height(self,row):
        return row.metadata['viewport']['height']

    def _anonymous_user(self,row):
        if row.name[0:13]=="not-logged-in":
            return True
        else:
            return False

    def create_misc_fields(self):

        tqdm.pandas(desc='extracting language  ')
        self.classifications['user_language']=self.classifications.progress_apply(self._user_language,axis=1)

        tqdm.pandas(desc='extracting viewport  ')
        self.classifications['viewport_width']=self.classifications.progress_apply(self._parse_viewport_width,axis=1)
        self.classifications['viewport_height']=self.classifications.progress_apply(self._parse_viewport_height,axis=1)

    def calculate_task_durations(self):

        tqdm.pandas(desc='extracting durations ')
        self.classifications['task_duration']=self.classifications.progress_apply(self._task_duration,axis=1)

    def save_pickle(self,filename):

        self.classifications.to_pickle(filename)

    def save_csv(self,filename,compression=False):

        if compression:
            self.classifications.to_csv(filename,compression='bz2')
        else:
            self.classifications.to_csv(filename)
