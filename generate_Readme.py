import xml.etree.ElementTree
import datetime
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
#%matplotlib inline


# ----------------------------------------------------
# Output Readme.md markdown file that list out my books_list
# ----------------------------------------------------

now = datetime.datetime.now()

print("# Literature log")
print("")
print("I started this log on October 30th, 2012. I list all books I read.  ")
print("""The most significant events impacting the number of books I read are
* Job changes in 2016/01 and 2019/03.
* The birth of my daughers in 2018/01 and 2019/08""")
print("")

total_books = 0
# open and parse XML database
e = xml.etree.ElementTree.parse('log.xml').getroot()
books = e.findall('book')
total_books = len(books)

# Print general statistics
print("### Statistics")
books_per_month = (total_books/( (now.year - 2013.0)*12.0 + 4.0 + now.month ))
print("Total number of books read: " + str(total_books) + "  ")
print("Books per month: " + str(round(books_per_month,2)) + " (2012/9 to "+str(now.year)+"/"+str(now.month)+")")
print("")
print("![Books recorded by year](book_recorded.png)")
print("![Books read per month](book_read.png)")
print('')
print("### List of books")

# List out all books with author and date read
books_list = []
for atype in books:
    total_books += 1
    books_list.append([atype.find('title').text, atype.find('author').text, atype.find('finnished').text])

    print(("*"+atype.find('title').text+"*, "+atype.find('author').text+"  ")) #.encode('utf-8'))
    if atype.find('title') != None:
        print("Finished: " + atype.find('finnished').text)
    print("")

# ---------------------------------------
# Update graphs
# ---------------------------------------

df = pd.DataFrame(books_list, columns=['title', 'author', 'date_read'])
df.date_read = pd.to_datetime(df.date_read, format="%Y.%m.%d")

# We want to summarize by date - make the date the index
df.index = df.date_read
# summarize by year
df2 = df.groupby(pd.Grouper(freq='A')).count()['title']

df2.year = pd.Series(df2.index).apply(lambda x: x.year)
df2.index = df2.year

# plot total books recorded each year
# Note: 2012 doesn't have data for the whole year, so it's books recorded, not book read
my_dpi=100
plt.figure(figsize=(580/my_dpi, 360/my_dpi), dpi=my_dpi)
fig = df2.plot(kind='bar')
fig.set_xlabel('Year')
fig.set_ylabel('Number of books recorded')
fig.set_title('Books recorded')
fig.get_figure().savefig('book_recorded.png')

# summarize by month
df3 = df.groupby(pd.Grouper(freq='M')).count()['title']

# extend to current month to also include recent periods without activity
start = max(df3.index)
end = pd.Timestamp.today() + pd.tseries.offsets.MonthEnd()

# update index including potentially empty months
df3a = df3.reindex(df3.index.union(pd.date_range(start=start, end=end,freq="M"))).fillna(0)

# plot
plt.figure(figsize=(580/my_dpi, 360/my_dpi), dpi=my_dpi)
df3df = df3a.rolling(window=5,center=True).mean()
fig = df3df.plot(yticks=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5])
fig.set_xlabel('Date')
fig.set_ylabel('Number of books read')
fig.set_title('Books read per month (5 month rolling average)')
fig.get_figure().savefig('book_read.png')
