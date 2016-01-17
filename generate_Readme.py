import xml.etree.ElementTree
import datetime

now = datetime.datetime.now()

print("# Literature log")
print("")
print("I started this log on October 30th, 2012. I list all books I read.")
print("")

total_books = 0

e = xml.etree.ElementTree.parse('log.xml').getroot()

for atype in e.findall('book'):
    total_books += 1
    print("*"+atype.find('title').text+"*, "+atype.find('author').text+"  ")
    if "finnished" != None:
        print("Finished: " + atype.find('finnished').text)
    print("")

print("### Statistics")
books_per_month = (total_books/( (now.year - 2013.0)*12.0 + 4.0 + now.month ))
print("Total number of books read: " + str(total_books) + "  ")
print("Books per month: " + str(round(books_per_month,2)))
