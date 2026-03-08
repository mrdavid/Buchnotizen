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

# open and parse XML database
e = xml.etree.ElementTree.parse('log.xml').getroot()
books = e.findall('book')
total_books = len(books)
books_per_month = (total_books/( (now.year - 2013.0)*12.0 + 4.0 + now.month ))


def generate_readme(books, total_books, books_per_month, now):
    lines = []
    lines.append("# Literature log")
    lines.append("")
    lines.append("I started this log on October 30th, 2012. I list all books I read.  ")
    lines.append("")
    lines.append("### Statistics")
    lines.append("Total number of books read: " + str(total_books) + "  ")
    lines.append("Books per month: " + str(round(books_per_month,2)) + " (2012/9 to "+str(now.year)+"/"+str(now.month)+")")
    lines.append("")
    lines.append("![Books recorded by year](book_recorded.png)")
    lines.append("![Books read per month](book_read.png)")
    lines.append("![Days between books (distribution)](book_gaps.png)")
    lines.append('')
    lines.append("### List of books")

    for atype in books:
        lines.append("*"+atype.find('title').text+"*, "+atype.find('author').text+"  ")
        if atype.find('title') is not None:
            lines.append("Finished: " + atype.find('finished').text)
        lines.append("")

    return "\n".join(lines) + "\n"


output = generate_readme(books, total_books, books_per_month, now)
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(output)

# ---------------------------------------
# Update graphs
# ---------------------------------------

books_list = [[b.find('title').text, b.find('author').text, b.find('finished').text] for b in books]
df = pd.DataFrame(books_list, columns=['title', 'author', 'date_read'])
df.date_read = pd.to_datetime(df.date_read, format="%Y.%m.%d")

# We want to summarize by date - make the date the index
df.index = df.date_read
# summarize by year
df2 = df.groupby(pd.Grouper(freq='YE')).count()['title']

df2.year = pd.Series(df2.index).apply(lambda x: x.year)
df2.index = df2.year

# plot total books recorded each year
# Note: 2012 doesn't have data for the whole year, so it's books recorded, not book read
my_dpi=100
plt.figure(figsize=(780/my_dpi, 360/my_dpi), dpi=my_dpi)
fig = df2.plot(kind='bar')
fig.axhline(y = 12, color = 'r', linestyle = 'dashed')
fig.set_xlabel('Year')
fig.set_ylabel('Number of books recorded')
fig.set_title('Books recorded')
fig.get_figure().savefig('book_recorded.png')

# summarize by month
df3 = df.groupby(pd.Grouper(freq='ME')).count()['title']

# extend to current month to also include recent periods without activity
start = max(df3.index)
end = pd.Timestamp.today() + pd.tseries.offsets.MonthEnd()

# update index including potentially empty months
df3a = df3.reindex(df3.index.union(pd.date_range(start=start, end=end,freq="ME"))).fillna(0)

# plot
plt.figure(figsize=(780/my_dpi, 360/my_dpi), dpi=my_dpi)
df3df = df3a.rolling(window=5,center=True).mean()
fig = df3df.plot(yticks=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5])
fig.set_xlabel('Date')
fig.set_ylabel('Number of books read')
fig.set_title('Books read per month (5 month rolling average)')
fig.get_figure().savefig('book_read.png')

# gap between consecutive books (days between finish dates)
dates_sorted = df['date_read'].sort_values()
gaps = dates_sorted.diff().dropna().dt.days

plt.figure(figsize=(780/my_dpi, 360/my_dpi), dpi=my_dpi)
fig, ax = plt.subplots(figsize=(780/my_dpi, 360/my_dpi), dpi=my_dpi)
ax.hist(gaps, bins=30, weights=[100.0 / len(gaps)] * len(gaps), edgecolor='white', linewidth=0.5)
ax.set_xlabel('Days between finishing books')
ax.set_ylabel('Percentage (%)')
ax.set_title('Distribution of gaps between books')
fig.savefig('book_gaps.png')
