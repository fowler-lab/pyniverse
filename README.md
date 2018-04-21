# pyniverse: a Python package to analyse generic results of the Zooniverse volunteers

This Python package is intended to allow Zooniverse Project Owners to quickly run some simple analysis on the classification CSVs that the Zooniverse backend allows you to export via the Data Exports page. 

## How to install

Download/clone the GitHub repo, then to install in your $HOME directory

    $ cd pyniverse/
    $ ls
    LICENSE            README.md          bin                examples           pyniverse          setup.py
    $ python setup.py install --user
  
## How to use

Most of the logic in Pyniverse is hidden away in a simple class, called `Classifications`, which contains a variety of methods, including several that plot graphs. Then there is a simple script in the `bin/` folder called `analyse-zooniverse-classifications.py` that creates an instance of the class by passing it the path of the CSV file downloaded from the Zooniverse file and calling several of the methods. Let's see how it works.

    $ cd examples/
    $ analyse-zooniverse-classifications.py --input_file dat/test-zooniverse-classifications.csv.bz2
    Reading classifications from CSV file...
        Total classifications:  218629
                  Total users:    4529
             Gini coefficient:   -0.78

     Top   10 users have done:    18.6 %
     Top  100 users have done:    44.4 %
     Top 1000 users have done:    82.8 %
     
This step should take no more than 30 seconds and in addition to the above information, you should find some graphs in `pdf/`. If you didn't specify the name of the output file using the `--output_stem` option then the program will use the default which is `test`. 

    $ ls pdf/
    test-classifications-day.pdf      test-classifications-week.pdf     test-user-distribution-log.pdf    test-users-month.pdf
    test-classifications-month.pdf    test-user-distribution-linear.pdf test-users-day.pdf                test-users-week.pdf
  
![a graph](examples/example-graphs/test-users-day.pdf)

  
