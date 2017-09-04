import xml.etree.ElementTree
import datetime
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
#%matplotlib inline

now = datetime.datetime.now()

print("# Literature log")
print("")
print("I started this log on October 30th, 2012. I list all books I read.")
print("")

total_books = 0
e = xml.etree.ElementTree.parse('log.xml').getroot()
books = e.findall('book')
total_books = len(books)

print("### Statistics")
books_per_month = (total_books/( (now.year - 2013.0)*12.0 + 4.0 + now.month ))
print("Total number of books read: " + str(total_books) + "  ")
print("Books per month: " + str(round(books_per_month,2)) + " (2012/9 to "+str(now.year)+"/"+str(now.month)+")")
print("")
print("![Books recorded by year](book_recorded.png)")
print('')
print("### List of books")

books_list = []
for atype in books:
    total_books += 1
    books_list.append([atype.find('title').text, atype.find('author').text, atype.find('finnished').text])

    print("*"+atype.find('title').text+"*, "+atype.find('author').text+"  ")
    if atype.find('title') != None:
        print("Finished: " + atype.find('finnished').text)
    print("")

# Update graphs
df = pd.DataFrame(books_list, columns=['title', 'author', 'date_read'])
df.date_read = pd.to_datetime(df.date_read, format="%Y.%m.%d")

df.index = df.date_read
df2 = df.groupby(pd.Grouper(freq='A')).count()['title']

df2.year = pd.Series(df2.index).apply(lambda x: x.year)
df2.index = df2.year

my_dpi=100
plt.figure(figsize=(540/my_dpi, 460/my_dpi), dpi=my_dpi)
fig = df2.plot(kind='bar')
fig.set_xlabel('Year')
fig.set_ylabel('Number of books recorded')
fig.set_title('Books recorded')
fig.get_figure().savefig('book_recorded.png')
