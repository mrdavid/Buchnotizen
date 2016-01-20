import xml.etree.ElementTree
import datetime

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
print("Books per month: " + str(round(books_per_month,2)))
print("")
print("### List of books")

for atype in books:
    total_books += 1
    print("*"+atype.find('title').text+"*, "+atype.find('author').text+"  ")
    if atype.find('title') != None:
        print("Finished: " + atype.find('finnished').text)
    print("")
