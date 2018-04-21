#! /usr/bin/env python

import time
import argparse

import pandas

import pyniverse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file",required=True,help="the csv file downloaded from the Zooniverse containing all the classifcations done to date")
    parser.add_argument("--output_stem",default="test",help="the first part of each of the output files")
    parser.add_argument("--timings",action='store_true',default=False,help="print the time taken for each step")
    options = parser.parse_args()


    print("Reading classifications from CSV file...")
    start=time.time()
    current_classifications=pyniverse.Classifications(zooniverse_file=options.input_file)
    if options.timings:
        print("%.1f seconds" % (time.time()-start))

    # Creating users table...
    current_classifications.create_users_table()

    # Plotting graphs...
    for sampling_time in ['month','week','day']:

        current_classifications.plot_classifications_by_time(sampling=sampling_time,filename='pdf/'+options.output_stem+'-classifications-'+sampling_time+'.pdf',pre_launch=True,add_cumulative=True)
        current_classifications.plot_users_by_time(sampling=sampling_time,filename='pdf/'+options.output_stem+'-users-'+sampling_time+'.pdf',pre_launch=True,add_cumulative=True)

    current_classifications.plot_user_classification_distribution(filename="pdf/"+options.output_stem+'-user-distribution.pdf')

    print(current_classifications)

    # print("Saving PKL file...")
    # current_classifications.save_pickle("dat/"+options.output_stem+".pkl")
